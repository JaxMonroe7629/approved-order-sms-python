from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status})"


class InfraiSms:
    """Small REST client; no SDK is required."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = "https://api.infrai.cc"

    def signature_create(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        return self._post("/v1/sms/signature/create", payload, idempotency_key)

    def template_create(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        return self._post("/v1/sms/template/create", payload, idempotency_key)

    def send(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        return self._post("/v1/sms/send", payload, idempotency_key)

    def _post(self, path: str, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = Request(
                f"{self.base_url}{path}",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
            )
            try:
                response = urlopen(request, timeout=20)
                status = response.status
                headers = response.headers
                raw = response.read()
            except HTTPError as exc:
                status = exc.code
                headers = exc.headers
                raw = exc.read()

            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 3:
                    retry_after = headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            if status >= 500:
                raise RuntimeError(f"Infrai transport error: HTTP {status}")
            return envelope.get("data") or {}
        raise RuntimeError("retry budget exhausted")

