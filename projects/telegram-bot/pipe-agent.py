#!/usr/bin/env python3
"""Telegram Agent Pipe — auto-discovers MCP tools and handles tool execution loop."""
import logging
import os, json, re
import httpx
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Match text-based tool calls: <TOOL_NAME>content</TOOL_NAME> or <TOOL_NAME args />
_TEXT_TOOL_RE = re.compile(r"<(\w+)>(.*?)</\1>", re.DOTALL)
_SELF_CLOSING_RE = re.compile(r"<(\w+)([^>]*?)/>")


class Pipe:
    class Valves(BaseModel):
        BASE_MODEL: str = Field(default="telegram-chat", description="Open WebUI model ID")
        OWUI_API_BASE: str = Field(default="http://127.0.0.1:8080/api", description="Open WebUI API Base URL")
        OWUI_API_KEY: str = Field(default="", description="Open WebUI API Key")
        MCPO_MEMORY: str = Field(default="", description="Memory mcpo URL")
        MCPO_GITHUB: str = Field(default="", description="GitHub mcpo URL")
        MCPO_FETCH: str = Field(default="", description="Fetch mcpo URL")
        MCPO_SEARXNG: str = Field(default="", description="SearXNG mcpo URL")

    def __init__(self):
        self.type = "pipe"
        self.id = "telegram-agent"
        self.name = "Telegram Agent"
        self.valves = self.Valves()

    async def _discover_tools(self, client: httpx.AsyncClient):
        path_map = {}
        endpoints = [
            ("memory", self.valves.MCPO_MEMORY),
            ("github", self.valves.MCPO_GITHUB),
            ("fetch", self.valves.MCPO_FETCH),
            ("searxng", self.valves.MCPO_SEARXNG),
        ]
        for name, url in endpoints:
            if not url:
                continue
            try:
                base_url = url.rstrip('/')
                r = await client.get(f"{base_url}/openapi.json", timeout=5.0)
                if r.status_code != 200:
                    continue
                spec = r.json()
                for path, methods in spec.get("paths", {}).items():
                    for method, details in methods.items():
                        opid = details.get("operationId", "")
                        clean = opid.replace("tool_", "").replace("_post", "")
                        opid = f"{name}_{clean}" if clean else f"{name}_{path.strip('/').replace('/', '_')}"
                        path_map[opid] = (base_url, path, method.upper())
            except Exception:
                logger.warning("MCP endpoint %s unreachable", name)
        return path_map

    async def _execute_tool(self, client: httpx.AsyncClient, opid: str, args: dict, path_map: dict) -> str:
        if opid not in path_map:
            return f"Error: tool '{opid}' not available"
        base_url, path, method = path_map[opid]
        try:
            r = await client.request(method, f"{base_url}{path}", json=args, timeout=15.0)
            return r.text[:1000]
        except Exception as e:
            logger.error("Tool %s failed: %s", opid, e)
            return f"Error: {e}"

    def _build_tool_tags(self, path_map: dict) -> dict:
        """Build tag_name → opid mapping from discovered tools."""
        tag_map = {}
        for opid in path_map:
            parts = opid.split("_")
            if parts[-1] == "post":
                parts = parts[:-1]
            # Build tag: first 2 parts joined (e.g. "memory_search", "searxng_searxng_search")
            if len(parts) >= 2:
                tag = "_".join(parts[:2])
            else:
                tag = opid
            tag_map[tag] = opid
        return tag_map

    def _build_system_prompt(self, tag_map: dict) -> str:
        """Generate system prompt listing available tools."""
        if not tag_map:
            return ""
        lines = [
            "You have access to these tools. To use a tool, output ONLY the XML tag.",
            "Available tools:",
        ]
        for tag, opid in sorted(tag_map.items()):
            lines.append(f"  <{tag.upper()}></{tag.upper()}> — {opid}")
        lines.append("")
        lines.append("For search tools, nest the search terms inside the tag: <TAG>search terms here</TAG>")
        lines.append("For other tools, use attributes: <TAG key=\"value\" />")
        lines.append("After receiving tool results, provide your final answer without XML tags.")
        return "\n".join(lines)

    def _extract_text_tool_calls(self, content: str, tag_map: dict) -> list[dict]:
        """Extract tool calls from text using dynamic tag_map."""
        calls = []
        # First try self-closing: <tool key="val" />
        for m in _SELF_CLOSING_RE.finditer(content):
            tag = m.group(1).lower()
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(2)))
            if tag in tag_map:
                calls.append({"tool": tag_map[tag], "args": attrs})
        # Then try nested: <TOOL>content</TOOL>
        for m in _TEXT_TOOL_RE.finditer(content):
            tag = m.group(1).lower()
            inner = m.group(2).strip()
            if tag in ("query",):
                continue
            if tag not in tag_map:
                continue
            args = {}
            # Extract sub-elements
            for sm in _TEXT_TOOL_RE.finditer(inner):
                sub_tag = sm.group(1).lower()
                sub_val = sm.group(2).strip()
                args[sub_tag] = sub_val
            # Also try self-closing in inner
            for sm in _SELF_CLOSING_RE.finditer(inner):
                sub_attrs = dict(re.findall(r'(\w+)="([^"]*)"', sm.group(2)))
                args.update(sub_attrs)
            # If no sub-elements found, treat inner text as the first arg
            if not args and inner:
                args["query"] = inner
            calls.append({"tool": tag_map[tag], "args": args})
        return calls

    async def pipe(self, body: dict, __user__: dict = None) -> str:
        messages = body.get("messages", [])
        if not messages:
            return "No messages."

        api_client = AsyncOpenAI(
            base_url=self.valves.OWUI_API_BASE,
            api_key=self.valves.OWUI_API_KEY or os.environ.get("OWUI_API_KEY", ""),
        )

        async with httpx.AsyncClient() as http:
            path_map = await self._discover_tools(http)
            tag_map = self._build_tool_tags(path_map)
            sys_prompt = self._build_system_prompt(tag_map)
            if sys_prompt:
                messages = [{"role": "system", "content": sys_prompt}] + list(messages)
            logger.info("Discovered %d tools, %d tags", len(path_map), len(tag_map))

            response = await api_client.chat.completions.create(
                model=self.valves.BASE_MODEL, messages=messages,
                stream=False, timeout=60.0,
            )
            content = response.choices[0].message.content or ""

            max_loops = 5
            while max_loops > 0:
                text_calls = self._extract_text_tool_calls(content, tag_map)
                if not text_calls:
                    break
                max_loops -= 1
                logger.info("Text tool calls: %s", [(c["tool"], c["args"]) for c in text_calls])

                # Execute tools
                results = []
                for tc in text_calls:
                    result = await self._execute_tool(http, tc["tool"], tc["args"], path_map)
                    results.append((tc["tool"], result))

                # Feed results back to model
                results_text = "\n".join(
                    f"<result_{name}>\n{text}\n</result_{name}>"
                    for name, text in results
                )
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": (
                    f"Here are the results of your tool calls:\n{results_text}\n\n"
                    "Now provide your final answer to the user. Do NOT output any XML or HTML tags."
                )})

                response = await api_client.chat.completions.create(
                    model=self.valves.BASE_MODEL, messages=messages,
                    stream=False, timeout=60.0,
                )
                content = response.choices[0].message.content or ""

            return content
