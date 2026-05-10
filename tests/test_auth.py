from core.auth import request_authorized


class Headers(dict):
    def get(self, key, default=None):
        return super().get(key, default)


def test_request_authorized_allows_when_token_not_configured():
    assert request_authorized(Headers(), "") is True


def test_request_authorized_accepts_bearer_or_athos_header():
    assert request_authorized(Headers({"Authorization": "Bearer secret"}), "secret") is True
    assert request_authorized(Headers({"X-Athos-Token": "secret"}), "secret") is True


def test_request_authorized_rejects_missing_or_wrong_token():
    assert request_authorized(Headers(), "secret") is False
    assert request_authorized(Headers({"Authorization": "Bearer wrong"}), "secret") is False
