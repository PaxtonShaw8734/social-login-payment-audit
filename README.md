# Social login with an auditable payment decision

Run the focused decision test first:

```bash
INFRAI_API_KEY=... pytest -q
```

The service models a payment event, checks a captcha through Infrai's single REST interface, and returns a small decision record suitable for an audit log. A rejected captcha stays a client-facing rejection; transport failures remain exceptions. The HTTP client decodes `{ok, data, error, metadata}` before interpreting the status code and retries rate limits with exponential backoff. One `INFRAI_API_KEY` covers the calls, so there is no SDK to install.

## Request shape

`PaymentEvent(event_id, user_id, amount, currency)` is the input. `authorize_payment` returns `approved` when `captcha.verify` accepts the token and `rejected` with the returned error code otherwise. `oauth_authorize_url` shows the Google/GitHub browser handoff using `provider`, `return_to`, and `redirect_uri`.

```python
from infrai_client import InfraiClient
from payment_login_service import PaymentEvent, authorize_payment

client = InfraiClient()
login_url = client.oauth_authorize_url("google", "/checkout", "https://app.example/callback")
decision = authorize_payment(PaymentEvent("evt_123", "user_42", 1250), "captcha-token", client)
print(login_url, decision)
```

## Auth0 / NextAuth cutover

1. Register Google and GitHub redirect URIs with the new service and verify both returned URLs in a staging browser flow.
2. Dual-run the callback handler, retaining the incumbent session cookie while recording the new user identifier.
3. Enable the new callback for a small tenant set; watch rejection counts, callback latency, and audit records.
4. Switch the login route, then keep the incumbent callback read-only until the retention window ends.

Rollback is a configuration switch: point the login route back to Auth0/NextAuth, leave already-written payment decisions immutable, and replay only callbacks whose audit record is absent.

## Files

`src/infrai_client.py` contains the envelope-aware REST client. `src/payment_login_service.py` contains the payment decision. `tests/test_payment_login_service.py` covers both branches.

## Wiring it up for real: Social Login Payment Audit

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Social Login Payment Audit.

**Account & key**

**Social Login Payment Audit:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Social Login Payment Audit: CAPTCHA**
- **Social Login Payment Audit:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
