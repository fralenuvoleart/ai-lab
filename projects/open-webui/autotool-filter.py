"""
title: Simple AutoTool Filter
author: AI Lab
version: 1.0.1
required_open_webui_version: 0.5.0
description: Filters tool_ids based on keywords. Zero dependencies.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional


KEYWORD_MAP = {
    "memory": ["remember", "save", "memory", "preference", "preferences",
               "personal", "profile", "fact", "note"],
    "github": ["github", "repo", "repository", "pull request", "pr",
               "commit", "branch", "issue", "code review", "git"],
    "fetch": ["fetch", "url", "webpage", "scrape", "website", "http",
              "download", "read this page", "summarize this"],
}


class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="Filter priority")

    def __init__(self):
        self.valves = self.Valves()

    async def inlet(self, body: dict, __user__: Optional[dict] = None, **kwargs) -> dict:
        messages = body.get("messages", [])
        if not messages:
            return body

        # Get last user message (no imports needed)
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "").lower()
                break

        if not user_message:
            return body

        tool_ids = body.get("tool_ids", [])
        if not tool_ids:
            return body

        # Match categories
        matched = set()
        for category, keywords in KEYWORD_MAP.items():
            if any(kw in user_message for kw in keywords):
                matched.add(category)

        if not matched:
            return body

        # Keep only matching tool IDs
        kept = [tid for tid in tool_ids if any(cat in tid.lower() for cat in matched)]

        if kept:
            body["tool_ids"] = kept

        return body
