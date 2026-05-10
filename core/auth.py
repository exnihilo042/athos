"""Authentication helpers for Athos HTTP APIs."""


def request_authorized(headers, access_token: str) -> bool:
    token = (access_token or "").strip()
    if not token:
        return True
    auth = headers.get("Authorization", "")
    return auth == f"Bearer {token}" or headers.get("X-Athos-Token", "") == token
