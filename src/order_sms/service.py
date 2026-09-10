from fastapi import FastAPI, HTTPException

from .infrai_sms import InfraiError, InfraiSms
from .order_updates import OrderSmsRequest, send_order_sms

service = FastAPI(title="Approved order SMS")


@service.post("/order-updates")
def publish_order_update(request: OrderSmsRequest) -> dict[str, object]:
    try:
        return send_order_sms(request, "shop", InfraiSms())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InfraiError as exc:
        client_status = exc.status if 400 <= exc.status < 500 else 502
        raise HTTPException(status_code=client_status, detail={"code": exc.code, "detail": exc.detail}) from exc

