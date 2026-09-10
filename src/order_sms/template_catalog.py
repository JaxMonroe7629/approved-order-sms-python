from __future__ import annotations

import hashlib
from typing import Protocol


class CatalogClient(Protocol):
    def signature_create(self, payload: dict[str, object], idempotency_key: str) -> dict[str, object]:
        pass

    def template_create(self, payload: dict[str, object], idempotency_key: str) -> dict[str, object]:
        pass


CONTENT = {
    "checkout-confirmed": "Hi {{customer_name}}, order {{order_id}} is confirmed.",
    "fulfillment-dispatched": "Hi {{customer_name}}, order {{order_id}} shipped. Tracking: {{tracking_number}}.",
    "payment-receipt": "Hi {{customer_name}}, receipt for order {{order_id}}: {{receipt_total}}.",
    "order-status-update": "Hi {{customer_name}}, order {{order_id}} is now {{status}}.",
}


def create_catalog(client: CatalogClient, namespace: str, signature: str) -> dict[str, object]:
    signature_name = signature
    created_signature = client.signature_create(
        {"name": signature_name},
        idempotency_key=_key("signature", signature_name),
    )
    templates = []
    for short_name, content in CONTENT.items():
        name = f"{namespace}-{short_name}"
        templates.append(
            client.template_create(
                {"name": name, "body": content},
                idempotency_key=_key("template", name),
            )
        )
    return {"signature": created_signature, "templates": templates}


def _key(kind: str, name: str) -> str:
    digest = hashlib.sha256(name.encode()).hexdigest()
    return f"catalog-{kind}-{digest}"
