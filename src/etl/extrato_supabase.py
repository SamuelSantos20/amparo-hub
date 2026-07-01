#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime, date, timedelta

import requests
import psycopg2
from psycopg2 import Error
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()  # carrega variáveis do arquivo .env

# CONFIGURAÇÃO via variáveis de ambiente
API_URL = os.getenv("API_URL", "http://177.69.231.91/agi_lab/app.php")
API_USER = os.getenv("API_USER")
API_PWD = os.getenv("API_PWD")
API_APP = os.getenv("API_APP", "extrato")
API_INTERVALO = os.getenv("API_INTERVALO", "0")
API_KEY_AGENTS = os.getenv("API_KEY_AGENTS", "")
API_KEY_QUEUES = os.getenv("API_KEY_QUEUES", "")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DB_NAME", "postgres"),
}

TABELA = "chamadas"
HTTP_TIMEOUT = 300


def validar_config():
    """Garante que as variáveis obrigatórias foram definidas no .env"""
    obrigatorias = {
        "API_USER": API_USER,
        "API_PWD": API_PWD,
        "DB_HOST": DB_CONFIG["host"],
        "DB_USER": DB_CONFIG["user"],
        "DB_PASSWORD": DB_CONFIG["password"],
    }
    faltando = [k for k, v in obrigatorias.items() if not v]
    if faltando:
        raise EnvironmentError(
            f"Variáveis de ambiente faltando: {', '.join(faltando)}. "
            f"Verifique seu arquivo .env (veja .env.example)."
        )


def get_conexao():
    return psycopg2.connect(**DB_CONFIG)


def validar_data_entrada(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Data inválida. Use o formato YYYY-MM-DD.")


def obter_data_inicial():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return validar_data_entrada(sys.argv[1].strip())
    # Padrão: dia anterior (recomendação da operadora de telefonia,
    # evita sobrecarga no servidor de origem)
    return date.today() - timedelta(days=1)


def gerar_datas(data_inicial, data_final):
    if data_inicial > data_final:
        raise ValueError("A data informada não pode ser futura.")

    datas = []
    data_atual = data_inicial
    while data_atual <= data_final:
        datas.append(data_atual)
        data_atual += timedelta(days=1)
    return datas


def montar_params_api(data_ref):
    return {
        "user": API_USER,
        "pwd": API_PWD,
        "app": API_APP,
        "end_date": data_ref.strftime("%Y-%m-%d"),
        "intervalo": API_INTERVALO,
        "key_agents": API_KEY_AGENTS,
        "key_queues": API_KEY_QUEUES,
    }


def baixar_api(sess, data_ref):
    params = montar_params_api(data_ref)
    response = sess.get(API_URL, params=params, timeout=HTTP_TIMEOUT)
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(f"Resposta da API fora do formato esperado para {data_ref}.")

    status = payload.get("status")
    if status not in (0, "0", None):
        raise ValueError(f"API retornou status inválido para {data_ref}: {status}")

    csv_data = payload.get("csv")
    if not isinstance(csv_data, dict):
        raise ValueError(f"Bloco 'csv' ausente ou inválido para {data_ref}.")

    return payload


def to_str(valor):
    if valor is None:
        return None
    return str(valor).strip()


def to_int(valor, default=0):
    if valor in (None, ""):
        return default
    try:
        return int(valor)
    except Exception:
        try:
            return int(float(str(valor).replace(",", ".")))
        except Exception:
            return default


def to_datetime_str(valor):
    if valor in (None, "", "null"):
        return None
    return str(valor).strip()


# Colunas na ordem exata da tabela (ver schema_chamadas_v2.sql)
COLUNAS = [
    "id", "protocolo", "callerid", "dt_up_cliente", "colaborador_up_cliente",
    "ramal_up_cliente", "date_evento", "event", "queue_id", "queue",
    "agent_id", "agent", "ringnoanswer", "completeagent", "completecaller",
    "transfer", "connect", "nota_avaliacao", "tabulacao_fila", "tme",
    "tma", "sla", "sla_p", "all_call", "all_esp", "max_esp",
]

UPSERT_SQL = f"""
INSERT INTO {TABELA} ({", ".join(COLUNAS)})
VALUES %s
ON CONFLICT (id) DO UPDATE SET
    {", ".join(f"{c} = EXCLUDED.{c}" for c in COLUNAS if c != "id")}
"""


def montar_linhas(payload):
    """Transforma o bloco 'csv' da API em uma lista de tuplas prontas para o execute_values."""
    registros = payload.get("csv", {})
    linhas = []

    for row_id, row in registros.items():
        if not isinstance(row, dict):
            continue

        protocolo = row.get("Protocolo ") or row.get("Protocolo")

        linhas.append((
            to_str(row_id),
            to_str(protocolo),
            to_str(row.get("callerid")),
            to_datetime_str(row.get("dt_up_Cliente")),
            to_str(row.get("colaborador_up_Cliente")),
            to_str(row.get("ramal_up_Cliente")),
            to_datetime_str(row.get("date")),
            to_str(row.get("event")),
            to_str(row.get("queue_id")),
            to_str(row.get("queue")),
            to_str(row.get("agent_id")),
            to_str(row.get("agent")),
            to_int(row.get("RINGNOANSWER")),
            to_int(row.get("COMPLETEAGENT")),
            to_int(row.get("COMPLETECALLER")),
            to_int(row.get("TRANSFER")),
            to_int(row.get("CONNECT")),
            to_str(row.get("nota_avaliacao")),
            to_str(row.get("tabulacao_fila")),
            to_str(row.get("TME")),
            to_str(row.get("TMA")),
            to_str(row.get("SLA")),
            to_str(row.get("SLA-P")),
            to_str(row.get("all_call")),
            to_str(row.get("all_esp")),
            to_str(row.get("max_esp")),
        ))

    return linhas


def salvar_registros(cursor, payload):
    linhas = montar_linhas(payload)
    if not linhas:
        return 0
    execute_values(cursor, UPSERT_SQL, linhas)
    return len(linhas)


def processar_data(sess, conn, cursor, data_ref):
    print(f"Processando {data_ref.strftime('%Y-%m-%d')} ...")
    payload = baixar_api(sess, data_ref)
    total_csv = len(payload.get("csv", {}))
    total_salvo = salvar_registros(cursor, payload)
    conn.commit()
    print(f"Data {data_ref.strftime('%Y-%m-%d')}: csv={total_csv} gravados={total_salvo}")
    return total_salvo


def main():
    conn = None
    sess = None

    try:
        validar_config()

        data_inicial = obter_data_inicial()
        data_final = date.today() - timedelta(days=1)  # nunca processa o dia corrente
        datas = gerar_datas(data_inicial, data_final)

        print(f"Período de execução: {datas[0].strftime('%Y-%m-%d')} até {datas[-1].strftime('%Y-%m-%d')}")
        print(f"Total de datas: {len(datas)}")

        conn = get_conexao()
        cursor = conn.cursor()

        sess = requests.Session()

        total_geral = 0

        for data_ref in datas:
            try:
                total_geral += processar_data(sess, conn, cursor, data_ref)
            except Exception as e:
                conn.rollback()
                print(f"Erro ao processar {data_ref.strftime('%Y-%m-%d')}: {e}")

        print(f"Concluído. Total geral processado: {total_geral}")

    except requests.HTTPError as e:
        print(f"Erro HTTP: {e}")
    except requests.RequestException as e:
        print(f"Erro de conexão com API: {e}")
    except Error as e:
        if conn:
            conn.rollback()
        print(f"Erro PostgreSQL: {e}")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro geral: {e}")
    finally:
        if conn:
            conn.close()
        if sess:
            sess.close()


if __name__ == "__main__":
    main()
