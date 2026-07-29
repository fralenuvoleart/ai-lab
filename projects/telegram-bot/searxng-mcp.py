#!/usr/bin/env python3
"""Minimal MCP server wrapping SearXNG JSON API."""
import json, sys, requests

SEARXNG_URL = "http://127.0.0.1:8888"

async def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method", "")
            rid = req.get("id")

            if method == "initialize":
                resp = {"jsonrpc": "2.0", "id": rid, "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "searxng", "version": "1.0"}
                }}
            elif method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": rid, "result": {"tools": [{
                    "name": "searxng_search",
                    "description": "Search the web using SearXNG. Returns titles, URLs, snippets, and source engine names.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"query": {"type": "string", "description": "Search query"}},
                        "required": ["query"]
                    }
                }]}}
            elif method == "tools/call":
                args = req["params"]["arguments"]
                query = args.get("query", "")
                try:
                    r = requests.get(f"{SEARXNG_URL}/search", params={"q": query, "format": "json"}, timeout=10)
                    data = r.json()
                    results = data.get("results", [])[:5]
                    if results:
                        lines = []
                        for res in results:
                            t = res.get("title", "No title")
                            u = res.get("url", "")
                            c = res.get("content", "")[:200]
                            e = ", ".join(res.get("engines", []))
                            s = res.get("score", 0)
                            lines.append(f"- {t} [{e}] (score: {s:.1f})\n  {u}\n  {c}")
                        text = "\n\n".join(lines)
                    else:
                        text = "No results found."
                    resp = {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}]}}
                except Exception as e:
                    resp = {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": f"Search error: {e}"}]}}
            elif method == "notifications/initialized":
                continue
            else:
                resp = {"jsonrpc": "2.0", "id": rid, "result": {}}

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
