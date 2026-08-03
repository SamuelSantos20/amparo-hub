from datetime import date

import pytest

from src.etl.extrato_supabase import gerar_datas, montar_linhas, validar_data_entrada


def test_validar_data_entrada():
    assert validar_data_entrada("2026-07-01") == date(2026, 7, 1)


def test_validar_data_entrada_rejeita_formato_invalido():
    with pytest.raises(ValueError):
        validar_data_entrada("01/07/2026")


def test_gerar_datas_inclui_inicio_e_fim():
    assert gerar_datas(date(2026, 7, 1), date(2026, 7, 3)) == [
        date(2026, 7, 1),
        date(2026, 7, 2),
        date(2026, 7, 3),
    ]


def test_montar_linhas_normaliza_payload():
    payload = {
        "status": 0,
        "csv": {
            "evento-1": {
                "Protocolo": "PROTOCOLO-DEMO",
                "callerid": "+5500000000000",
                "date": "2026-07-01 10:00:00",
                "event": "COMPLETEAGENT",
                "RINGNOANSWER": "0",
                "COMPLETEAGENT": "1",
                "COMPLETECALLER": "0",
                "TRANSFER": "0",
                "CONNECT": "1",
            }
        },
    }

    linhas = montar_linhas(payload)

    assert len(linhas) == 1
    assert linhas[0][0] == "evento-1"
    assert linhas[0][1] == "PROTOCOLO-DEMO"
    assert linhas[0][2] == "+5500000000000"
    assert linhas[0][13] == 1
