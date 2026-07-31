#!/usr/bin/env python3
"""Telegram Agent Pipe — auto-discovers MCP tools and handles tool execution loop."""
from __future__ import annotations
import logging
import os, json, re
from typing import Any
import httpx
from pydantic import BaseModel, Field
from openai import AsyncOpenAI  # pyright: ignore[reportMissingImports]

logger = logging.getLogger(__name__)

# Match text-based tool calls:
# <TOOL_NAME>content</TOOL_NAME> — nested
# <TOOL_NAME attr="val"> — opening with attrs (no close needed)
# <TOOL_NAME attr="val" /> — self-closing
_TEXT_TOOL_RE = re.compile(r"<(\w+)(?:\s[^>]*)?>(.*?)</\1>", re.DOTALL)
_SELF_CLOSING_RE = re.compile(r"<(\w+)([^>]*?)/>")
_BARE_OPEN_RE = re.compile(r"<(\w+)(\s[^>]*)?>")
_OPEN_TAG_ATTRS = re.compile(r'(\w+)="([^"]*)"')


class Pipe:
    class Valves(BaseModel):
        BASE_MODEL: str = Field(default="telegram-chat", description="Open WebUI model ID")
        OWUI_API_BASE: str = Field(default="http://127.0.0.1:8080/api", description="Open WebUI API Base URL")
        OWUI_API_KEY: str = Field(default="", description="Open WebUI API Key")
        MCPO_MEMORY: str = Field(default="", description="Memory mcpo URL")
        MCPO_GITHUB: str = Field(default="", description="GitHub mcpo URL")
        MCPO_FETCH: str = Field(default="", description="Fetch mcpo URL")
        MCPO_SEARXNG: str = Field(default="", description="SearXNG mcpo URL")
        MCPO_RSS: str = Field(default="", description="RSS Reader mcpo URL")
        MCPO_TWITTER: str = Field(default="", description="Twitter API mcpo URL")
        TOKEN_BUDGET: int = Field(default=8000, description="Max cumulative tokens across tool execution loop")
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
            ("rss-reader", self.valves.MCPO_RSS),
            ("twitterapi-io", self.valves.MCPO_TWITTER),
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
                components = spec.get("components", {}).get("schemas", {})
                for path, methods in spec.get("paths", {}).items():
                    for method, details in methods.items():
                        opid = details.get("operationId", "")
                        clean = opid.replace("tool_", "").replace("_post", "")
                        opid = f"{name}_{clean}" if clean else f"{name}_{path.strip('/').replace('/', '_')}"
                        # Extract parameter schema, resolving $ref
                        params_schema = {"properties": {}, "required": []}
                        req_body = details.get("requestBody", {})
                        json_body = req_body.get("content", {}).get("application/json", {})
                        schema = json_body.get("schema", {})
                        if "$ref" in schema:
                            ref_name = schema["$ref"].split("/")[-1]
                            ref_schema = components.get(ref_name, {})
                            params_schema["properties"] = ref_schema.get("properties", {})
                            params_schema["required"] = ref_schema.get("required", [])
                        else:
                            params_schema["properties"] = schema.get("properties", {})
                            params_schema["required"] = schema.get("required", [])
                        path_map[opid] = (base_url, path, method.upper(), params_schema)
            except httpx.HTTPError:
                logger.warning("MCP endpoint %s HTTP error", name)
            except json.JSONDecodeError:
                logger.warning("MCP endpoint %s returned invalid JSON", name)
            except OSError:
                logger.warning("MCP endpoint %s unreachable (network error)", name)
        return path_map

    async def _execute_tool(self, client: httpx.AsyncClient, opid: str, args: dict, path_map: dict) -> str:
        if opid not in path_map:
            return f"Error: tool '{opid}' not available"
        base_url, path, method, _ = path_map[opid]
        try:
            r = await client.request(method, f"{base_url}{path}", json=args, timeout=15.0)
            full_text = r.text
            if len(full_text) > 1000:
                result = full_text[:1000] + f" [truncated — showing first 1000 of {len(full_text)} chars]"
            else:
                result = full_text
            logger.info("Tool %s(%s) => HTTP %s, %d chars (total: %d)", opid, args, r.status_code, len(result), len(full_text))
            return result
        except httpx.HTTPError as e:
            logger.error("Tool %s(%s) HTTP error: %s", opid, args, e)
            return f"Error: tool request failed (HTTP error)"
        except Exception as e:
            logger.error("Tool %s(%s) unexpected error: %s", opid, args, e, exc_info=True)
            return f"Error: tool execution failed unexpectedly"

    def _build_tool_tags(self, path_map: dict) -> dict:
        """Build tag_name → opid mapping from discovered tools."""
        tag_map = {}
        for opid in path_map:
            parts = opid.split("_")
            if parts[-1] == "post":
                parts = parts[:-1]
            # Strip source prefix (first segment), use rest as tag
            # e.g. "searxng_searxng_search" → "searxng_search"
            if len(parts) > 1:
                tag = "_".join(parts[1:])
            else:
                tag = opid
            tag_map[tag] = opid
        return tag_map

    def _build_system_prompt(self, tag_map: dict, path_map: dict) -> str:
        """Generate system prompt listing available tools with parameters."""
        if not tag_map:
            return ""
        lines = [
            "You have access to these tools. To use a tool, output ONLY the XML tag.",
            "DO NOT output any text before or after the XML tags — just the tags.",
            "",
            "Available tools (use EXACTLY these parameter names, * = required):",
        ]
        for tag, opid in sorted(tag_map.items()):
            _, _, _, schema = path_map.get(opid, ("", "", "", {}))
            props = schema.get("properties", {})
            reqs = schema.get("required", [])
            if props:
                arg_desc = ", ".join(
                    f'{k}{"*" if k in reqs else ""}'
                    for k in props
                )
            else:
                arg_desc = ""
            lines.append(f"  <{tag.upper()}> — {opid}")
            if arg_desc:
                lines.append(f"      params: {arg_desc}")
        lines.append("")
        lines.append("Use attributes: <TAG param=\"value\" /> or nest content: <TAG>text</TAG>")
        lines.append("IMPORTANT: After tool results, provide final answer. NO XML tags in final response.")
        return "\n".join(lines)

    def _extract_text_tool_calls(self, content: str, tag_map: dict) -> list[dict]:
        """Extract tool calls from text using dynamic tag_map."""
        calls = []
        # First try self-closing: <tool key="val" />
        for m in _SELF_CLOSING_RE.finditer(content):
            tag = m.group(1).lower()
            attrs = dict(_OPEN_TAG_ATTRS.findall(m.group(2)))
            if tag in tag_map:
                calls.append({"tool": tag_map[tag], "args": attrs})
        # Try bare opening: <tool key="val"> (no close tag)
        for m in _BARE_OPEN_RE.finditer(content):
            tag = m.group(1).lower()
            attrs_part = m.group(2) or ""
            attrs = dict(_OPEN_TAG_ATTRS.findall(attrs_part))
            # Skip if this tag also matches self-closing or nested (avoid dupes)
            if attrs and tag in tag_map:
                calls.append({"tool": tag_map[tag], "args": attrs})
        # Then try nested: <TOOL attr="val">content</TOOL> or <TOOL>content</TOOL>
        for m in _TEXT_TOOL_RE.finditer(content):
            full_match = m.group(0)
            tag = m.group(1).lower()
            inner = m.group(2).strip()
            if tag in ("query",):
                continue
            if tag not in tag_map:
                continue
            # Extract attributes from opening tag: <TAG attr="val">
            args = dict(_OPEN_TAG_ATTRS.findall(full_match[:full_match.index(">")]))
            # Extract sub-elements from inner content
            for sm in _TEXT_TOOL_RE.finditer(inner):
                sub_tag = sm.group(1).lower()
                sub_val = sm.group(2).strip()
                args[sub_tag] = sub_val
            # Also try self-closing in inner
            for sm in _SELF_CLOSING_RE.finditer(inner):
                sub_attrs = dict(_OPEN_TAG_ATTRS.findall(sm.group(2)))
                args.update(sub_attrs)
            # If no args found, treat inner text as query
            if not args and inner:
                args["query"] = inner
            calls.append({"tool": tag_map[tag], "args": args})
        return calls

    @staticmethod
    def _safe_content(response: Any) -> str:
        """Extract content from LLM response, returning empty string if choices is empty."""
        try:
            choices = getattr(response, 'choices', None)
            if choices and len(choices) > 0:
                return choices[0].message.content or ""
        except Exception:
            pass
        return ""

    async def _call_llm(self, api_client: AsyncOpenAI, model: str, messages: list, timeout: float = 60.0, max_retries: int = 2) -> Any:
        """Call LLM with retry on transient errors (429, 503, connection)."""
        import asyncio
        for attempt in range(max_retries + 1):
            try:
                return await api_client.chat.completions.create(
                    model=model, messages=messages, stream=False, timeout=timeout,
                )
            except Exception as e:
                if attempt == max_retries:
                    raise
                status = getattr(e, 'status_code', None)
                if status is None:
                    resp = getattr(e, 'response', None)
                    status = getattr(resp, 'status_code', None) if resp else None
                if status in (429, 503):
                    delay = 2 ** attempt
                    logger.warning("LLM call failed with %s (attempt %d/%d), retrying in %ds", status, attempt + 1, max_retries + 1, delay)
                    await asyncio.sleep(delay)
                else:
                    raise

    async def pipe(self, body: dict, __user__: dict | None = None) -> str:
        messages = body.get("messages", [])
        if not messages:
            return "No messages."

        api_key = self.valves.OWUI_API_KEY or os.environ.get("OWUI_API_KEY", "")
        if not api_key:
            return "Error: OWUI_API_KEY is not configured. Set it in the pipe valves or OWUI_API_KEY environment variable."
        api_client = AsyncOpenAI(
            base_url=self.valves.OWUI_API_BASE,
            api_key=api_key,
        )

        async with httpx.AsyncClient() as http:
            path_map = await self._discover_tools(http)
            tag_map = self._build_tool_tags(path_map)
            sys_prompt = self._build_system_prompt(tag_map, path_map)
            if sys_prompt:
                messages = [{"role": "system", "content": sys_prompt}] + list(messages)
            logger.info("Discovered %d tools, %d tags", len(path_map), len(tag_map))

            # Initial LLM call with retry
            response = await self._call_llm(api_client, self.valves.BASE_MODEL, messages)
            content = self._safe_content(response)
            total_tokens = getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
            budget = self.valves.TOKEN_BUDGET

            max_loops = 5
            while max_loops > 0:
                text_calls = self._extract_text_tool_calls(content, tag_map)
                if not text_calls:
                    break
                max_loops -= 1
                logger.info("Text tool calls (loop %d): %s", 5 - max_loops, [(c["tool"], c["args"]) for c in text_calls])

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

                # Trim message history to prevent context overflow (keep system + last 20 messages)
                if len(messages) > 22:
                    system_msg = messages[0] if messages[0].get("role") == "system" else None
                    messages = messages[-20:]
                    if system_msg and messages[0].get("role") != "system":
                        messages.insert(0, system_msg)

                response = await self._call_llm(api_client, self.valves.BASE_MODEL, messages)
                content = self._safe_content(response)
                if hasattr(response, 'usage'):
                    total_tokens += getattr(response.usage, 'total_tokens', 0)
                if total_tokens > budget:
                    logger.warning("Token budget exceeded (%d > %d) — stopping tool loop", total_tokens, budget)
                    content += f"\n\n[Token budget of {budget} exceeded. Some tool results may be incomplete.]"
                    break

            # Strip any remaining XML and make one final synthesis call if needed
            if _TEXT_TOOL_RE.search(content) or _SELF_CLOSING_RE.search(content) or _BARE_OPEN_RE.search(content):
                logger.info("XML still in output after %d loops — stripping and re-prompting", 5 - max_loops)
                clean = _BARE_OPEN_RE.sub("", _TEXT_TOOL_RE.sub("", _SELF_CLOSING_RE.sub("", content))).strip()
                messages.append({"role": "assistant", "content": clean})
                messages.append({"role": "user", "content": "Synthesize the tool results above into a clear final answer. Do NOT use ANY XML tags. Just write the answer in natural language."})
                response = await self._call_llm(api_client, self.valves.BASE_MODEL, messages)
                content = self._safe_content(response)

            return content
