from core import model_profiles


def test_model_profiles_catalog_exposes_hermes_style_providers(monkeypatch):
    monkeypatch.setattr(model_profiles.engine_router, "chatgpt_plus_available", lambda: True)
    monkeypatch.setattr(model_profiles.engine_router, "claude_code_available", lambda: False)
    monkeypatch.setattr(model_profiles, "local_endpoint_reachable", lambda url: False)

    catalog = model_profiles.catalog(["chatgpt_plus"])
    providers = {provider["id"]: provider for provider in catalog["providers"]}

    assert "openrouter" in providers
    assert "ollama" in providers
    assert "lmstudio" in providers
    assert providers["chatgpt_plus"]["status"] == "available"
    assert catalog["summary"]["providers"] >= 10


def test_choose_profile_prefers_local_for_austerity(monkeypatch):
    monkeypatch.setattr(model_profiles.engine_router, "available_engines", lambda **kwargs: ["chatgpt_plus", "ollama"])

    result = model_profiles.choose_profile("travaille hors ligne en local", ["chatgpt_plus", "ollama"])

    assert result["reason"] == "local_austerity"
    assert result["selected"]["engine"] == "ollama"


def test_remote_api_providers_are_blocked_by_zero_spend(monkeypatch):
    monkeypatch.setattr(model_profiles.config, "PAID_API_ENABLED", False)

    status = model_profiles.provider_status(
        next(provider for provider in model_profiles.PROVIDERS if provider.id == "openrouter")
    )

    assert status == "blocked_by_zero_spend"
