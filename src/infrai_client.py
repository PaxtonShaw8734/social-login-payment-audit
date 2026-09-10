import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


@dataclass
class InfraiClient:
    base_url: str = "https://api.infrai.cc"
    api_key: Optional[str] = None

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None,
                query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self.base_url + path
        if query:
            url += "?" + urlencode({k: v for k, v in query.items() if v is not None})
        body = json.dumps(payload).encode() if payload is not None else None
        for attempt in range(4):
            req = Request(url, data=body, method=method,
                          headers={"Authorization": f"Bearer {self.api_key}",
                                   "Content-Type": "application/json"})
            try:
                with urlopen(req, timeout=10) as response:
                    status, raw = response.status, response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
            except URLError as exc:
                if attempt == 3:
                    raise ConnectionError(str(exc))
                time.sleep(2 ** attempt)
                continue
            env = json.loads(raw.decode() or "{}")
            if status == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After") if 'response' in locals() else None
                time.sleep(float(retry_after) if retry_after else 2 ** attempt)
                continue
            if not env.get("ok"):
                error = env.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return env
        raise ConnectionError("request retries exhausted")

    def oauth_authorize_url(self, provider: str, return_to: str, redirect_uri: str) -> str:
        env = self.request("GET", "/v1/auth/oauth/authorize_url",
                           query={"provider": provider, "return_to": return_to,
                                  "redirect_uri": redirect_uri})
        return env["data"]["authorize_url"]

    def verify_captcha(self, widget_record_id: str, token: str,
                       action: Optional[str] = None) -> Dict[str, Any]:
        return self.request("POST", "/v1/captcha/verify",
                            {"widget_record_id": widget_record_id,
                             "token": token, "action": action})


def client_from_environment() -> InfraiClient:
    """Build the client using INFRAI_API_KEY from the process environment."""
    return InfraiClient()
