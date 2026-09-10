from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    BaseModel = None


class OrderMoment(str, Enum):
    CHECKOUT = "checkout"
    FULFILLMENT = "fulfillment"
    RECEIPT = "receipt"
    ORDER_UPDATE = "order_update"


if BaseModel is not None:
    class OrderSmsRequest(BaseModel):
        order_id: str = Field(min_length=1)
        phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
        moment: OrderMoment
        customer_name: str = Field(min_length=1)
        status: str | None = None
        tracking_number: str | None = None
        receipt_total: str | None = None


    class PreparedSms(BaseModel):
        template_name: str
        template_vars: dict[str, str]
else:
    @dataclass
    class OrderSmsRequest:
        order_id: str
        phone: str
        moment: OrderMoment
        customer_name: str
        status: str | None = None
        tracking_number: str | None = None
        receipt_total: str | None = None

        def __post_init__(self) -> None:
            if not self.order_id or not self.customer_name:
                raise ValueError("order_id and customer_name must not be empty")
            if not re.fullmatch(r"\+[1-9]\d{7,14}", self.phone):
                raise ValueError("phone must be in E.164 format")
            self.moment = OrderMoment(self.moment)


    @dataclass
    class PreparedSms:
        template_name: str
        template_vars: dict[str, str]


class SmsSender(Protocol):
    def send(self, payload: dict[str, object], idempotency_key: str) -> dict[str, object]:
        pass


TEMPLATES = {
    OrderMoment.CHECKOUT: "checkout-confirmed",
    OrderMoment.FULFILLMENT: "fulfillment-dispatched",
    OrderMoment.RECEIPT: "payment-receipt",
    OrderMoment.ORDER_UPDATE: "order-status-update",
}


def prepare_order_sms(request: OrderSmsRequest, namespace: str) -> PreparedSms:
    values = {"customer_name": request.customer_name, "order_id": request.order_id}
    if request.moment is OrderMoment.FULFILLMENT:
        values["tracking_number"] = _required(request.tracking_number, "tracking_number")
    elif request.moment is OrderMoment.RECEIPT:
        values["receipt_total"] = _required(request.receipt_total, "receipt_total")
    elif request.moment is OrderMoment.ORDER_UPDATE:
        values["status"] = _required(request.status, "status")
    return PreparedSms(template_name=f"{namespace}-{TEMPLATES[request.moment]}", template_vars=values)


def send_order_sms(request: OrderSmsRequest, namespace: str, sender: SmsSender) -> dict[str, object]:
    prepared = prepare_order_sms(request, namespace)
    key = hashlib.sha256(f"{request.order_id}:{request.moment.value}".encode()).hexdigest()
    return sender.send(
        {"to": request.phone, "template_id": prepared.template_name, "template_vars": prepared.template_vars},
        idempotency_key=f"order-sms-{key}",
    )


def _required(value: str | None, field: str) -> str:
    if not value:
        raise ValueError(f"{field} is required for this order moment")
    return value
