"""Unit-Tests für den CLI-Rand: Hilfe, Fehlervertrag, Config."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _env(tmp_path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path),
            "XDG_CONFIG_HOME": str(tmp_path / ".config"),
            "XDG_CACHE_HOME": str(tmp_path / ".cache"),
            "PYTHONPATH": os.path.join(REPO, "src"),
            "NOTDIENST_HEUTE": "2026-11-11",
        }
    )
    env.pop("NOTDIENST_BASE_URL", None)
    return env


def _run(tmp_path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "notdienst", *args],
        capture_output=True,
        text=True,
        env=_env(tmp_path),
        cwd=REPO,
        timeout=30,
    )


def test_version_und_help_exit_null(tmp_path):
    for flag in ("--version", "--help"):
        ergebnis = _run(tmp_path, flag)
        assert ergebnis.returncode == 0, ergebnis.stderr
        assert "notdienst" in ergebnis.stdout.lower()
        assert "Traceback" not in ergebnis.stderr


def test_unbekanntes_unterkommando_ist_json_fehler(tmp_path):
    ergebnis = _run(tmp_path, "quatsch")
    assert ergebnis.returncode == 2
    daten = json.loads(ergebnis.stdout)
    assert daten["fehler"]["exit_code"] == 2
    assert daten["fehler"]["naechster_schritt"]
    assert "Traceback" not in ergebnis.stderr


def test_ungueltiges_datum_ist_json_fehler_ohne_netz(tmp_path):
    ergebnis = _run(tmp_path, "datum", "quatsch", "heilbronn")
    assert ergebnis.returncode == 2
    daten = json.loads(ergebnis.stdout)
    assert "Ungültiges Datum" in daten["fehler"]["meldung"]


def test_standard_ohne_config_ist_fehler(tmp_path):
    ergebnis = _run(tmp_path, "standard")
    assert ergebnis.returncode == 1
    daten = json.loads(ergebnis.stdout)
    assert daten["fehler"]["exit_code"] == 1
    assert "notdienst standard" in daten["fehler"]["naechster_schritt"]


def test_standard_speichert_config_mit_0600(tmp_path):
    ergebnis = _run(tmp_path, "standard", "heilbronn")
    assert ergebnis.returncode == 0, ergebnis.stderr
    daten = json.loads(ergebnis.stdout)
    assert daten["standard_ort"] == "Heilbronn"
    config = tmp_path / ".config" / "apotheken-notdienst-cli" / "config.json"
    assert config.is_file()
    assert stat.S_IMODE(config.stat().st_mode) == 0o600
    assert json.loads(config.read_text(encoding="utf-8"))["standard_ort"] == "Heilbronn"

    ergebnis = _run(tmp_path, "standard")
    assert ergebnis.returncode == 0
    assert json.loads(ergebnis.stdout)["standard_ort"] == "Heilbronn"


class _FakeClient:
    def __init__(self):
        self.aufrufe: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def suche(self, ort, *, datum=None, strasse=None, radius=5):
        from notdienst.models import Suchergebnis, Treffer

        self.aufrufe.append(ort)
        if ort.lower() == "vorschlag":
            return Suchergebnis(
                vorschlaege=[
                    "74388 Talheim Rauher Stich",
                    "91555 Feuchtwangen Heilbronn",
                ]
            )
        return Suchergebnis(
            treffer=[Treffer(name="Gewaehlte-Apotheke", entfernung_km=1.0)],
            radius_km=25,
            trefferblock=True,
        )


def test_erster_nutzt_aufgeloesten_ort_im_json(monkeypatch, capsys):
    fake = _FakeClient()
    monkeypatch.setattr("notdienst.cli.Client", lambda: fake)

    code = cli_main(monkeypatch, ["jetzt", "vorschlag", "--erster", "--json"])

    assert code == 0
    daten = json.loads(capsys.readouterr().out)
    assert daten["abfrage"]["ort"] == "74388 Talheim Rauher Stich"
    assert fake.aufrufe == ["Vorschlag", "74388 Talheim Rauher Stich"]


def test_erster_nutzt_aufgeloesten_ort_in_kopfzeile(monkeypatch, capsys):
    fake = _FakeClient()
    monkeypatch.setattr("notdienst.cli.Client", lambda: fake)
    monkeypatch.setattr("notdienst.cli._will_json", lambda argv: False)

    code = cli_main(monkeypatch, ["jetzt", "vorschlag", "--erster"])

    assert code == 0
    ausgabe = capsys.readouterr().out
    assert "in 74388 Talheim Rauher Stich" in ausgabe


def cli_main(monkeypatch, argv):
    from notdienst import cli

    monkeypatch.setenv("NOTDIENST_HEUTE", "2026-11-11")
    return cli.main(argv)


def test_strg_c_und_eof_ohne_traceback(monkeypatch, capsys):
    from notdienst import cli

    def _abbruch(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "_suche_ausfuehren", _abbruch)
    assert cli.main(["jetzt", "heilbronn"]) == 130
    ausgabe = capsys.readouterr()
    assert "Traceback" not in ausgabe.err

    def _eof(*args, **kwargs):
        raise EOFError

    monkeypatch.setattr(cli, "_suche_ausfuehren", _eof)
    assert cli.main(["jetzt", "heilbronn"]) == 130
    ausgabe = capsys.readouterr()
    assert "Traceback" not in ausgabe.err
