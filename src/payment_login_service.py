from dataclasses import dataclass
from typing import Dict

from infrai_client import InfraiClient, InfraiError


@dataclass
class PaymentEvent:
    event_id: str
    user_id: str
    amount: int
    currency: str = "USD"


def authorize_payment(event: PaymentEvent, captcha_token: str, client: InfraiClient) -> Dict[str, str]:
    """Return an audit-friendly decision for a social-login payment."""
    try:
        client.verify_captcha(captcha_token, "payment_authorize")
    except InfraiError as exc:
        if 400 <= exc.status < 500:
            return {"event_id": event.event_id, "decision": "rejected", "reason": exc.code}
        raise
    return {"event_id": event.event_id, "decision": "approved", "reason": "captcha_verified"}
