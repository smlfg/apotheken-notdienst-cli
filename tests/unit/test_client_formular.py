"""Unit-Test: die Formularseite wird innerhalb eines Laufs nur einmal geholt."""

from __future__ import annotations

from pathlib import Path

import httpx

from notdienst.client import Client

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures" / "ux"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_zweite_suche_verwendet_formular_erneut():
    aufrufe: list[httpx.Request] = []
    form = _fixture("notdienstsuche_form.html")
    jetzt = _fixture("suche_heilbronn_jetzt.html")

    def handler(request: httpx.Request) -> httpx.Response:
        aufrufe.append(request)
        if "tx_aponetpharmacy_search[search][plzort]" in request.url.params:
            return httpx.Response(200, text=jetzt)
        return httpx.Response(200, text=form)

    with Client(
        base_url="https://aponet.example.invalid",
        transport=httpx.MockTransport(handler),
        use_cache=False,
    ) as client:
        client.suche("Vorschlag")
        client.suche("Heilbronn")

    assert len(aufrufe) == 3
    assert sum(
        "tx_aponetpharmacy_search[search][plzort]" not in aufruf.url.params
        for aufruf in aufrufe
    ) == 1
