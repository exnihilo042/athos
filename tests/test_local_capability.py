from core import local_capability


def test_local_capability_scan_is_network_free_and_compensates_llm_limits(tmp_path, monkeypatch):
    monkeypatch.setattr(local_capability.config, "ATHOS_PATH", tmp_path)
    monkeypatch.setattr(local_capability.config, "DRIVE", tmp_path / "memory")
    monkeypatch.setattr(
        local_capability.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"python3", "git", "rg"} else None,
    )

    data = local_capability.scan()

    assert data["network_required"] is False
    assert data["available_tool_count"] == 3
    assert "compensate_llm_scope_rigidity_with_authorized_local_memory_tools_and_protocols" in data["capabilities_without_network"]
    assert any("engine limits" in item for item in data["anti_rigidity_policy"])


def test_austerity_pack_keeps_physical_world_as_amplifier_not_prerequisite(monkeypatch):
    monkeypatch.setattr(local_capability, "scan", lambda: {"network_required": False})

    pack = local_capability.austerity_pack("hors réseau, sans rien, reste capable")

    assert pack["base"] == "capability_under_resource_austerity"
    assert "compensates engine rigidity" in pack["principle"]
    assert pack["physical_world_position"] == "devices, sensors and hardware are accelerators, not prerequisites"
    assert "inventory_available_local_resources" in pack["action_loop"]
