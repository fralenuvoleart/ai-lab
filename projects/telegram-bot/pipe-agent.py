"""
title: Telegram Agent Pipe
author: AI Lab
version: 1.2.1
description: Non-blocking Async server-side Pipe that auto-discovers tools and handles execution loop.
"""

import os, json
import httpx
from pydantic import BaseModel, Field
from openai import AsyncOpenAI


class Pipe:
    class Valves(BaseModel):
        BASE_MODEL: str = Field(default="deepseek-v4-pro", description="Underlying chat model ID")
        OWUI_API_BASE: str = Field(default="http://127.0.0.1:8080/api", description="Open WebUI API Base URL (container port)")
        OWUI_API_KEY: str = Field(default="", description="Open WebUI API Key")
        MCPO_MEMORY: str = Field(default="http://host.docker.internal:8000", description="Memory mcpo URL")
        MCPO_GITHUB: str = Field(default="http://host.docker.internal:8001/github", description="GitHub mcpo URL")
        MCPO_FETCH: str = Field(default="http://host.docker.internal:8001/fetch", description="Fetch mcpo URL")

    def __init__(self):
        self.type = "pipe"
        self.id = "telegram-agent"
        self.name = "Telegram Agent"
        self.valves = self.Valves()

    async def _discover_tools(self, client: httpx.AsyncClient):
        tools = []
        path_map = {}
        endpoints = [
            ("memory", self.valves.MCPO_MEMORY),
            ("github", self.valves.MCPO_GITHUB),
            ("fetch", self.valves.MCPO_FETCH),
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
                        # Prefix with server name to avoid duplicates, strip tool_ prefix
                        clean = opid.replace("tool_", "").replace("_post", "")
                        opid = f"{name}_{clean}" if clean else f"{name}_{path.strip('/').replace('/', '_')}"
                        summary = details.get("summary") or details.get("description") or opid
                        schema = {"type": "object", "properties": {}}
                        req_body = details.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
                        if "$ref" in req_body:
                            ref_key = req_body["$ref"].split("/")[-1]
                            schema = components.get(ref_key, schema)
                        elif req_body:
                            schema = req_body
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": opid,
                                "description": summary[:1024],
                                "parameters": schema,
                            }
                        })
                        path_map[opid] = (base_url, path, method.upper())
            except Exception:
                pass
        return tools, path_map

    async def _execute_tool(self, client: httpx.AsyncClient, opid: str, args: dict, path_map: dict) -> str:
        if opid not in path_map:
            return f"Error: Tool '{opid}' not found."
        base_url, path, method = path_map[opid]
        try:
            r = await client.request(method, f"{base_url}{path}", json=args, timeout=15.0)
            return r.text[:1000]
        except Exception as e:
            return f"Error: {e}"

    async def pipe(self, body: dict, __user__: dict = None) -> str:
        messages = body.get("messages", [])
        if not messages:
            return "No messages."

        api_client = AsyncOpenAI(
            base_url=self.valves.OWUI_API_BASE,
            api_key=self.valves.OWUI_API_KEY or os.environ.get("OWUI_API_KEY", ""),
        )

        async with httpx.AsyncClient() as http:
            tools, path_map = await self._discover_tools(http)

            payload = {"model": self.valves.BASE_MODEL, "messages": messages, "stream": False}
            if tools:
                payload["tools"] = tools

            response = await api_client.chat.completions.create(**payload)
            choice = response.choices[0].message

            max_loops = 5
            while choice.tool_calls and max_loops > 0:
                max_loops -= 1
                assistant_msg = {"role": "assistant", "content": choice.content}
                assistant_msg["tool_calls"] = [{
                    "id": tc.id, "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                } for tc in choice.tool_calls]
                messages.append(assistant_msg)

                for tc in choice.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                    except json.JSONDecodeError:
                        args = {}
                    result = await self._execute_tool(http, tc.function.name, args, path_map)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})

                payload["messages"] = messages
                response = await api_client.chat.completions.create(**payload)
                choice = response.choices[0].message

            return choice.content or ""
