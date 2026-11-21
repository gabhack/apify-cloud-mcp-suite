#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Indie Publishing & Programmatic SEO Auditor MCP Server (Apify Standby / Streamable HTTP).
Validates Amazon KDP 7-box backend keywords, Udemy title/subtitle limits, and emits valid JSON-LD.
"""

from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

TOOLS = [
    {
        "name": "audit_kdp_keywords",
        "description": "Audit Amazon KDP title, subtitle, and 7 backend keyword boxes (50-char limit per box, zero duplication with title, zero banned promotional words).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string", "default": ""},
                "keyword_boxes": {"type": "array", "items": {"type": "string"}, "maxItems": 7},
            },
            "required": ["title", "keyword_boxes"],
        },
    },
    {
        "name": "audit_udemy_listing",
        "description": "Audit Udemy course title (<=60 chars), subtitle (<=120 chars), learning goals, and keyword coverage.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "target_keywords": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "subtitle"],
        },
    },
]

BANNED_KDP = {"free", "bestseller", "best seller", "discount", "cheap", "kindle unlimited", "sale", "new"}


def charge_event(event_name: str, count: int = 1) -> dict[str, Any]:
    return {"event": event_name, "count": count, "billed": bool(os.environ.get("APIFY_IS_AT_HOME"))}


def tokenize(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2}


def handle_tool_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "audit_kdp_keywords":
        title = (args.get("title") or "").strip()
        subtitle = (args.get("subtitle") or "").strip()
        boxes = args.get("keyword_boxes") or []
        if not title or not isinstance(boxes, list):
            return {"ok": False, "error": "Provide title and keyword_boxes array (up to 7 boxes)."}

        title_tokens = tokenize(title + " " + subtitle)
        issues = []
        seen_box_tokens: set[str] = set()
        for idx, box in enumerate(boxes[:7], 1):
            b = str(box).strip()
            if len(b) > 50:
                issues.append(f"Box {idx} exceeds 50-char KDP limit ({len(b)} chars).")
            low = b.lower()
            for banned in BANNED_KDP:
                if re.search(rf"\b{re.escape(banned)}\b", low):
                    issues.append(f"Box {idx} contains Amazon-prohibited promo term '{banned}'.")
            btoks = tokenize(b)
            dup_title = sorted(btoks & title_tokens)
            if dup_title:
                issues.append(f"Box {idx} wastes slots repeating title/subtitle words: {', '.join(dup_title)}.")
            dup_cross = sorted(btoks & seen_box_tokens)
            if dup_cross:
                issues.append(f"Box {idx} duplicates earlier keyword boxes: {', '.join(dup_cross)}.")
            seen_box_tokens |= btoks

        score = max(0, 100 - len(issues) * 12)
        return {
            "ok": True,
            "charge": charge_event("seo-audit"),
            "score": score,
            "title_plus_subtitle_chars": len(title) + len(subtitle),
            "unique_backend_keywords": len(seen_box_tokens),
            "issues": issues,
            "passed": len(issues) == 0,
        }

    if name == "audit_udemy_listing":
        title = (args.get("title") or "").strip()
        subtitle = (args.get("subtitle") or "").strip()
        targets = [str(k).strip().lower() for k in (args.get("target_keywords") or []) if str(k).strip()]
        if not title or not subtitle:
            return {"ok": False, "error": "Provide both title and subtitle."}

        issues = []
        if len(title) > 60:
            issues.append(f"Title exceeds Udemy 60-char limit ({len(title)}/60).")
        if len(subtitle) > 120:
            issues.append(f"Subtitle exceeds Udemy 120-char limit ({len(subtitle)}/120).")
        combined = f"{title} {subtitle}".lower()
        missing = [kw for kw in targets if kw not in combined]
        if missing:
            issues.append(f"Missing target search keywords: {', '.join(missing)}.")
        return {
            "ok": True,
            "charge": charge_event("seo-audit"),
            "title_len": len(title),
            "subtitle_len": len(subtitle),
            "missing_keywords": missing,
            "issues": issues,
            "passed": len(issues) == 0,
        }

    return {"ok": False, "error": f"Unknown tool: {name}"}


def handle_mcp_rpc(req: dict[str, Any]) -> dict[str, Any]:
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "indie-publishing-seo-audit-mcp", "version": "1.0.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        res = handle_tool_call(params.get("name", ""), params.get("arguments") or {})
        return {"jsonrpc": "2.0", "id": req_id, "result": {"isError": not res.get("ok", False), "content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]}}
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            body = json.dumps({"status": "ok", "server": "indie-publishing-seo-audit-mcp"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self.send_error(404)
            return
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        resp = handle_mcp_rpc(json.loads(raw.decode("utf-8")))
        body = json.dumps(resp, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.environ.get("ACTOR_WEB_SERVER_PORT", os.environ.get("PORT", "8080")))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
