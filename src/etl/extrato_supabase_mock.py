#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import random
from datetime import datetime, date, timedelta

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

# CONFIGURAÇÃO DO BANCO
DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "port":     os.getenv("DB_PORT", "5432"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname":   os.getenv("DB_NAME", "postgres"),
}

TABELA = "chamadas"

# DADOS FICTÍCIOS PARA SIMULAR A API
FILAS = {
    "1": "Suporte Técnico",
    "2": "Vendas",
    "3": "Reboque",
    "4": "Financeiro",
    "5": "Qualidade",
}

AGENTES = {
    "101": "Carlos Silva",
    "102": "Ana Souza",
    "103": "Pedro Lima",
    "104": "Juliana Costa",
    "105": "Marcos Oliveira",
    "106": "Fernanda Santos",
    "107": "Ricardo Alves",
    "108": "Patrícia Rocha",
}

EVENTOS = ["COMPLETEAGENT", "COMPLETECALLER", "RINGNOANSWER", "TRANSFER"]
TABULACOES = ["Resolvido", "Callback", "Transferido", "Sem Solução", "Erro Operacional"]


def gera_numero():
    return f"+55119{random.randint(10000000, 99999999)}"


def gera_tempo(min_s, max_s):
    s = random.randint(min_s, max_s)
    return f"{s // 60:02d}:{s % 60:02d}"


def simular_api(data_ref):
    """
    Simula a resposta da API de telefonia.
    Retorna um dicionário no mesmo formato que a API real retornaria:
    {
        "status": 0,
        "csv": {
            "id_evento": { campos... },
            ...
        }
    }
    """
    csv_data = {}
    total_registros = random.randint(50, 150)

    for i in range(1, total_registros + 1):
        hora = random.randint(7, 19)
        minuto = random.randint(0, 59)
        segundo = random.randint(0, 59)
        dt_evento = datetime(
            data_ref.year, data_ref.month, data_ref.day,
            hora, minuto, segundo
        )

        fila_id = random.choice(list(FILAS.keys()))
        fila_nome = FILAS[fila_id]

        agent_id = random.choice(list(AGENTES.keys()))
        agent_nome = AGENTES[agent_id]

        evento = random.choices(EVENTOS, weights=[55, 20, 15, 10])[0]

        completeagent  = 1 if evento == "COMPLETEAGENT"  else 0
        completecaller = 1 if evento == "COMPLETECALLER" else 0
        ringnoanswer   = random.randint(1, 3) if evento == "RINGNOANSWER" else 0
        transfer       = 1 if evento == "TRANSFER" else 0
        connect        = 1 if evento in ("COMPLETEAGENT", "COMPLETECALLER", "TRANSFER") else 0

        nota      = random.randint(1, 5) if connect else ""
        tabulacao = random.choice(TABULACOES) if connect else "Não Atendida"

        row_id = f"EVT{data_ref.strftime('%Y%m%d')}{str(i).zfill(4)}"

        csv_data[row_id] = {
            "Protocolo":             f"PROT{random.randint(100000, 999999)}",
            "callerid":              gera_numero(),
            "dt_up_Cliente":         dt_evento.strftime("%Y-%m-%d %H:%M:%S"),
            "colaborador_up_Cliente": agent_nome,
            "ramal_up_Cliente":      f"20{random.randint(10, 99)}",
            "date":                  dt_evento.strftime("%Y-%m-%d %H:%M:%S"),
            "event":                 evento,
            "queue_id":              fila_id,
            "queue":                 fila_nome,
            "agent_id":              agent_id,
            "agent":                 agent_nome,
            "RINGNOANSWER":          ringnoanswer,
            "COMPLETEAGENT":         completeagent,
            "COMPLETECALLER":        completecaller,
            "TRANSFER":              transfer,
            "CONNECT":               connect,
            "nota_avaliacao":        str(nota),
            "tabulacao_fila":        tabulacao,
            "TME":                   gera_tempo(5, 180),
            "TMA":                   gera_tempo(30, 900) if connect else "00:00",
            "SLA":                   random.choice(["SIM", "NÃO"]),
            "SLA-P":                 f"{random.randint(60, 98)}%",
            "all_call":              str(random.randint(80, 500)),
            "all_esp":               str(random.randint(10, 80)),
            "max_esp":               gera_tempo(60, 600),
        }

    return {"status": 0, "csv": csv_data}


# FUNÇÕES DE CONVERSÃO
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


# MAPEAMENTO DE COLUNAS E SQL DE UPSERT

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


# LÓGICA PRINCIPAL

def obter_data_inicial():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        try:
            return datetime.strptime(sys.argv[1].strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Data inválida. Use o formato YYYY-MM-DD.")
    return date.today() - timedelta(days=1)


def gerar_datas(data_inicial, data_final):
    datas = []
    d = data_inicial
    while d <= data_final:
        datas.append(d)
        d += timedelta(days=1)
    return datas


def main():
    conn = None
    try:
        data_inicial = obter_data_inicial()
        data_final   = date.today() - timedelta(days=1)
        datas        = gerar_datas(data_inicial, data_final)

        print("=" * 50)
        print("  MODO MOCK — API simulada localmente")
        print("  Nenhuma requisição real será feita.")
        print("=" * 50)
        print(f"Período: {datas[0]} até {datas[-1]}")
        print(f"Total de datas: {len(datas)}")
        print()

        conn   = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        total_geral = 0
        erros = []

        for data_ref in datas:
            try:
                print(f"Processando {data_ref} (simulado) ...")
                payload     = simular_api(data_ref)
                total_csv   = len(payload.get("csv", {}))
                total_salvo = salvar_registros(cursor, payload)
                conn.commit()
                print(f"  → csv={total_csv}  gravados={total_salvo}")
                total_geral += total_salvo
            except Exception as e:
                conn.rollback()
                print(f"  ✗ Erro em {data_ref}: {e}")
                erros.append(data_ref)

        print()
        print(f"Concluído. Total geral gravado: {total_geral} registros.")
        if erros:
            print(f"Falha em {len(erros)} data(s). Marcando execução como erro.")
            return 1
        return 0

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro fatal: {e}")
        return 1
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
