-- ============================================================
-- amparo-hub | Tabela: chamadas (v2 - baseada na API real)
-- Campos extraídos do script extrato.py (sistema de telefonia)
-- ============================================================

-- Remove a tabela antiga (protótipo fictício) se existir
DROP TABLE IF EXISTS chamadas_old;
ALTER TABLE IF EXISTS chamadas RENAME TO chamadas_old;

CREATE TABLE chamadas (
    id                      VARCHAR(255) PRIMARY KEY,
    protocolo               VARCHAR(100),
    callerid                VARCHAR(100),
    dt_up_cliente           TIMESTAMP,
    colaborador_up_cliente  VARCHAR(255),
    ramal_up_cliente        VARCHAR(100),
    date_evento             TIMESTAMP,
    event                   VARCHAR(100),
    queue_id                VARCHAR(50),
    queue                   VARCHAR(255),
    agent_id                VARCHAR(50),
    agent                   VARCHAR(255),
    ringnoanswer            INT DEFAULT 0,
    completeagent           INT DEFAULT 0,
    completecaller          INT DEFAULT 0,
    transfer                INT DEFAULT 0,
    connect                 INT DEFAULT 0,
    nota_avaliacao          VARCHAR(255),
    tabulacao_fila          VARCHAR(255),
    tme                     VARCHAR(50),  -- Tempo Médio de Espera
    tma                     VARCHAR(50),  -- Tempo Médio de Atendimento
    sla                     VARCHAR(50),
    sla_p                   VARCHAR(50),
    all_call                VARCHAR(50),
    all_esp                 VARCHAR(50),
    max_esp                 VARCHAR(50),
    created_at              TIMESTAMPTZ DEFAULT now()
);

-- Índices para acelerar os filtros e agregações do dashboard
CREATE INDEX idx_chamadas_date_evento ON chamadas(date_evento);
CREATE INDEX idx_chamadas_protocolo   ON chamadas(protocolo);
CREATE INDEX idx_chamadas_callerid    ON chamadas(callerid);
CREATE INDEX idx_chamadas_agent_id    ON chamadas(agent_id);
CREATE INDEX idx_chamadas_queue_id    ON chamadas(queue_id);
CREATE INDEX idx_chamadas_event       ON chamadas(event);
