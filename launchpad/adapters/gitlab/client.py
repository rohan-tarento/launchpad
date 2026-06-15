"""GitLab REST API client (GITLAB_TOKEN + optional GITLAB_HOST)."""

from __future__ import annotations

import os
import time
import urllib.parse
from typing import Any

import httpx

_TRANSIENT_HTTP = frozenset({408, 429, 500, 502, 503, 504})


class GitLabError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class GitLabClient:
    def __init__(
        self,
        token: str | None = None,
        *,
        host: str | None = None,
        dry_run: bool = True,
    ) -> None:
        self.host = (host or os.environ.get("GITLAB_HOST") or "https://gitlab.com").rstrip("/")
        self.token = token or os.environ.get("GITLAB_TOKEN") or os.environ.get("GITLAB_PRIVATE_TOKEN")
        if not self.token and not dry_run:
            raise GitLabError(
                "GITLAB_TOKEN not set. Export GITLAB_TOKEN or GITLAB_PRIVATE_TOKEN. "
                "See playbook/bootstrap-prerequisites.md."
            )
        self.dry_run = dry_run
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        self._http = httpx.Client(base_url=f"{self.host}/api/v4", headers=headers, timeout=60.0)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> GitLabClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def whoami(self) -> str:
        return str(self.rest("GET", "/user").get("username", ""))

    def rest(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        if self.dry_run and method != "GET":
            print(f"[dry-run] {method} {path} {json_body or ''}")
            return {}
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                resp = self._http.request(method, path, json=json_body, params=params)
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(0.5 * (2**attempt))
                continue
            if resp.status_code in _TRANSIENT_HTTP:
                time.sleep(0.5 * (2**attempt))
                continue
            if resp.status_code >= 400:
                raise GitLabError(
                    f"GitLab API {method} {path} failed: {resp.status_code}",
                    status=resp.status_code,
                    body=resp.text,
                )
            if resp.status_code == 204 or not resp.content:
                return {}
            return resp.json()
        raise GitLabError(f"GitLab API failed after retries: {last_exc}")

    @staticmethod
    def encode_project(path: str) -> str:
        """Namespace/project → URL-encoded id for API paths."""
        return urllib.parse.quote(path, safe="")

    def project(self, group: str, repo: str) -> dict[str, Any]:
        project_path = f"{group}/{repo}"
        if self.dry_run:
            return {"id": 0, "path_with_namespace": project_path, "web_url": f"{self.host}/{project_path}"}
        return self.rest("GET", f"/projects/{self.encode_project(project_path)}")

    def ensure_label(self, project_id: int, name: str, *, color: str = "#1E3A8A") -> None:
        if self.dry_run or project_id == 0:
            print(f"[dry-run] ensure label {name!r} on project {project_id}")
            return
        labels = self.rest("GET", f"/projects/{project_id}/labels")
        if isinstance(labels, list) and any(lb.get("name") == name for lb in labels):
            return
        self.rest(
            "POST",
            f"/projects/{project_id}/labels",
            json_body={"name": name, "color": color},
        )

    def find_issue_by_title(self, project_id: int, title: str) -> dict[str, Any] | None:
        issues = self.rest(
            "GET",
            f"/projects/{project_id}/issues",
            params={"search": title[:80], "in": "title"},
        )
        if not isinstance(issues, list):
            return None
        for issue in issues:
            if issue.get("title") == title:
                return issue
        return None

    def create_issue(
        self,
        project_id: int,
        *,
        title: str,
        description: str,
        labels: list[str],
    ) -> dict[str, Any]:
        if self.dry_run or project_id == 0:
            print(f"[dry-run] create issue {title!r} labels={labels}")
            return {"title": title, "web_url": "(dry-run)"}
        existing = self.find_issue_by_title(project_id, title)
        if existing:
            return existing
        return self.rest(
            "POST",
            f"/projects/{project_id}/issues",
            json_body={
                "title": title,
                "description": description,
                "labels": ",".join(labels),
            },
        )
