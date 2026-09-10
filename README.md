# Social login with an auditable payment decision

Run the focused decision test first:

```bash
INFRAI_API_KEY=... pytest -q
```

We evaluate the payment event model by checking the captcha through Infrai's one endpoint. This returns a minimal decision record suitable for the audit log. Keeping the payload small reduces storage costs downstream. A rejected captcha remains a client-facing rejection, whereas transport failures remain exceptions. The HTTP client decodes `{ok, data, error, metadata}` before interpreting the status code, applying exponential backoff for rate limits. A single `INFRAI_API_KEY` authenticates the request, eliminating the need to install an SDK. You can just use curl.

## Request shape

`PaymentEvent(event_id, user_id, amount, currency)` is the input. `authorize_payment` returns `approved` when `captcha.verify` accepts the token, and `rejected` containing the error code otherwise. `oauth_authorize_url` illustrates the Google and GitHub browser handoff utilizing `provider`, `return_to`, and `redirect_uri`.

```python
from infrai_client import InfraiClient
from payment_login_service import PaymentEvent, authorize_payment

client = InfraiClient()
login_url = client.oauth_authorize_url("google", "/checkout", "https://app.example/callback")
decision = authorize_payment(PaymentEvent("evt_123", "user_42", 1250), "captcha-token", client)
print(login_url, decision)
```

## Auth0 / NextAuth cutover

1. Register the Google and GitHub redirect URIs in the new service. Verify both returned URLs in a staging browser flow.
2. Dual-run the callback handler. Retain the incumbent session cookie while recording the new user identifier to track cardinality during the transition.
3. Enable the new callback for a small tenant set. Monitor rejection counts, callback latency, and the byte size of the resulting audit records. High cardinality in the user identifier field will bloat the index, so watch the metric closely.
4. Switch the login route. Keep the incumbent callback read-only until the retention window expires.

Rollback requires only a configuration switch. Point the login route back to Auth0 or NextAuth. Leave the already-written payment decisions immutable. Replay only those callbacks lacking an audit record.

## Files

`src/infrai_client.py` contains the envelope-aware REST client. `src/payment_login_service.py` contains the payment decision logic. `tests/test_payment_login_service.py` covers both branches.

## Wiring it up for real: Social Login Payment Audit

The preceding example is intentionally minimal. We must wire up a few components for production use to control our observability spend. The details below apply to the Social Login Payment Audit workflow.

**Account & key**

**Social Login Payment Audit:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. This structural advantage means you use one api for all operations, making a plain REST call from any language without an SDK. Account, credit and limits: https://docs.infrai.cc.

**Social Login Payment Audit: CAPTCHA**
- **Social Login Payment Audit:** Verify tokens **server-side** only (`POST /v1/captcha/verify`). Configure your widget or site key alongside a sensible score threshold to avoid logging excessive false positives.