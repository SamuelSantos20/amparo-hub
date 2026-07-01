#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Desenlvolvido por Luiz Adriano Pereira de Lima 5521985395900
#

import sys
from datetime import datetime, date, timedelta

import requests
import mysql.connector
from mysql.connector import Error


API_URL = "http://177.69.231.91/agi_lab/app.php"

API_USER = "root"
API_PWD = "simples01"
API_APP = "extrato"
API_INTERVALO = "0"
API_KEY_AGENTS = ""
API_KEY_QUEUES = ""

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "lyd2160i",
    "database": "amparo",
    "charset": "utf8mb4",
}

TABELA = "api_extrato_dia"
HTTP_TIMEOUT = 300


def get_conexao():
    return mysql.connector.connect(**DB_CONFIG)


def criar_tabela(cursor):
    sql = f"""
    CREATE TABLE IF NOT EXISTS `{TABELA}` (
        `id` VARCHAR(255) NOT NULL,
        `protocolo` VARCHAR(100) DEFAULT NULL,
        `callerid` VARCHAR(100) DEFAULT NULL,
        `dt_up_cliente` DATETIME DEFAULT NULL,
        `colaborador_up_cliente` VARCHAR(255) DEFAULT NULL,
        `ramal_up_cliente` VARCHAR(100) DEFAULT NULL,
        `date_evento` DATETIME DEFAULT NULL,
        `event` VARCHAR(100) DEFAULT NULL,
        `queue_id` VARCHAR(50) DEFAULT NULL,
        `queue` VARCHAR(255) DEFAULT NULL,
        `agent_id` VARCHAR(50) DEFAULT NULL,
        `agent` VARCHAR(255) DEFAULT NULL,
        `RINGNOANSWER` INT DEFAULT 0,
        `COMPLETEAGENT` INT DEFAULT 0,
        `COMPLETECALLER` INT DEFAULT 0,
        `TRANSFER` INT DEFAULT 0,
        `CONNECT` INT DEFAULT 0,
        `nota_avaliacao` VARCHAR(255) DEFAULT NULL,
        `tabulacao_fila` VARCHAR(255) DEFAULT NULL,
        `TME` VARCHAR(50) DEFAULT NULL,
        `TMA` VARCHAR(50) DEFAULT NULL,
        `SLA` VARCHAR(50) DEFAULT NULL,
        `SLA_P` VARCHAR(50) DEFAULT NULL,
        `all_call` VARCHAR(50) DEFAULT NULL,
        `all_esp` VARCHAR(50) DEFAULT NULL,
        `max_esp` VARCHAR(50) DEFAULT NULL,
        PRIMARY KEY (`id`),
        KEY `idx_date_evento` (`date_evento`),
        KEY `idx_protocolo` (`protocolo`),
        KEY `idx_callerid` (`callerid`),
        KEY `idx_agent_id` (`agent_id`),
        KEY `idx_queue_id` (`queue_id`),
        KEY `idx_event` (`event`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql)


def validar_data_entrada(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Data inválida. Use o formato YYYY-MM-DD.")


def obter_data_inicial():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return validar_data_entrada(sys.argv[1].strip())
    return date.today()


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


def salvar_registros(cursor, payload):
    registros = payload.get("csv", {})

    sql = f"""
    INSERT INTO `{TABELA}` (
        `id`,
        `protocolo`,
        `callerid`,
        `dt_up_cliente`,
        `colaborador_up_cliente`,
        `ramal_up_cliente`,
        `date_evento`,
        `event`,
        `queue_id`,
        `queue`,
        `agent_id`,
        `agent`,
        `RINGNOANSWER`,
        `COMPLETEAGENT`,
        `COMPLETECALLER`,
        `TRANSFER`,
        `CONNECT`,
        `nota_avaliacao`,
        `tabulacao_fila`,
        `TME`,
        `TMA`,
        `SLA`,
        `SLA_P`,
        `all_call`,
        `all_esp`,
        `max_esp`
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON DUPLICATE KEY UPDATE
        `protocolo` = VALUES(`protocolo`),
        `callerid` = VALUES(`callerid`),
        `dt_up_cliente` = VALUES(`dt_up_cliente`),
        `colaborador_up_cliente` = VALUES(`colaborador_up_cliente`),
        `ramal_up_cliente` = VALUES(`ramal_up_cliente`),
        `date_evento` = VALUES(`date_evento`),
        `event` = VALUES(`event`),
        `queue_id` = VALUES(`queue_id`),
        `queue` = VALUES(`queue`),
        `agent_id` = VALUES(`agent_id`),
        `agent` = VALUES(`agent`),
        `RINGNOANSWER` = VALUES(`RINGNOANSWER`),
        `COMPLETEAGENT` = VALUES(`COMPLETEAGENT`),
        `COMPLETECALLER` = VALUES(`COMPLETECALLER`),
        `TRANSFER` = VALUES(`TRANSFER`),
        `CONNECT` = VALUES(`CONNECT`),
        `nota_avaliacao` = VALUES(`nota_avaliacao`),
        `tabulacao_fila` = VALUES(`tabulacao_fila`),
        `TME` = VALUES(`TME`),
        `TMA` = VALUES(`TMA`),
        `SLA` = VALUES(`SLA`),
        `SLA_P` = VALUES(`SLA_P`),
        `all_call` = VALUES(`all_call`),
        `all_esp` = VALUES(`all_esp`),
        `max_esp` = VALUES(`max_esp`)
    """

    total = 0

    for row_id, row in registros.items():
        if not isinstance(row, dict):
            continue

        protocolo = row.get("Protocolo ") or row.get("Protocolo")
        callerid = row.get("callerid")
        dt_up_cliente = row.get("dt_up_Cliente")
        colaborador_up_cliente = row.get("colaborador_up_Cliente")
        ramal_up_cliente = row.get("ramal_up_Cliente")
        date_evento = row.get("date")
        event = row.get("event")
        queue_id = row.get("queue_id")
        queue = row.get("queue")
        agent_id = row.get("agent_id")
        agent = row.get("agent")
        ringnoanswer = to_int(row.get("RINGNOANSWER"))
        completeagent = to_int(row.get("COMPLETEAGENT"))
        completecaller = to_int(row.get("COMPLETECALLER"))
        transfer = to_int(row.get("TRANSFER"))
        connect = to_int(row.get("CONNECT"))
        nota_avaliacao = row.get("nota_avaliacao")
        tabulacao_fila = row.get("tabulacao_fila")
        tme = row.get("TME")
        tma = row.get("TMA")
        sla = row.get("SLA")
        sla_p = row.get("SLA-P")
        all_call = row.get("all_call")
        all_esp = row.get("all_esp")
        max_esp = row.get("max_esp")

        cursor.execute(sql, (
            to_str(row_id),
            to_str(protocolo),
            to_str(callerid),
            to_datetime_str(dt_up_cliente),
            to_str(colaborador_up_cliente),
            to_str(ramal_up_cliente),
            to_datetime_str(date_evento),
            to_str(event),
            to_str(queue_id),
            to_str(queue),
            to_str(agent_id),
            to_str(agent),
            ringnoanswer,
            completeagent,
            completecaller,
            transfer,
            connect,
            to_str(nota_avaliacao),
            to_str(tabulacao_fila),
            to_str(tme),
            to_str(tma),
            to_str(sla),
            to_str(sla_p),
            to_str(all_call),
            to_str(all_esp),
            to_str(max_esp)
        ))
        total += 1

    return total


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
        data_inicial = obter_data_inicial()
        data_final = date.today()
        datas = gerar_datas(data_inicial, data_final)

        print(f"Período de execução: {datas[0].strftime('%Y-%m-%d')} até {datas[-1].strftime('%Y-%m-%d')}")
        print(f"Total de datas: {len(datas)}")

        conn = get_conexao()
        cursor = conn.cursor()
        criar_tabela(cursor)
        conn.commit()

        sess = requests.Session()
        # sess.cookies.set("PHPSESSID", "se_precisar")

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
        print(f"Erro MySQL: {e}")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erro geral: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
        if sess:
            sess.close()


if __name__ == "__main__":
    main()
