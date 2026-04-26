from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from ..exceptions import ApiError, AuthError, RateLimitError

if TYPE_CHECKING:
    from ..auth.authenticator import Authenticator
    from ..config import Endpoints


class BaseResource:
    def __init__(self, http: httpx.Client, auth: "Authenticator", endpoints: "Endpoints", shop_id: str | None = None, commerce_id: str | None = None) -> None:
        self._http = http
        self._auth = auth
        self._endpoints = endpoints
        self._shop_id = shop_id
        self._commerce_id = commerce_id

    def request(
        self,
        method: str,
        url: str,
        *,
        retry_on_401: bool = True,
        **kwargs: Any,
    ) -> Any:
        token = self._auth.ensure_valid()
        
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token.access_token}"
        if self._shop_id:
            headers["shop_id"] = self._shop_id
        
        req = self._http.build_request(method, url, headers=headers, **kwargs)
        self._print_curl(req)
        resp = self._http.send(req)
        
        if resp.status_code == 401 and retry_on_401:
            token = self._auth.refresh()
            headers["Authorization"] = f"Bearer {token.access_token}"
            req = self._http.build_request(method, url, headers=headers, **kwargs)
            self._print_curl(req)
            resp = self._http.send(req)

        self._raise_for_status(resp)
        if resp.content:
            return resp.json()
        return None

    @staticmethod
    def _print_curl(req: httpx.Request) -> None:
        parts = [f"-X {req.method} '{req.url}'"]
        for name, value in req.headers.items():
            parts.append(f"-H '{name}: {value}'")
        body = req.content
        if body:
            parts.append(f"--data-raw '{body.decode()}'")
        print("curl " + " \\\n  ".join(parts))

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return

        if resp.status_code == 401:
            raise AuthError(f"Unauthorized [{resp.status_code}]: {resp.text}")

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )

        message = resp.text
        code = None
        try:
            body = resp.json()
            message = body.get("message") or body.get("error") or message
            code = body.get("code")
        except Exception:
            pass

        raise ApiError(status=resp.status_code, message=message, code=code, payload=resp.text)
