"""Unit-Tests für den HTTP-Client ohne echtes Netz."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from notdienst.client import Client
from notdienst.errors import InputError, ParseError, SourceError

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures" / "ux"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _transport(aufrufe: list[httpx.Request], *, status: int = 200):
    form = _fixture("notdienstsuche_form.html")
    jetzt = _fixture("suche_heilbronn_jetzt.html")

    def handler(request: httpx.Request) -> httpx.Response:
        aufrufe.append(request)
        if request.method != "GET":
            return httpx.Response(405, text="method not allowed")
        params = request.url.params
        if "tx_aponetpharmacy_search[search][plzort]" in params:
            return httpx.Response(status, text=jetzt)
        return httpx.Response(200, text=form)

    return httpx.MockTransport(handler)


def test_suche_liest_formular_und_suchseite_und_parst_treffer():
    aufrufe: list[httpx.Request] = []
    with Client(
        base_url="https://aponet.example.invalid",
        transport=_transport(aufrufe),
        use_cache=False,
    ) as client:
        ergebnis = client.suche(
            "Heilbronn", datum=None, strasse=None, radius=5
        )

    assert len(aufrufe) == 2
    assert all(aufruf.method == "GET" for aufruf in aufrufe)
    assert aufrufe[0].url.path == "/notdienstsuche"
    assert len(ergebnis.treffer) == 3
    assert ergebnis.radius_km == 25

    such_params = aufrufe[1].url.params
    assert such_params["tx_aponetpharmacy_search[search][plzort]"] == "heilbronn"
    assert such_params["tx_aponetpharmacy_search[search][radius]"] == "5"
    assert such_params["tx_aponetpharmacy_search[search][date]"] == ""
    assert "cHash" in such_params


def test_suche_sendet_datum_und_strasse():
    aufrufe: list[httpx.Request] = []
    with Client(
        base_url="https://aponet.example.invalid",
        transport=_transport(aufrufe),
        use_cache=False,
    ) as client:
        client.suche(
            "74072",
            datum="2026-11-14",
            strasse="Wollhaus",
            radius=10,
        )

    params = aufrufe[1].url.params
    assert params["tx_aponetpharmacy_search[search][date]"] == "2026-11-14"
    assert params["tx_aponetpharmacy_search[search][street]"] == "Wollhaus"
    assert params["tx_aponetpharmacy_search[search][radius]"] == "10"


def test_http_fehler_ist_quellfehler():
    aufrufe: list[httpx.Request] = []
    with Client(
        base_url="https://aponet.example.invalid",
        transport=_transport(aufrufe, status=503),
        use_cache=False,
    ) as client:
        with pytest.raises(SourceError) as fehler:
            client.suche("Heilbronn")
    assert fehler.value.exit_code == 3


def test_fehlende_chash_ist_quellfehler():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>kein Formular</body></html>")

    with Client(
        base_url="https://aponet.example.invalid",
        transport=httpx.MockTransport(handler),
        use_cache=False,
    ) as client:
        with pytest.raises(ParseError) as fehler:
            client.suche("Heilbronn")
    assert fehler.value.exit_code == 3


@pytest.mark.parametrize(
    "wert",
    [
        "keine-url",
        "ftp://example.invalid",
        "http://",
        "http://host:abc",
        "http://host:70000",
        "http://[::1",
    ],
)
def test_ungueltige_basis_url_ist_eingabefehler(monkeypatch, wert):
    monkeypatch.setenv("NOTDIENST_BASE_URL", wert)
    with pytest.raises(InputError) as fehler:
        Client()
    assert fehler.value.exit_code == 2
    assert fehler.value.naechster_schritt


def test_leere_basis_url_nutzt_standard(monkeypatch):
    monkeypatch.setenv("NOTDIENST_BASE_URL", "")
    assert Client().base_url == "https://www.aponet.de"


def test_nicht_erreichbar_ist_quellfehler_mit_naechstem_schritt():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("kaputt", request=request)

    with Client(
        base_url="https://aponet.example.invalid",
        transport=httpx.MockTransport(handler),
        use_cache=False,
    ) as client:
        with pytest.raises(SourceError) as fehler:
            client.suche("Heilbronn")
    assert fehler.value.exit_code == 3
    assert "Netzverbindung" in fehler.value.naechster_schritt
