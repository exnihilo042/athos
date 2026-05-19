import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_voice_index_inline_javascript_is_valid(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node not installed")

    html = Path("voice/index.html").read_text("utf-8")
    scripts = [
        match.group(1)
        for match in re.finditer(r"<script[^>]*>(.*?)</script>", html, re.S | re.I)
        if match.group(1).strip()
    ]
    assert scripts

    for index, code in enumerate(scripts, start=1):
        script = tmp_path / f"index_inline_{index}.js"
        script.write_text(code, "utf-8")
        result = subprocess.run(
            [node, "--check", str(script)],
            capture_output=True,
            text=True,
            timeout=10,
            stdin=subprocess.DEVNULL,
        )
        assert result.returncode == 0, result.stderr
