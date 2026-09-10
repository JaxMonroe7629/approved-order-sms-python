import pytest

from order_sms.order_updates import OrderMoment, OrderSmsRequest, prepare_order_sms


def test_fulfillment_selects_approved_template_and_tracking_fields() -> None:
    request = OrderSmsRequest(
        order_id="ORD-1042",
        phone="+15551234567",
        moment=OrderMoment.FULFILLMENT,
        customer_name="Mina",
        tracking_number="TRACK-88",
    )

    prepared = prepare_order_sms(request, "spring-shop")

    assert prepared.template_name == "spring-shop-fulfillment-dispatched"
    assert prepared.template_vars == {
        "customer_name": "Mina",
        "order_id": "ORD-1042",
        "tracking_number": "TRACK-88",
    }


def test_receipt_requires_a_total() -> None:
    request = OrderSmsRequest(
        order_id="ORD-1043",
        phone="+15551234567",
        moment=OrderMoment.RECEIPT,
        customer_name="Mina",
    )
    with pytest.raises(ValueError, match="receipt_total"):
        prepare_order_sms(request, "spring-shop")

