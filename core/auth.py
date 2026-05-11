"""Authentication helpers for Athos HTTP APIs."""


def request_authorized(headers, access_token: str, require_token: bool = False) -> bool:
    token = (access_token or "").strip()
    if not token:
        return not require_token
    auth = headers.get("Authorization", "")
    return auth == f"Bearer {token}" or headers.get("X-Athos-Token", "") == token
