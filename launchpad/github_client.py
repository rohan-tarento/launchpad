"""GitHub REST + GraphQL client using PAT (GITHUB_TOKEN)."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx

_TRANSIENT_HTTP = frozenset({408, 429, 500, 502, 503, 504})
_TRANSIENT_EXC = (
    httpx.RemoteProtocolError,
    httpx.ReadTimeout,
    httpx.ConnectTimeout,
    httpx.ConnectError,
    httpx.WriteError,
)


class GitHubError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


def _api_retries() -> int:
    try:
        return max(1, int(os.environ.get("META_API_RETRIES", "3")))
    except ValueError:
        return 3


def _retry_delay_seconds(attempt: int) -> float:
    try:
        base = max(0.0, int(os.environ.get("META_API_DELAY_MS", "500")) / 1000.0)
    except ValueError:
        base = 0.5
    return base * (2**attempt)


class GitHubClient:
    def __init__(self, token: str | None = None, *, dry_run: bool = True) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not self.token:
            if dry_run:
                self.token = "dry-run"
            else:
                raise GitHubError(
                    "GITHUB_TOKEN not set. Add it to ~/.config/launchpad/env.d/<client-id>.env "
                    "or export GITHUB_TOKEN. See docs/multi-laptop.md."
                )
        self.dry_run = dry_run
        self._rest = httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=60.0,
        )

    def close(self) -> None:
        self._rest.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def whoami(self) -> str:
        if self.dry_run and self.token == "dry-run":
            return "dry-run"
        return self.rest("GET", "/user")["login"]

    def _request(self, method: str, path: str, *, json_body: dict | None = None, params: dict | None = None) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(_api_retries()):
            try:
                return self._rest.request(method, path, json=json_body, params=params)
            except _TRANSIENT_EXC as exc:
                last_exc = exc
                if attempt + 1 >= _api_retries():
                    break
                delay = _retry_delay_seconds(attempt)
                print(f"  [retry] {method} {path} — {exc!s}; wait {delay:.1f}s")
                time.sleep(delay)
        raise GitHubError(f"{method} {path} failed after retries", body=str(last_exc)) from last_exc

    def rest(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        path = path if path.startswith("/") else f"/{path}"
        if self.dry_run and method != "GET":
            print(f"[dry-run] {method} {path}")
            return {}
        last_error: GitHubError | None = None
        for attempt in range(_api_retries()):
            r = self._request(method, path, json_body=json_body, params=params)
            if r.status_code == 204:
                return {}
            if r.status_code in _TRANSIENT_HTTP and attempt + 1 < _api_retries():
                delay = _retry_delay_seconds(attempt)
                print(f"  [retry] {method} {path} — HTTP {r.status_code}; wait {delay:.1f}s")
                time.sleep(delay)
                continue
            if r.status_code >= 400:
                last_error = GitHubError(f"{method} {path} failed", r.status_code, r.text)
                if attempt + 1 < _api_retries() and r.status_code in _TRANSIENT_HTTP:
                    time.sleep(_retry_delay_seconds(attempt))
                    continue
                raise last_error
            if not r.content:
                return {}
            return r.json()
        if last_error:
            raise last_error
        return {}

    def graphql(self, query: str, variables: dict | None = None) -> dict:
        if self.dry_run and self.token == "dry-run":
            return {}
        if self.dry_run and "mutation" in query.lower():
            print(f"[dry-run] GraphQL mutation")
            return {}
        last_error: GitHubError | None = None
        for attempt in range(_api_retries()):
            try:
                r = self._request(
                    "POST",
                    "/graphql",
                    json_body={"query": query, "variables": variables or {}},
                )
            except GitHubError:
                if attempt + 1 >= _api_retries():
                    raise
                time.sleep(_retry_delay_seconds(attempt))
                continue
            data = r.json()
            if r.status_code in _TRANSIENT_HTTP and attempt + 1 < _api_retries():
                delay = _retry_delay_seconds(attempt)
                print(f"  [retry] GraphQL — HTTP {r.status_code}; wait {delay:.1f}s")
                time.sleep(delay)
                continue
            if r.status_code >= 400 or data.get("errors"):
                last_error = GitHubError(
                    "GraphQL error",
                    r.status_code,
                    json.dumps(data.get("errors", data), indent=2),
                )
                if attempt + 1 < _api_retries():
                    time.sleep(_retry_delay_seconds(attempt))
                    continue
                raise last_error
            return data.get("data", {})
        if last_error:
            raise last_error
        return {}

    def org_ok(self, org: str) -> bool:
        if self.dry_run and self.token == "dry-run":
            return True
        try:
            self.rest("GET", f"/orgs/{org}")
            return True
        except GitHubError:
            return False
