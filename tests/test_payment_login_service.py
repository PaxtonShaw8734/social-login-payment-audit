from payment_login_service import PaymentEvent, authorize_payment
from infrai_client import InfraiError


class CaptchaRejected:
    def verify_captcha(self, token, action):
        raise InfraiError("CAPTCHA_SCORE_TOO_LOW", {"code": "CAPTCHA_SCORE_TOO_LOW"}, 422)


class CaptchaAccepted:
    def verify_captcha(self, token, action):
        return {"ok": True, "data": {}}


def test_rejected_captcha_is_a_payment_decision():
    event = PaymentEvent("evt_123", "user_42", 1250)
    result = authorize_payment(event, "captcha-token", CaptchaRejected())
    assert result == {"event_id": "evt_123", "decision": "rejected", "reason": "CAPTCHA_SCORE_TOO_LOW"}


def test_verified_captcha_approves_payment():
    result = authorize_payment(PaymentEvent("evt_124", "user_42", 1250), "ok", CaptchaAccepted())
    assert result["decision"] == "approved"
