from core.auth import request_authorized


class Headers(dict):
    def get(self, key, default=None):
        return super().get(key, default)


def test_request_authorized_allows_when_token_not_configured():
    assert request_authorized(Headers(), "") is True


def test_request_authorized_can_require_token_even_if_missing():
    assert request_authorized(Headers(), "", require_token=True) is False


def test_request_authorized_accepts_bearer_or_athos_header():
    assert request_authorized(Headers({"Authorization": "Bearer secret"}), "secret", require_token=True) is True
    assert request_authorized(Headers({"X-Athos-Token": "secret"}), "secret", require_token=True) is True


def test_request_authorized_rejects_missing_or_wrong_token():
    assert request_authorized(Headers(), "secret", require_token=True) is False
    assert request_authorized(Headers({"Authorization": "Bearer wrong"}), "secret", require_token=True) is False
