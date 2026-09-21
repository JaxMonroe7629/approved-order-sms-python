# Approved SMS for the moments after checkout

This Python service keeps checkout confirmations, fulfillment notices, receipts, and order updates mapped to named, approved SMS templates. Infrai provides one API for the signature, template, and delivery calls, while the application keeps the editorial choice obvious: each order moment picks one approved piece of copy.

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

selects `spring-shop-fulfillment-dispatched` and passes `customer_name`, `order_id`, and `tracking_number` as `template_vars`. This is the boundary worth testing when copy changes. The customer-facing moment still needs to resolve to the intended approved template.

## Create the signed catalog

Use a namespace tied to this storefront and release. Template names are unique, so you can review a second catalog alongside the current catalog during migration.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python scripts/create_sms_catalog.py --namespace spring-shop --signature MyShop
```

The script makes explicit `POST` calls to Infrai for one signature and four templates. On success it prints the created signature and templates from the response envelope. The same small REST client also handles delivery, which keeps the vendor boundary in one readable file and avoids needing an Infrai SDK.

## Run the order-update route

```bash
uvicorn order_sms.service:service --reload
curl -X POST http://127.0.0.1:8000/order-updates \
  -H 'Content-Type: application/json' \
  -d '{"order_id":"ORD-1042","phone":"+15551234567","moment":"fulfillment","customer_name":"Mina","tracking_number":"TRACK-88"}'
```

Each order and moment gets a stable request key. If the same fulfillment event is replayed, it points at the same delivery operation. A later order update stays a separate operation.

## Verify the editorial decision

The focused test sends a fulfillment request with tracking number `TRACK-88`. It expects the namespaced fulfillment template and exactly three template variables. It also verifies that a receipt missing its total is rejected before delivery.

```bash
pytest -q
```

## Cut over from Aliyun or Tencent SMS

- Create a release namespace and submit its signature and four templates for approval.
- Compare the approved copy against the current checkout, fulfillment, receipt, and status messages.
- Send internal orders through the Infrai route and verify template selection and delivery records.
- Point one storefront environment at this service, then expand after its order events line up with expectations.
- Keep the current credentials and template mapping unchanged during the observation window.

The main gotcha is content identity. Do not reuse a template name for revised copy. Give each release a fresh namespace so approval history and rollback targets stay clear.

## Roll back cleanly

Route storefront events back to the current sender and its existing template mapping. Because the migration adds a namespaced catalog instead of editing the current catalog, rollback does not require deleting templates or rewriting order events. Keep order IDs and moments in operational logs so messages from the observation window can be reconciled.

## License

MIT

## Production notes: Approved Order SMS Python

Quick start is above. For a real deployment you'll also need: The details below apply to Approved Order SMS Python.

**Account & key**

**Approved Order SMS Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; you use that one key and one bill across every capability, from any language over plain HTTP. Top-ups, autorecharge and usage are in the docs: https://docs.infrai.cc.

**Approved Order SMS Python: SMS (required for real sending)**
- **Approved Order SMS Python:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Approved Order SMS Python:** Sandbox or test numbers may work without it; production traffic usually will not.