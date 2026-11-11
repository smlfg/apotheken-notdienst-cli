"""Akzeptanztests für die drei Nutzer-Sitzungen aus docs/UX.md.

Die Tests starten das CLI als Subprozess in einem PTY gegen den Fake-Server
aus tests/harness. Sie dürfen vor dem Bau (Schritt S3) rot sein.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HARNESS = REPO / "tests" / "harness"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

from fake_server import FakeServer  # noqa: E402
from ux_session import PtySession, strip_ansi  # noqa: E402
from ux_spec import parse  # noqa: E402

HEUTE = "2026-11-11"
SPEC = parse(REPO / "docs" / "UX.md")


@pytest.fixture
def server():
    with FakeServer(SPEC, REPO) as fake:
        yield fake


def _env(fake: FakeServer, home: Path) -> dict[str, str]:
    for relative in (".config", ".cache", ".local/share", ".local/state"):
        (home / relative).mkdir(parents=True, exist_ok=True)
    pythonpath = [str(HARNESS), str(REPO)]
    src = REPO / "src"
    if src.is_dir():
        pythonpath.insert(0, str(src))
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "XDG_DATA_HOME": str(home / ".local" / "share"),
            "XDG_STATE_HOME": str(home / ".local" / "state"),
            "NOTDIENST_BASE_URL": fake.base_url,
            "NOTDIENST_HEUTE": HEUTE,
            "PYTHONPATH": os.pathsep.join(pythonpath),
            "PYTHONUNBUFFERED": "1",
            "ACCEPTANCE_SANDBOX": "1",
            "ACCEPTANCE_NET_LOG": str(home / "net.log"),
            "TERM": "xterm",
            "LANG": "C.UTF-8",
            "NO_COLOR": "1",
        }
    )
    return env


def _run(fake: FakeServer, home: Path, *args: str, timeout: float = 30.0):
    session = PtySession(
        [sys.executable, "-m", "notdienst", *args],
        env=_env(fake, home),
        cwd=REPO,
    )
    try:
        code = session.wait_exit(timeout)
        output = strip_ansi(session.transcript)
    finally:
        session.close()
    output = output.replace("\r\n", "\n").replace("\r", "\n")
    return code, output


def _assert_output(output: str, *expected: str) -> None:
    for line in expected:
        assert line in output, f"{line!r} fehlt in der Ausgabe:\n{output}"


def test_ux_session_1_jetzt_heilbronn(server, tmp_path):
    code, output = _run(server, tmp_path, "jetzt", "heilbronn")

    assert code == 0, output
    _assert_output(
        output,
        "Notdienst-Apotheken für heute (11.11.2026) in Heilbronn",
        "3 Treffer",
        "Apotheke im Staufenberg-Zentrum (3.22 km)",
        "Notdienst 11.11.2026 08:30 bis 12.11.2026 08:30",
        "Staufenbergstr. 31, 74081 Heilbronn",
        "Tel: +49 7131 899055",
    )
    assert any(
        request.path == "/notdienstsuche" and "heilbronn" in request.query.lower()
        for request in server.requests
    ), "keine Suchanfrage mit dem Ort heilbronn am Fake-Server"


def test_ux_session_2_datum_samstag(server, tmp_path):
    code, output = _run(server, tmp_path, "datum", "samstag", "74072")

    assert code == 0, output
    _assert_output(
        output,
        "Notdienst-Apotheken für Samstag, 14.11.2026 in 74072",
        "3 Treffer",
        "Harfensteller Apotheke Wollhaus (0.28 km)",
        "Notdienst 14.11.2026 08:30 bis 15.11.2026 08:30",
        "Am Wollhaus 4, 74072 Heilbronn",
        "Tel: +49 7131 991990",
    )
    assert any(
        request.path == "/notdienstsuche" and "2026-11-14" in request.query
        for request in server.requests
    ), "keine Suchanfrage mit dem Datum 2026-11-14 am Fake-Server"


def test_ux_session_3_standard_und_details(server, tmp_path):
    code, output = _run(server, tmp_path, "standard", "heilbronn")

    assert code == 0, output
    assert "Standard-Ort gespeichert: Heilbronn" in output
    configs = list(tmp_path.rglob("config.json"))
    assert configs, "keine Config-Datei unter HOME/XDG_CONFIG_HOME angelegt"
    assert any(
        stat.S_IMODE(config.stat().st_mode) == 0o600 for config in configs
    ), "Config-Datei hat nicht die Rechte 0600"

    code, output = _run(server, tmp_path, "details", "Greif")

    assert code == 0, output
    _assert_output(
        output,
        "Greif-Apotheke (8.01 km)",
        "Notdienst 11.11.2026 08:30 bis 12.11.2026 08:30",
        "Frankenweg 5, 74172 Neckarsulm",
        "Tel: +49 7132 83811",
    )
    assert any(
        request.path == "/notdienstsuche" and "heilbronn" in request.query.lower()
        for request in server.requests
    ), "details hat den Standard-Ort nicht für die Suche verwendet"


def test_keine_treffer_nennt_naechsten_schritt(server, tmp_path):
    code, output = _run(server, tmp_path, "jetzt", "Xyzzy123")

    assert code == 1, output
    assert "Keine Notdienst-Apotheke gefunden" in output
    assert "notdienst jetzt" in output
    assert "Traceback" not in output
