"""
HTTP request tool.

Input format: "METHOD URL" (e.g. "GET https://api.example.com/data"),
defaulting to GET if only a URL is given. Blocks requests to loopback,
link-local, and private-network addresses by resolving the hostname
before connecting — basic SSRF protection so a workflow can't be used
to reach internal services (the backend container, the database,
other services on a private Docker network) via a crafted URL. This is
best-effort at the application layer, not a substitute for network-level
egress controls in a genuinely multi-tenant deployment.
"""
import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from app.services.tools.base import Tool, ToolContext, ToolError

ALLOWED_METHODS = {"GET", "POST"}


def _is_safe_host(hostname: str) -> bool:
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False
    return True


class HttpRequestTool(Tool):
    name = "http_request"
    description = (
        "Makes an HTTP GET or POST request. Input: 'METHOD URL' or just a URL (defaults to GET)."
    )

    async def run(self, input_text: str, *, context: ToolContext | None = None) -> str:
        parts = input_text.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[0].upper() in ALLOWED_METHODS:
            method, url = parts[0].upper(), parts[1]
        else:
            method, url = "GET", input_text.strip()

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ToolError("Only http:// and https:// URLs are allowed")
        if not parsed.hostname:
            raise ToolError("Invalid URL")
        if not _is_safe_host(parsed.hostname):
            raise ToolError(
                "Requests to private, loopback, or link-local addresses are not allowed"
            )

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
                response = await client.request(method, url)
        except httpx.RequestError as exc:
            raise ToolError(f"Request failed: {exc}") from exc

        body = response.text
        if len(body) > 4000:
            body = body[:4000] + "... [truncated]"
        return f"HTTP {response.status_code}\n{body}"
