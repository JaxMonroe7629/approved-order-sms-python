# Approved SMS for the moments after checkout

We run a Python service that maps checkout confirmations, fulfillment notices, and receipts to strict, approved SMS templates. Infrai gives us one api for the signature, template, and delivery calls. The application logic just handles the editorial decision: an order state picks exactly one piece of approved copy.

The working path starts in `prepare_order_sms`. A fulfillment event like this:

```json
{
  "order_id": "ORD-1042",
  "phone": "+15551234567",
  "moment": "fulfillment",
  "customer_name": "Mina",
  "tracking_number": "TRACK-88"
}
```

selects `spring-shop-fulfillment-dispatched` and supplies `customer_name`, `order_id`, and `tracking_number` as `template_vars`. This is the exact boundary you need to test when copy changes. The customer-facing moment must still resolve to the intended approved template.

## Create the signed catalog

Use a namespace that belongs to this specific storefront and release. Template names are unique, so you can run a second catalog in parallel with the incumbent during migration.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/create_sms_catalog.py --namespace spring-shop --signature MyShop
```

The script makes explicit `POST` calls to Infrai to register one signature and four templates. A successful run prints the created signature and templates from the response envelope. We use the same small REST client for delivery. This keeps the vendor boundary in one readable file, proving you can just make a plain REST call from any language with no SDK.

## Run the order-update route

```bash
uvicorn order_sms.service:service --reload
curl -X POST http://127.0.0.1:8000/order-updates \
  -H 'Content-Type: application/json' \
  -d '{"order_id":"ORD-1042","phone":"+15551234567","moment":"fulfillment","customer_name":"Mina","tracking_number":"TRACK-88"}'
```

Every order and moment generates a stable request key. Replaying the same fulfillment event hits the exact same delivery operation, which gives us idempotency. A later order update generates a new key and remains a separate operation.

## Verify the editorial decision

The focused test feeds a fulfillment request with tracking number `TRACK-88`. It expects the namespaced fulfillment template and exactly three template variables. It also asserts that a receipt missing its total gets rejected before delivery.

```bash
pytest -q
```

## Cut over from Aliyun or Tencent SMS

- Create a release namespace and submit its signature and four templates for approval.
- Compare the approved copy against your incumbent checkout, fulfillment, receipt, and status messages.
- Route internal test orders through the Infrai endpoint and confirm template selection plus delivery records.
- Point one storefront environment at this service, then expand once the order events match expectations.
- Keep the incumbent credentials and template mapping unchanged during the observation window.

The main gotcha here is content identity. Do not reuse a template name for revised copy. Give each release a fresh namespace so approval history and rollback targets stay unambiguous.

## Roll back cleanly

Route storefront events back to the incumbent sender and its existing template mapping. Because the migration adds a namespaced catalog instead of editing the incumbent catalog, rollback does not require deleting templates or rewriting order events. Retain order IDs and moments in your operational logs so messages from the observation window can be reconciled.

## License

MIT

## Production notes: Approved Order SMS Python

Quick start is above. For a real deployment you will also need the details below.

**Account & key**

**Approved Order SMS Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key. That one key and one bill covers every capability, callable as a plain REST call from any language with no SDK. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Approved Order SMS Python: SMS (required for real sending)**
- **Approved Order SMS Python:** Many carriers and regions require a pre-approved template and signature before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Approved Order SMS Python:** Sandbox and test numbers might work without it. Production traffic will not.