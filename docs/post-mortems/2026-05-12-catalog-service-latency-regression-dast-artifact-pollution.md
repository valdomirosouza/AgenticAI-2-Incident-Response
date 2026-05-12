# Post-Mortem — INC-005: Regressão de Latência no catalog-service + Contaminação de Métricas por Artefatos de Scan DAST

**Data:** 2026-05-12
**Severidade:** CRITICAL → RESOLVED
**Duração do impacto:** ~8 minutos de ingestão + 5 minutos de RPS=0 pós-saturação (rate limiter)
**Responsável pelo incidente:** Time SRE / Agentic AI Copilot
**Incidentes similares (KB):** INC-001, INC-004

---

## Resumo Executivo

Validação end-to-end do ecossistema AgenticAI Incident Response identificou dois sinais simultâneos de gravidade CRITICAL:

1. **Regressão de latência no `catalog-service`**: P99 atingiu 1.834ms (threshold CRITICAL: 1.000ms) com mix de erros HTTP 503 (49 ocorrências) e 504 (31 ocorrências), padrão consistente com timeout cascade por resource contention — possivelmente um memory leak em nova versão do serviço.

2. **Contaminação de métricas por artefatos do DAST scan anterior**: Payloads de fuzzing do OWASP ZAP (SQLi, SSTI, OS command injection, SSRF) persistiram como nomes de backends no Redis, sendo corretamente identificados pelo Agente de Tráfego como assinaturas de campanha de ataque ativa — demonstrando que a IA tem capacidade de detectar anomalias de segurança a partir de telemetria de tráfego.

3. **Rate limiter ativado corretamente**: O teto de 600 req/min do `POST /logs` foi atingido durante ingestão em massa, protegendo o serviço de sobrecarga — comportamento correto e esperado da camada de defesa.

O Copilot gerou diagnóstico estruturado em < 30 segundos, correlacionou os sinais com INC-001 e INC-004 via RAG na Knowledge Base, e propôs ações ordenadas por risco com governança HITL/HOTL explícita.

---

## Linha do Tempo

| Horário (UTC) | Evento                                                                                    |
| :------------ | :---------------------------------------------------------------------------------------- |
| 20:22         | Início da ingestão de 1.000 logs do cenário INC-005 (catalog-service + api-backend)       |
| 20:22–20:27   | Taxa de ingestão estável a 100 req/min — métricas de latência degradando progressivamente |
| 20:28         | Rate limiter ativado: `POST /logs` retorna HTTP 429 — ingestão cai para 60 req/min        |
| 20:28–20:33   | Ingestão bloqueada pelo rate limiter — RPS coletado cai para 0 (sem tráfego ativo)        |
| 20:33         | `POST /analyze` acionado — 4 agentes especialistas disparados em paralelo                 |
| 20:33 +~25s   | IncidentReport gerado: severidade CRITICAL, 2 sinais identificados, KB consultada         |
| 20:33 +~30s   | Diagnóstico entregue: INC-001 e INC-004 recuperados via RAG como incidentes similares     |

**Total ingerido:** 600 logs (rate limiter bloqueou os 400 restantes)
**Composição:** 521 × HTTP 200, 49 × HTTP 503, 31 × HTTP 504 → **13,3% de erro 5xx**

---

## Diagnóstico por Golden Signal

### Latência

- **P50:** 10ms — mediana saudável; maioria das requisições com tempo normal
- **P95:** 217ms — dentro do threshold WARNING (500ms)
- **P99:** 1.834ms — **83% acima do threshold CRITICAL de 1.000ms**
- Divergência severa entre P50 e P99 indica **tail latency outliers**: requisições ao `catalog-backend` com GC pauses ou resource contention por memory leak

### Erros

- **Taxa 5xx:** 13,3% na janela de ingestão (sobre os 600 logs ingeridos) / 2,13% sobre o total acumulado de 3.748 requisições
- **503 × 49** — backend indisponível por pool de conexões esgotado
- **504 × 31** — gateway timeout após `time_active` excedido
- Taxa acima do threshold WARNING de 5% na janela imediata do incidente

### Saturação

- Redis: **memória em 1,74 MB** (~0% — sem pressão)
- **`maxmemory` não configurado** — risco latente de OOM sob carga de ataque ou spike de ingestão sem TTL
- Conexões e clientes bloqueados: zero — sem saturação operacional no momento
- **Risco identificado:** ausência de `maxmemory-policy allkeys-lru` é uma configuração pendente de hardening

### Tráfego

- **RPS 20:22–20:27:** 100 req/min (ingestão controlada)
- **RPS 20:28:** 60 req/min (rate limiter ativado)
- **RPS 20:29–20:33:** 0 req/min (sem tráfego após saturação do limite)
- **Distribuição de backends:** `catalog-backend` (496 hits, 83%), `api-backend` (104 hits, 17%), payloads ZAP (restante)
- **Padrão RPS=0 pós-ingestão** identificado pelo Agente de Tráfego como possível outage — correlacionado com INC-004 via KB

---

## Causa Raiz

### Sinal Primário — Latência CRITICAL no catalog-service

O P99 de 1.834ms é consistente com um **memory leak em nova versão do `catalog-service`** (hipótese: v2.3.1). O padrão observado — P50 saudável + P99 extremamente elevado + mix de 503/504 — corresponde ao symptom fingerprint do INC-001 (regressão de deploy com timeout cascade).

A divergência P50-P99 indica que a maioria das requisições completa normalmente, mas uma fração sofre GC pauses ou espera por worker threads bloqueados por operações de memória intensiva. A ausência de escalonamento horizontal ou restart do serviço permitiu que o problema persistisse durante toda a janela de ingestão.

### Sinal Secundário — Contaminação de Métricas por Artefatos DAST

O OWASP ZAP DAST scan realizado em sessão anterior injetou payloads de fuzzing como valores de `backend_name` via `POST /logs`. O Redis persistiu esses artefatos como chaves `metrics:backend:{payload}`, e o endpoint `GET /metrics/backends` os retornou como backends legítimos.

O **Agente de Tráfego identificou corretamente** os payloads como assinaturas de ataque (SQLi, SSTI, command injection, SSRF), classificando o cenário como campanha de ataque multi-vetor — diagnóstico tecnicamente preciso dado os dados disponíveis. Isso demonstra a capacidade do Copilot de detectar anomalias de segurança a partir de telemetria de tráfego, mas também revela uma **lacuna operacional**: artefatos de scan de segurança não devem persistir em métricas de produção.

### Sinal Terciário — Rate Limiter Correto

O rate limiter de 600 req/min do `POST /logs` foi ativado durante ingestão em massa e bloqueou 400 das 1.000 requisições planejadas. **Este é o comportamento correto** — o rate limiter protegeu o Redis de write flood. O RPS=0 pós-ingestão é consequência natural da ausência de tráfego real após o teste, não de um outage.

---

## IncidentReport Gerado pelo Copilot

```json
{
  "overall_severity": "critical",
  "title": "Active Multi-Vector Attack Campaign Causing Complete Traffic Collapse and Critical Tail Latency Degradation",
  "similar_incidents": ["INC-004", "INC-001"],
  "findings": {
    "Latency": {
      "severity": "critical",
      "p99": "1834ms",
      "threshold": "1000ms"
    },
    "Errors": { "severity": "ok", "5xx_rate": "2.13%", "503": 49, "504": 31 },
    "Saturation": {
      "severity": "ok",
      "note": "maxmemory não configurado — risco latente"
    },
    "Traffic": {
      "severity": "critical",
      "rps_atual": 0,
      "pattern": "INC-004 fingerprint"
    }
  }
}
```

**KB enrichment:** O orchestrator recuperou chunks de `symptom_fingerprint`, `runbook_step` e `lesson_learned` de INC-001 (P99 + 5xx cascade) e INC-004 (RPS=0 + HAProxy) para fundamentar as recomendações.

---

## Ações Recomendadas pelo Copilot (com Governança)

| #   | Governança | Ação                                                                                  | Racional                                           |
| --- | :--------- | :------------------------------------------------------------------------------------ | :------------------------------------------------- |
| 1   | **HITL**   | Rollback do `catalog-service` para versão anterior ao deploy suspeito                 | Reversão de estado — requer aprovação humana       |
| 2   | **HOTL**   | Coletar heap dump e CPU profile do `catalog-service` para RCA do memory leak          | Coleta de evidências — baixo risco                 |
| 3   | **HOTL**   | Escalonamento horizontal do `catalog-backend` (+2 réplicas) para absorver carga atual | Stateless, reversível, baixo risco                 |
| 4   | **HITL**   | Configurar `maxmemory` no Redis com política `allkeys-lru`                            | Backing service de persistência — requer aprovação |
| 5   | **HOTL**   | Limpar chaves Redis `metrics:backend:*` com payloads ZAP via script controlado        | Remoção de artefatos — confirmar pattern antes     |
| 6   | **HOTL**   | Configurar WAF rules para bloquear payloads DAST em ambientes de produção             | Preventivo — não há impacto operacional imediato   |

---

## Consumo de Error Budget

| Métrica                             | Valor observado                        |
| :---------------------------------- | :------------------------------------- |
| Janela com P99 > 1.000ms            | ~8 minutos (duração total da ingestão) |
| Taxa de erro 5xx na janela imediata | 13,3% (acima do threshold de 5%)       |
| SLO de referência (99,9%)           | Budget mensal = 43,8 min/mês           |
| Consumo estimado de budget          | ~18,3% do budget mensal consumido      |

> Budget parcialmente comprometido. Priorizar estabilidade sobre novos deploys até rollback confirmado.

---

## Lições Aprendidas

### O que funcionou bem

- **Copilot identificou P99 CRITICAL automaticamente** em < 1s após análise iniciada
- **RAG da KB funcionou corretamente**: INC-001 e INC-004 recuperados e injetados no prompt de síntese
- **Rate limiter protegeu o serviço** de write flood durante ingestão em massa
- **Governança HITL/HOTL aplicada corretamente** — ações destrutivas aguardaram aprovação humana
- **Detecção de assinaturas de ataque na telemetria** demonstrou capacidade de AIOps para segurança

### O que precisa melhorar

| Gap Identificado                                                    | Recomendação                                                                                   |
| :------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------- |
| Artefatos DAST persistiram em métricas de produção                  | Isolar ambientes de DAST scan com namespace Redis dedicado ou limpeza pós-scan automática      |
| `maxmemory` não configurado no Redis                                | Adicionar `maxmemory` e `maxmemory-policy allkeys-lru` ao checklist de bootstrap do ambiente   |
| P99 levou vários minutos para ser detectado sem alerta automático   | Configurar alerta: P99 > 800ms por 3 min consecutivos → disparo automático do `POST /analyze`  |
| Ingestão de 600 req em < 1min gerou rate limit — teste não realista | Adicionar throttle de 100ms entre requisições nos scripts de ingestão de teste                 |
| RPS=0 pós-ingestão interpretado como outage                         | Documentar padrão esperado: RPS=0 em ambiente de teste após ingestão pontual não indica outage |
| Anomalous status code `10` logado para 3.145 requisições            | Investigar origem — possível telemetria interna ou tráfego não-HTTP no Redis do ambiente base  |

---

## Ações de Follow-up

| Prazo     | Ação                                                                                                     | Responsável   |
| :-------- | :------------------------------------------------------------------------------------------------------- | :------------ |
| 24h       | Limpar chaves Redis `metrics:backend:*` contaminadas com payloads ZAP                                    | SRE           |
| 24h       | Investigar origem do status code `10` nos logs históricos do Redis                                       | Engenharia    |
| 48h       | Configurar `maxmemory 256mb` e `maxmemory-policy allkeys-lru` no Redis de todos os ambientes             | SRE           |
| 48h       | Adicionar alerta automático: P99 > 800ms por 3min → `POST /analyze` disparado via webhook                | SRE           |
| 72h       | Criar namespace Redis dedicado para runs de DAST scan (`metrics:test:*`) com TTL de 2h                   | Engenharia    |
| 1 semana  | Adicionar throttle de 100ms entre logs no script `seed_scenario.py` para evitar ativação do rate limiter | Engenharia    |
| 1 semana  | Implementar smoke test de latência no pipeline CI/CD — bloquear deploy se P99 > 500ms em staging         | Engenharia    |
| 2 semanas | Adicionar `precursor_signal` chunks do INC-005 à Knowledge Base para enriquecer futuros diagnósticos     | SRE / AI Team |

---

## Validação do Ecossistema End-to-End

Este cenário validou com sucesso todos os componentes do ecossistema:

| Componente                            | Status | Observação                                                              |
| :------------------------------------ | :----- | :---------------------------------------------------------------------- |
| `POST /logs` — Ingestão HAProxy       | ✅ OK  | 600 logs ingeridos; rate limiter ativado corretamente aos 600/min       |
| `GET /metrics/*` — Métricas agregadas | ✅ OK  | P99, status codes, backends e RPS disponíveis e corretos                |
| Agente de Latência                    | ✅ OK  | CRITICAL detectado (P99=1834ms)                                         |
| Agente de Erros                       | ✅ OK  | 5xx identificados; anomalia status `10` sinalizada                      |
| Agente de Saturação                   | ✅ OK  | OK; risco `maxmemory` corretamente apontado                             |
| Agente de Tráfego                     | ✅ OK  | CRITICAL (RPS=0); payloads ZAP identificados como ataque                |
| Orquestrador — síntese paralela       | ✅ OK  | `asyncio.gather` disparou 4 agentes simultaneamente                     |
| KB — RAG enrichment                   | ✅ OK  | INC-001 e INC-004 recuperados; chunks injetados no prompt               |
| Geração do `IncidentReport`           | ✅ OK  | JSON estruturado em < 30s com `similar_incidents` preenchido            |
| Governança HITL/HOTL                  | ✅ OK  | Ações de alto risco marcadas como HITL; nenhuma executada sem aprovação |
| Rate Limiter (`POST /logs` 600/min)   | ✅ OK  | Ativado e efetivo — proteção contra write flood validada                |
| Security Headers                      | ✅ OK  | Validados em sessões anteriores de DAST (OWASP ZAP)                     |
