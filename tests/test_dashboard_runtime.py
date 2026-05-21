import importlib
import json
import os
import sys
import threading
import urllib.error
import urllib.request


def _load_server(tmp_path, monkeypatch):
    monkeypatch.setenv("DRIVE_PATH", str(tmp_path))
    monkeypatch.setenv("ATHOS_PATH", str(tmp_path))
    monkeypatch.setenv("ATHOS_BIND_HOST", "127.0.0.1")
    monkeypatch.setenv("ATHOS_ROOM_AUTO_RESPOND", "false")
    monkeypatch.setenv("ATHOS_ROOM_AUTO_WORK", "false")
    monkeypatch.delenv("ATHOS_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ATHOS_REQUIRE_TOKEN", raising=False)
    root = os.getcwd()
    voice_path = os.path.join(root, "voice")
    core_path = os.path.join(root, "core")
    for path in (voice_path, core_path):
        if path not in sys.path:
            sys.path.insert(0, path)
    for name in (
        "config",
        "session_kernel",
        "sync_manager",
        "task_queue",
        "session_compactor",
        "athos_room",
        "attach_protocol",
        "dashboard_runtime",
        "project_registry",
        "autonomous_loop",
        "server",
    ):
        sys.modules.pop(name, None)
    import voice.server as server
    importlib.reload(server)
    server.config.ATHOS_TOKEN_ENFORCED = False
    server.ACCESS_TOKEN = ""
    server.athos_room._ROOM_FILE = tmp_path / "athos_conversation.jsonl"
    server.athos_room._DRIVE_MIRROR = tmp_path / "drive" / "athos_conversation.jsonl"
    server.session_kernel.SESSION_FILE = tmp_path / "athos_session_kernel.jsonl"
    server.sync_manager.OUTBOX_FILE = tmp_path / "athos_sync_outbox.jsonl"
    server.task_queue.TASK_QUEUE_FILE = tmp_path / "athos_task_queue.json"
    server.session_compactor.SUMMARY_FILE = tmp_path / "athos_session_summary.mem"
    import attach_protocol
    attach_protocol.athos_room._ROOM_FILE = server.athos_room._ROOM_FILE
    attach_protocol.athos_room._DRIVE_MIRROR = server.athos_room._DRIVE_MIRROR
    attach_protocol.session_kernel.SESSION_FILE = server.session_kernel.SESSION_FILE
    return server


class _RunningServer:
    def __init__(self, server_module):
        self.httpd = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def post(self, path, body):
        req = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def post_raw(self, path, body_bytes):
        req = urllib.request.Request(
            self.base + path,
            data=body_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)


def _server(tmp_path, monkeypatch):
    module = _load_server(tmp_path, monkeypatch)
    running = _RunningServer(module)
    return module, running


def test_projects_endpoints_support_mem_create_update_and_detail(tmp_path, monkeypatch):
    (tmp_path / "athos_projects.mem").write_text(
        "\n".join(
            [
                "§proj:athos|status:building|priority:0",
                "§proj:rouge-pivoine|status:active|priority:5|store:rouge-pivoine.myshopify.com|repo:rouge-pivoine-theme|next:Livrer_V2",
                "§proj:placerr|status:active|priority:1|stack:Next.js(web/)+Pixi.js|blocker:attente_design",
            ]
        ),
        encoding="utf-8",
    )
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/projects", {})
        assert status == 200
        assert body["ok"] is True
        assert body["summary"]["total"] == 3
        by_id = {project["id"]: project for project in body["projects"]}
        assert by_id["rouge-pivoine"]["name"] == "Rouge Pivoine"
        assert by_id["rouge-pivoine"]["store"] == "rouge-pivoine.myshopify.com"
        assert by_id["placerr"]["blocker"] == "attente_design"
        assert by_id["placerr"]["health_score"] < by_id["rouge-pivoine"]["health_score"]

        status, body = srv.post("/api/projects/detail", {"project_id": "rouge-pivoine"})
        assert status == 200
        assert body["ok"] is True
        assert body["project"]["id"] == "rouge-pivoine"
        assert "rouge-pivoine.myshopify.com" in body["project"]["domains"]

        status, body = srv.post("/api/projects/detail", {"project_id": "inconnu"})
        assert status == 404
        assert body["error"] == "project_not_found"

        status, body = srv.post("/api/projects/create", {
            "project": {
                "name": "Nom Projet++",
                "type": "internal",
                "description": "Projet interne",
                "priority": "P2",
                "status": "active",
                "domains": [],
                "repositories": [],
                "integrations": [],
                "social_channels": [],
                "goals": [],
                "agents": [],
            }
        })
        assert status == 200
        assert body["ok"] is True
        assert body["project_id"] == "nom-projet"
        assert body["storage"]["path"] == "memory/athos_project_registry.json"
        assert (tmp_path / "athos_project_registry.json").exists()

        status, body = srv.post("/api/projects/create", {"project": {"name": "Nom Projet++"}})
        assert status == 409
        assert body["error"] == "project_already_exists"

        status, body = srv.post("/api/projects/update", {
            "project_id": "rouge-pivoine",
            "patch": {"status": "paused", "priority": "P1", "next_action": "Reprendre bientôt"},
        })
        assert status == 200
        assert body["ok"] is True
        assert body["project"]["status"] == "paused"
        assert body["project"]["priority"] == "1"
        assert body["project"]["next_action"] == "Reprendre bientôt"

        status, body = srv.post("/api/projects/update", {
            "project_id": "nom-projet",
            "patch": {"domains": ["ex-nihilo.agency"], "agents": ["seo", "dev"]},
        })
        assert status == 200
        assert body["project"]["domains"] == ["ex-nihilo.agency"]
        assert body["project"]["agents"] == ["seo", "dev"]
    finally:
        srv.close()


def test_projects_endpoints_validate_payloads(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/projects/create", {"project": {"type": "internal"}})
        assert status == 400
        assert body["error"] == "name_required"

        status, body = srv.post("/api/projects/create", {"project": {"name": "Bad", "domains": "oops"}})
        assert status == 400
        assert body["error"] == "invalid_array_field"

        status, body = srv.post("/api/projects/update", {"project_id": "athos", "patch": {"secret": "nope"}})
        assert status == 400
        assert body["error"] == "forbidden_patch_field"

        status, body = srv.post_raw("/api/projects/create", b"{")
        assert status == 400
        assert body["error"] == "invalid_json"
    finally:
        srv.close()


def test_finances_endpoint_returns_partial_payload_without_sources(tmp_path, monkeypatch):
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/finances", {})
        assert status == 200
        assert body["ok"] is True
        assert body["summary"]["currency"] == "EUR"
        assert body["summary"]["revenue_gross"] is None
        assert body["capabilities"]["stripe_configured"] is False
        assert body["capabilities"]["shopify_configured"] is False
        assert body["data_quality"] == "partial"
    finally:
        srv.close()


def test_seo_endpoint_derives_sites_from_project_memory(tmp_path, monkeypatch):
    (tmp_path / "athos_projects.mem").write_text(
        "\n".join(
            [
                "§proj:athos|status:building",
                "§proj:olivia|status:active|store:ex-nihilo-agency.myshopify.com",
                "§proj:rouge-pivoine|status:active|domain:cbdpascher14.fr",
            ]
        ),
        encoding="utf-8",
    )
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/seo", {})
        assert status == 200
        assert body["ok"] is True
        assert body["data_quality"] == "partial"
        assert {site["id"] for site in body["sites"]} == {"olivia", "rouge-pivoine"}
        assert all(site["metrics"]["avg_position"] is None for site in body["sites"])
    finally:
        srv.close()


def test_commandes_endpoint_handles_empty_sources_and_invalid_limit(tmp_path, monkeypatch):
    (tmp_path / "athos_projects.mem").write_text("§proj:athos|status:building\n", encoding="utf-8")
    _, srv = _server(tmp_path, monkeypatch)
    try:
        status, body = srv.post("/api/commandes", {"limit": 50, "project_id": "unknown"})
        assert status == 200
        assert body["ok"] is True
        assert body["orders"] == []
        assert body["data_quality"] == "empty_no_source"

        status, body = srv.post("/api/commandes", {"limit": 999})
        assert status == 400
        assert body["error"] == "invalid_limit"
    finally:
        srv.close()


def test_skills_registry_availability_and_recommendations_are_stable(tmp_path, monkeypatch):
    module, srv = _server(tmp_path, monkeypatch)
    module.dashboard_runtime._responder_status = lambda: {
        "actors": {
            "claude": {"available": True, "last_problem": {}},
            "codex": {"available": False, "last_problem": {"kind": "usage_limit", "detail": "quota"}},
        }
    }
    try:
        status, body = srv.post("/api/skills/registry", {})
        assert status == 200
        assert body["ok"] is True
        assert body["summary"]["total"] == len(module.dashboard_runtime.CODEX_SKILL_REGISTRY)
        assert body["summary"]["codex"] >= 1
        assert any(skill["id"] == "codex-api-and-interface-design" for skill in body["skills"])

        status, body = srv.post("/api/skills/engine-availability", {})
        assert status == 200
        assert body["engines"]["claude"]["available"] is True
        assert body["engines"]["codex"]["available"] is False
        assert body["engines"]["codex"]["reason"] == "usage_limit"

        status, body = srv.post("/api/skills/recommend", {"context": {"page": "dashboard/automations", "task": "frontend QA", "phase": "QA"}})
        assert status == 200
        assert body["ok"] is True
        assert body["mode"] == "static_rules"
        assert body["recommendations"][0]["human_approval_required"] is True

        status, body = srv.post("/api/skills/recommend", {"context": "bad"})
        assert status == 400
        assert body["error"] == "invalid_context"
    finally:
        srv.close()
