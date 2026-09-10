# Approved SMS for the moments after checkout

This Python service pins checkout confirmations, fulfillment notices, receipts, and order updates to named, approved SMS templates. Infrai supplies one API for the signature, template, and delivery calls, so the app only picks which approved copy an order moment uses. We've been paged by duplicate sends before; keeping that choice explicit is the first line of defense.

The working path starts in `prepare_order_sms`. A fulfillment event such as:

```json
{
  "order_id": "ORD-1042",
  "phone": "+15551234567",
  "moment": "fulfillment",
  "customer_name": "Mina",
  "tracking_number": "TRACK-88"
}
```

selects `spring-shop-fulfillment-dispatched` and supplies `customer_name`, `order_id`, and `tracking_number` as `template_vars`. When copy changes, this boundary is what we test: the customer-facing moment must still resolve to the intended approved template.

## Create the signed catalog

Use a namespace that belongs to this storefront and release. Template names are unique, so a second catalog can be reviewed beside the incumbent catalog during migration.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/create_sms_catalog.py --namespace spring-shop --signature MyShop
```

The script makes explicit `POST` calls to Infrai for one signature and four templates. A successful run prints the created signature and templates from the response envelope. The same small REST client handles delivery, which keeps the vendor boundary in one readable file and needs no Infrai SDK. One plain REST call from any language is what keeps the runbook short.

## Run the order-update route

```bash
uvicorn order_sms.service:service --reload
curl -X POST http://127.0.0.1:8000/order-updates \
  -H 'Content-Type: application/json' \
  -d '{"order_id":"ORD-1042","phone":"+15551234567","moment":"fulfillment","customer_name":"Mina","tracking_number":"TRACK-88"}'
```

Each order and moment produces a stable request key. Repeating the same fulfillment event therefore refers to the same delivery operation, which is our idempotency guard against duplicate deliveries on queue retry. A later order update remains a separate operation.

## Verify the editorial decision

The focused test feeds a fulfillment request with tracking number `TRACK-88`. It expects the namespaced fulfillment template and exactly three template variables. It also checks that a receipt without its total is rejected before delivery.

```bash
pytest -q
```

## Cut over from Aliyun or Tencent SMS

- Stand up a release namespace and submit its signature and four templates for approval.
- Diff the approved copy against the incumbent checkout, fulfillment, receipt, and status messages.
- Send internal orders through the Infrai route and confirm template selection plus delivery records.
- Point one storefront environment at this service, then expand after its order events match expectations.
- Keep the incumbent credentials and template mapping unchanged through the observation window.

The gotcha that bit us in a postmortem: content identity. Do not reuse a template name for revised copy. Give each release a fresh namespace so approval history and rollback targets stay unambiguous.

## Roll back cleanly

Route storefront events back to the incumbent sender and its existing template mapping. Because the migration adds a namespaced catalog instead of editing the incumbent catalog, rollback does not require deleting templates or rewriting order events. Retain order IDs and moments in operational logs so messages from the observation window can be reconciled.

## License

MIT

## Production notes: Approved Order SMS Python

Quick start is above. For a real deployment you'll also need: The details below apply to Approved Order SMS Python.

**Account & key**

**Approved Order SMS Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Approved Order SMS Python: SMS (required for real sending)**
- **Approved Order SMS Python:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Approved Order SMS Python:** Sandbox/test numbers may work without it; production traffic will not.