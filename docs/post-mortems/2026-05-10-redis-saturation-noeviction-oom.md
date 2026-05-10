# Post-Mortem — Redis Saturação CRITICAL (90% memória) + Política noeviction

**Data:** 2026-05-10
**Severidade:** CRITICAL → CONTAINED
**Duração do risco:** Indeterminada (crescimento gradual sem TTL)
**Responsável pelo incidente:** Time SRE

---

## Resumo Executivo

Redis atingiu 90% de utilização de memória com política `noeviction` configurada, colocando o sistema a uma rajada de ingestão de distância de falha total de escrita (`OOM command not allowed`). A causa raiz é estrutural: contadores de métricas sem TTL acumulam indefinidamente conforme logs são ingeridos. A ação imediata de alterar a política para `allkeys-lru` conteve o incidente. A correção definitiva requer refatoração no serviço de ingestão para expirar chaves por janela de tempo.

---

## Linha do Tempo

| Horário (relativo) | Evento                                                                   |
| :----------------- | :----------------------------------------------------------------------- |
| T-indefinido       | Contadores Redis crescendo sem TTL desde o início da operação do serviço |
| T+0h               | Alertas de saturação disparados — Redis em 90% de memória                |
| T+~5min            | Copilot acionado — contexto coletado, diagnóstico iniciado               |
| T+~10min           | Causa raiz identificada: contadores sem TTL + política `noeviction`      |
| T+~12min           | Ação 1 autorizada (HITL): `maxmemory-policy` alterada para `allkeys-lru` |
| T+~15min           | Incidente contido — risco de OOM eliminado                               |

---

## Diagnóstico por Golden Signal

- **Latência:** Não impactada no momento da detecção — risco potencial se OOM ocorresse e `POST /logs` começasse a retornar 500.
- **Erros:** Não impactados no momento da detecção — `noeviction` impediria qualquer escrita ao atingir o limite.
- **Saturação:** Redis em **90% de memória** — threshold CRITICAL (> 80%) ultrapassado. Política `noeviction` configurada eliminava qualquer mecanismo de auto-recuperação.
- **Tráfego:** Volume de ingestão de logs dentro do esperado — o crescimento foi gradual e estrutural, não causado por spike pontual.

---

## Causa Raiz

**Causa imediata:** Política `maxmemory-policy: noeviction` impedia qualquer descarte automático de chaves, tornando o OOM inevitável com o crescimento contínuo dos dados.

**Causa estrutural:** Contadores de métricas sem TTL acumulam indefinidamente no Redis:

| Chave                            | TTL              | Comportamento                                     |
| :------------------------------- | :--------------- | :------------------------------------------------ |
| `metrics:requests:total`         | Nenhum           | Cresce 1 por log ingerido                         |
| `metrics:status:{code}`          | Nenhum           | Cresce por status code único                      |
| `metrics:backend:{name}`         | Nenhum           | Cresce por backend único                          |
| `metrics:frontend:{name}`        | Nenhum           | Cresce por frontend único                         |
| `metrics:errors:4xx / 5xx`       | Nenhum           | Contadores globais sem expiração                  |
| `metrics:rps:{YYYY-MM-DDTHH:MM}` | 2h               | Único com TTL — correto                           |
| `metrics:response_times`         | Nenhum (capeado) | Bounded por `RESPONSE_TIME_MAX_ENTRIES` — correto |

O sorted set `metrics:response_times` está corretamente capeado em 100.000 entradas e **não** é o vetor de crescimento.

---

## Ações Executadas

1. **[HOTL]** Coleta de diagnóstico: `redis-cli --bigkeys`, `INFO memory`, `DBSIZE`
2. **[HITL — aprovado]** Alteração de `maxmemory-policy: noeviction` → `allkeys-lru`
3. **[HOTL]** Monitoramento pós-ação: `used_memory`, `evicted_keys`, `POST /logs`

---

## Impacto Evitado

Com `noeviction`, ao atingir 100% de memória o Redis passaria a retornar `OOM command not allowed` para todas as operações de escrita, causando:

- `POST /logs` → 500 (falha total de ingestão)
- `GET /metrics/*` → dados congelados no último estado antes do OOM
- `POST /analyze` → diagnóstico cego, sem dados atualizados dos Four Golden Signals

---

## Lições Aprendidas

**O que funcionou bem:**

- Alertas de saturação dispararam antes do OOM — MTTD adequado
- Governança HITL impediu alteração em backing service sem aprovação
- Diagnóstico correto identificou a causa raiz estrutural além da ação imediata

**O que precisa melhorar:**

| Gap Identificado                                             | Recomendação                                                               |
| :----------------------------------------------------------- | :------------------------------------------------------------------------- |
| Contadores sem TTL acumulam indefinidamente                  | Refatorar `ingestion.py` para expirar chaves por janela de tempo           |
| `noeviction` é política inadequada para workload de métricas | Definir `allkeys-lru` como padrão no `docker-compose.yml` e `.env.example` |
| Sem alerta de tendência de crescimento                       | Configurar alerta em > 70% de memória para ação preventiva, não reativa    |
| Causa raiz não será corrigida pela ação imediata             | Ação 1 é paliativa — correção estrutural ainda pendente                    |

---

## Ações de Follow-up

| Prazo    | Ação                                                                                                             | Responsável |
| :------- | :--------------------------------------------------------------------------------------------------------------- | :---------- |
| 24h      | Verificar se `used_memory` estabilizou após ativação do `allkeys-lru`                                            | SRE         |
| 48h      | Avaliar `CONFIG SET maxmemory` para aumentar o limite se o host tiver RAM disponível                             | SRE         |
| 1 semana | Refatorar `Log-Ingestion-and-Metrics/app/services/ingestion.py` — adicionar TTL nos contadores por janela diária | Engenharia  |
| 1 semana | Definir `maxmemory-policy allkeys-lru` no `docker-compose.yml` como padrão de configuração                       | Engenharia  |
| 1 semana | Adicionar alerta preventivo: Redis > 70% de memória → WARNING antes de atingir threshold CRITICAL                | SRE         |
