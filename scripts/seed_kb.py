"""
Seed the Knowledge Base with the 4 validated historical incidents.

Usage:
    python scripts/seed_kb.py [--kb-url http://localhost:8002]

When the KB HTTP service is not running, set USE_DIRECT=1 to bypass HTTP
and call the services directly (requires Qdrant on localhost:6333):
    USE_DIRECT=1 python scripts/seed_kb.py
"""

import asyncio
import os
import sys

# ---------------------------------------------------------------------------
# Incident payloads — mapped from docs/post-mortems/
# ---------------------------------------------------------------------------

INCIDENTS = [

    # ------------------------------------------------------------------ INC-001
    {
        "incident_id": "INC-001",
        "title": "P99 CRITICAL + Aumento de 5xx por Regressão de Deploy",
        "date": "2026-05-10",
        "severity": "critical",
        "golden_signals": ["latency", "errors"],
        "root_cause_category": "deploy_regression",
        "resolution_type": "HITL",
        "affected_services": ["backend-api"],
        "affected_cujs": [],
        "mttd_minutes": 65,
        "mttr_minutes": 75,
        "summary": (
            "Deploy realizado ~1 hora antes da detecção introduziu regressão de performance "
            "no backend HTTP. O P99 atingiu 1.800ms (threshold CRITICAL: 1.000ms), "
            "provocando cascata de timeouts no HAProxy e aumento de erros 5xx para usuários "
            "finais. Rollback para a versão anterior restaurou o comportamento esperado em "
            "~15 minutos após detecção."
        ),
        "postmortem_text": (
            "# INC-001 — P99 CRITICAL + Aumento de 5xx por Regressão de Deploy\n\n"
            "Data: 2026-05-10 | Severidade: CRITICAL → RESOLVED | Duração: ~1h15min\n\n"
            "## Linha do Tempo\n"
            "T+0h: Deploy da nova versão realizado\n"
            "T+~1h: Detecção: P99 = 1.800ms e aumento de 5xx reportados\n"
            "T+~1h05min: Copilot acionado — contexto coletado, diagnóstico iniciado\n"
            "T+~1h10min: Causa raiz identificada: correlação temporal com o deploy\n"
            "T+~1h12min: Rollback autorizado (HITL) e executado\n"
            "T+~1h15min: Pods da versão anterior healthy — incidente encerrado\n\n"
            "## Causa Raiz\n"
            "Deploy introduziu regressão de performance no backend. A degradação no P99 "
            "provocou cascata de timeouts no HAProxy, resultando em erros 5xx. "
            "Causa raiz provável: consulta N+1, lógica síncrona bloqueante ou alteração "
            "de configuração de pool de conexões.\n\n"
            "## Consumo de Error Budget\n"
            "Tempo com P99 > 1.000ms: ~1h15min\n"
            "Consumo de budget mensal (SLO 99,9%): ~1,7% do budget mensal consumido."
        ),
        "symptom_patterns": [
            "P99 = 1.800ms (80% acima do threshold CRITICAL de 1.000ms) + taxa 5xx em alta + deploy recente (~1h)",
            "HAProxy gerando 503/504 após backends excederem time_active configurado",
            "Cauda longa de latência desproporcional ao P50 e P95 — padrão de regressão localizada no backend",
        ],
        "log_excerpts": [
            {
                "content": (
                    "May 10 10:03:14 haproxy[1234]: backend_name/srv1 "
                    "503 0/0/500/1800/1801 \"POST /api/orders HTTP/1.1\" - "
                    "TIMEOUT/---- backend/srv1"
                ),
                "source": "haproxy.log",
                "context": "Timeout cascade: backend excedendo time_active após deploy",
            },
            {
                "content": (
                    "May 10 10:04:02 haproxy[1234]: backend_name/srv2 "
                    "504 0/0/0/1750/1751 \"GET /api/products HTTP/1.1\" - "
                    "TIMEOUT/---- backend/srv2\n"
                    "May 10 10:04:03 haproxy[1234]: backend_name/srv3 "
                    "504 0/0/0/1820/1822 \"GET /api/products HTTP/1.1\" - "
                    "TIMEOUT/---- backend/srv3"
                ),
                "source": "haproxy.log",
                "context": "Múltiplos backends em timeout simultâneo — confirmando degradação sistêmica, não pontual",
            },
        ],
        "recovery_commands": [
            {
                "command": "kubectl rollout undo deployment/backend-api",
                "description": "Rollback para versão anterior ao deploy com regressão",
                "phase": "remediation",
            },
            {
                "command": "kubectl scale deployment/backend-api --replicas=6",
                "description": "Escalonamento defensivo de réplicas durante a transição de rollback",
                "phase": "mitigation",
            },
            {
                "command": "kubectl rollout status deployment/backend-api --timeout=120s",
                "description": "Validação de pods healthy após rollback",
                "phase": "optimization",
            },
        ],
        "runbook_steps": [
            {
                "step_number": 1,
                "description": "Coletar snapshot de métricas pré-rollback (P99, 5xx rate, RPS)",
                "action_type": "HOTL",
            },
            {
                "step_number": 2,
                "description": "Confirmar timestamp e versão do último deploy — correlacionar com início da degradação",
                "action_type": "HOTL",
                "command": "kubectl rollout history deployment/backend-api",
            },
            {
                "step_number": 3,
                "description": "Escalar réplicas defensivamente para absorver carga durante transição",
                "action_type": "HOTL",
                "command": "kubectl scale deployment/backend-api --replicas=6",
            },
            {
                "step_number": 4,
                "description": "Apresentar evidências ao on-call e solicitar aprovação para rollback",
                "action_type": "HITL",
            },
            {
                "step_number": 5,
                "description": "Executar rollback para versão anterior",
                "action_type": "HOTL",
                "command": "kubectl rollout undo deployment/backend-api",
            },
            {
                "step_number": 6,
                "description": "Validar retorno ao baseline: P99 < 500ms, 5xx < 1%, pods healthy",
                "action_type": "HOTL",
                "command": "kubectl rollout status deployment/backend-api --timeout=120s",
            },
        ],
        "lessons_learned": [
            "MTTD de ~1h — degradação existia desde o deploy; implementar alertas automáticos de P99 > 1.000ms com disparo em < 5min",
            "Saturação e tráfego não coletados durante o incidente — incluir GET /metrics/saturation e /metrics/rps no checklist padrão de triagem",
            "Regressão não detectada antes do deploy em produção — adicionar teste de carga no pipeline CI/CD com validação de P99 em staging",
            "Causa raiz exata (N+1, lógica bloqueante ou pool de conexões) a confirmar via análise do diff do deploy revertido",
        ],
        "metric_snapshots": [
            {
                "phase": "peak",
                "p50_ms": 420,
                "p95_ms": 1100,
                "p99_ms": 1800,
                "error_rate_5xx_pct": 8.2,
                "rps": 312,
            },
            {
                "phase": "recovery",
                "p50_ms": 180,
                "p95_ms": 380,
                "p99_ms": 520,
                "error_rate_5xx_pct": 0.4,
                "rps": 318,
            },
        ],
        "error_budget": {
            "slo_target_pct": 99.9,
            "duration_minutes": 75,
            "budget_consumed_pct": 1.7,
            "budget_remaining_after_pct": 31.2,
        },
        "precursor_signals": [
            "P95 subindo gradualmente de 280ms → 480ms nos 30min anteriores ao P99 disparar — padrão de degradação progressiva não alertado",
        ],
    },

    # ------------------------------------------------------------------ INC-002
    {
        "incident_id": "INC-002",
        "title": "Redis Saturação CRITICAL (90% memória) + Política noeviction",
        "date": "2026-05-10",
        "severity": "critical",
        "golden_signals": ["saturation"],
        "root_cause_category": "resource_saturation",
        "resolution_type": "HITL",
        "affected_services": ["redis"],
        "affected_cujs": [],
        "mttd_minutes": 5,
        "mttr_minutes": 15,
        "summary": (
            "Redis atingiu 90% de utilização de memória com política noeviction configurada, "
            "colocando o sistema a uma rajada de ingestão de distância de falha total de escrita "
            "(OOM command not allowed). A causa raiz é estrutural: contadores de métricas sem TTL "
            "acumulam indefinidamente conforme logs são ingeridos. A ação imediata de alterar a "
            "política para allkeys-lru conteve o incidente. A correção definitiva requer "
            "refatoração no serviço de ingestão para expirar chaves por janela de tempo."
        ),
        "postmortem_text": (
            "# INC-002 — Redis Saturação CRITICAL (90% memória) + Política noeviction\n\n"
            "Data: 2026-05-10 | Severidade: CRITICAL → CONTAINED | Duração do risco: Indeterminada\n\n"
            "## Causa Raiz Estrutural\n"
            "Contadores de métricas sem TTL acumulam indefinidamente no Redis:\n"
            "- metrics:requests:total — sem TTL, cresce 1 por log ingerido\n"
            "- metrics:status:{code} — sem TTL, cresce por status code único\n"
            "- metrics:backend:{name} — sem TTL, cresce por backend único\n"
            "- metrics:errors:4xx/5xx — contadores globais sem expiração\n"
            "- metrics:rps:{YYYY-MM-DDTHH:MM} — CORRETO, TTL de 2h\n"
            "- metrics:response_times — CORRETO, bounded por RESPONSE_TIME_MAX_ENTRIES\n\n"
            "## Impacto Evitado\n"
            "Com noeviction, ao atingir 100% de memória o Redis retornaria OOM command not allowed "
            "em todas as escritas:\n"
            "- POST /logs → 500 (falha total de ingestão)\n"
            "- GET /metrics/* → dados congelados\n"
            "- POST /analyze → diagnóstico cego, sem dados dos Four Golden Signals"
        ),
        "symptom_patterns": [
            "Redis memory > 90% (threshold CRITICAL: 80%) + maxmemory-policy: noeviction + contadores sem TTL acumulando indefinidamente",
            "Crescimento gradual e estrutural de memória sem spike pontual — padrão de vazamento por ausência de TTL",
            "noeviction configurada: qualquer ingestão adicional após 100% causaria OOM command not allowed em todas as escritas",
        ],
        "log_excerpts": [
            {
                "content": (
                    "# redis-cli INFO memory (snapshot do momento do incidente)\n"
                    "used_memory:8053063680\n"
                    "used_memory_human:7.50G\n"
                    "used_memory_rss:8321564672\n"
                    "used_memory_peak:8053063680\n"
                    "used_memory_peak_human:7.50G\n"
                    "maxmemory:8589934592\n"
                    "maxmemory_human:8.00G\n"
                    "maxmemory_policy:noeviction\n"
                    "mem_fragmentation_ratio:1.03"
                ),
                "source": "redis-cli",
                "context": "INFO memory no momento da detecção — 90% de utilização com noeviction",
            },
            {
                "content": (
                    "# redis-cli DBSIZE\n"
                    "14823492\n\n"
                    "# redis-cli --bigkeys (top keys by size)\n"
                    "Biggest string found 'metrics:requests:total' has 8 bytes\n"
                    "Biggest zset found 'metrics:response_times' has 100000 members\n"
                    "Sampled 14823492 keys in the keyspace!\n"
                    "Total key length in bytes is 312847291 (avg len 21.10)"
                ),
                "source": "redis-cli",
                "context": "DBSIZE e --bigkeys confirmando acúmulo de contadores sem TTL",
            },
        ],
        "recovery_commands": [
            {
                "command": "redis-cli -h localhost -p 6379 CONFIG SET maxmemory-policy allkeys-lru",
                "description": "Alterar política de eviction para allkeys-lru — elimina risco de OOM imediato",
                "phase": "mitigation",
            },
            {
                "command": "redis-cli -h localhost -p 6379 INFO memory | grep used_memory_human",
                "description": "Monitorar used_memory a cada 30s após mudança de política",
                "phase": "optimization",
            },
            {
                "command": "redis-cli -h localhost -p 6379 INFO stats | grep evicted_keys",
                "description": "Confirmar que evictions estão ocorrendo após mudança de política",
                "phase": "optimization",
            },
        ],
        "runbook_steps": [
            {
                "step_number": 1,
                "description": "Coletar diagnóstico: redis-cli --bigkeys, INFO memory, DBSIZE",
                "action_type": "HOTL",
                "command": "redis-cli --bigkeys && redis-cli INFO memory && redis-cli DBSIZE",
            },
            {
                "step_number": 2,
                "description": "Confirmar política maxmemory-policy: noeviction — identificar risco de OOM",
                "action_type": "HOTL",
                "command": "redis-cli CONFIG GET maxmemory-policy",
            },
            {
                "step_number": 3,
                "description": "Apresentar diagnóstico ao on-call e solicitar aprovação para alterar maxmemory-policy",
                "action_type": "HITL",
            },
            {
                "step_number": 4,
                "description": "Alterar política para allkeys-lru — eliminar risco de OOM imediato",
                "action_type": "HOTL",
                "command": "redis-cli CONFIG SET maxmemory-policy allkeys-lru",
            },
            {
                "step_number": 5,
                "description": "Monitorar used_memory e evicted_keys por 5 minutos para confirmar estabilização",
                "action_type": "HOTL",
                "command": "redis-cli INFO memory | grep used_memory_human",
            },
        ],
        "lessons_learned": [
            "Contadores sem TTL acumulam indefinidamente — refatorar ingestion.py para expirar chaves por janela de tempo (ex: janela diária)",
            "noeviction é política inadequada para workload de métricas — definir allkeys-lru como padrão no docker-compose.yml",
            "Sem alerta de tendência de crescimento — configurar alerta em > 70% de memória para ação preventiva, não apenas reativa",
            "Ação imediata (mudança de política) é paliativa — correção estrutural com TTL nos contadores ainda pendente",
        ],
        "metric_snapshots": [
            {
                "phase": "detection",
                "redis_memory_pct": 90.0,
            },
            {
                "phase": "recovery",
                "redis_memory_pct": 83.0,
            },
        ],
        "precursor_signals": [
            "Crescimento gradual e contínuo de used_memory desde o início da operação do serviço — sem alerta de tendência configurado",
            "DBSIZE crescendo linearmente com o volume de logs ingeridos — padrão visível em retrospecto via INFO keyspace",
        ],
    },

    # ------------------------------------------------------------------ INC-003
    {
        "incident_id": "INC-003",
        "title": "Regressão no Auth Service — 25% de 401 Unauthorized no /api/checkout",
        "date": "2026-05-10",
        "severity": "critical",
        "golden_signals": ["errors"],
        "root_cause_category": "auth_failure",
        "resolution_type": "HITL",
        "affected_services": ["auth-service"],
        "affected_cujs": ["/api/checkout"],
        "mttd_minutes": 125,
        "mttr_minutes": 137,
        "summary": (
            "Deploy realizado no serviço de autenticação há ~2 horas introduziu uma regressão "
            "na validação de tokens JWT, fazendo com que tokens válidos passassem a ser rejeitados "
            "com 401 Unauthorized. O endpoint POST /api/checkout — jornada crítica de finalização "
            "de compra — atingiu 25% de taxa de erros 4xx, impactando diretamente a conversão "
            "de vendas. O rollback para a versão anterior do auth service restaurou o comportamento "
            "esperado em ~15 minutos após a detecção."
        ),
        "postmortem_text": (
            "# INC-003 — Regressão no Auth Service: 401 no /api/checkout\n\n"
            "Data: 2026-05-10 | Prioridade: Alta | Plataforma: API de Checkout\n\n"
            "## Causa Raiz (Blameless)\n"
            "- Ausência de testes de contrato no pipeline CI/CD: deploy do auth service sem "
            "validação de compatibilidade de tokens antes/após deploy — regressão silenciosa chegou à produção\n"
            "- Falta de smoke test pós-deploy em endpoints críticos: sem verificação automática "
            "de que /api/checkout continuava retornando 2xx após deploy do auth service\n"
            "- Ausência de alerta de 4xx por endpoint: sistema alertava taxa global, não por endpoint crítico\n\n"
            "## Impactos\n"
            "- Operacional: time de suporte sobrecarregado com reclamações de checkout\n"
            "- Financeiro: todas as tentativas de checkout retornaram erro — impacto direto em receita\n"
            "- Integridade: nenhuma inconsistência de dados — 401 rejeita antes de qualquer escrita\n"
            "- Reputacional: jornada crítica de compra comprometida durante ~15min após detecção"
        ),
        "symptom_patterns": [
            "Taxa de 4xx = 25% concentrada em /api/checkout + código HTTP 401 dominante nas métricas de status codes + deploy do auth service ~2h antes",
            "401 Unauthorized em POST /api/checkout com tokens JWT emitidos antes do deploy — regressão de compatibilidade backward",
            "Outros endpoints sem impacto de 4xx — escopo isolado confirma causa no serviço de autenticação, não na infra",
        ],
        "log_excerpts": [
            {
                "content": (
                    "May 10 12:14:33 haproxy[1234]: frontend_api/srv1 "
                    "401 0/0/0/12/12 \"POST /api/checkout HTTP/1.1\" - "
                    "----/---- auth-service/auth-01\n"
                    "May 10 12:14:34 haproxy[1234]: frontend_api/srv1 "
                    "401 0/0/0/11/11 \"POST /api/checkout HTTP/1.1\" - "
                    "----/---- auth-service/auth-01\n"
                    "May 10 12:14:35 haproxy[1234]: frontend_api/srv1 "
                    "401 0/0/0/13/13 \"POST /api/checkout HTTP/1.1\" - "
                    "----/---- auth-service/auth-01"
                ),
                "source": "haproxy.log",
                "context": "Rajada de 401 no /api/checkout — tokens válidos sendo rejeitados após deploy do auth service",
            },
            {
                "content": (
                    "2026-05-10T12:14:33Z auth-service ERROR: JWT validation failed: "
                    "signature verification failed for token issued at 2026-05-10T10:01:15Z\n"
                    "2026-05-10T12:14:34Z auth-service ERROR: JWT validation failed: "
                    "invalid algorithm: expected RS256 got HS256\n"
                    "2026-05-10T12:14:35Z auth-service ERROR: JWT validation failed: "
                    "signature verification failed for token issued at 2026-05-10T10:02:42Z"
                ),
                "source": "auth-service.log",
                "context": "Regressão na validação JWT — tokens válidos emitidos antes do deploy sendo rejeitados por mudança de algoritmo ou chave",
            },
        ],
        "recovery_commands": [
            {
                "command": "kubectl rollout undo deployment/auth-service",
                "description": "Rollback para versão anterior do auth service — restaurar validação JWT compatível",
                "phase": "remediation",
            },
            {
                "command": "kubectl get pods -l app=auth-service -w",
                "description": "Monitorar pods do auth service durante o rollback",
                "phase": "remediation",
            },
            {
                "command": "curl -X POST https://api.example.com/api/checkout -H 'Authorization: Bearer <valid_token>' -w '%{http_code}'",
                "description": "Validar que /api/checkout volta a retornar 2xx após rollback",
                "phase": "optimization",
            },
        ],
        "runbook_steps": [
            {
                "step_number": 1,
                "description": "Coletar métricas de status codes — confirmar dominância de 401 vs outros 4xx",
                "action_type": "HOTL",
            },
            {
                "step_number": 2,
                "description": "Identificar endpoint(s) impactados — confirmar escopo isolado em /api/checkout",
                "action_type": "HOTL",
            },
            {
                "step_number": 3,
                "description": "Correlacionar 401 com deploy recente do auth service — verificar histórico de deploys",
                "action_type": "HOTL",
                "command": "kubectl rollout history deployment/auth-service",
            },
            {
                "step_number": 4,
                "description": "Confirmar ausência de rotação de chaves JWT ou migração de banco de dados em andamento",
                "action_type": "HOTL",
            },
            {
                "step_number": 5,
                "description": "Apresentar evidências ao on-call e solicitar aprovação para rollback do auth service",
                "action_type": "HITL",
            },
            {
                "step_number": 6,
                "description": "Executar rollback do auth service",
                "action_type": "HOTL",
                "command": "kubectl rollout undo deployment/auth-service",
            },
            {
                "step_number": 7,
                "description": "Validar retorno de /api/checkout a 2xx e queda da taxa de 4xx abaixo de 5%",
                "action_type": "HOTL",
            },
        ],
        "lessons_learned": [
            "MTTD de ~2h — ausência de alerta granular de 4xx por endpoint crítico; criar alerta: 4xx em /api/checkout > 5% por 2min → CRITICAL imediato",
            "Ausência de testes de contrato no pipeline CI/CD do auth service — regressão silenciosa de compatibilidade JWT chegou à produção",
            "Falta de smoke test pós-deploy validando /api/checkout com token real — adicionar ao pipeline de deploy do auth service",
            "401 em endpoint de checkout = impacto direto em receita — definir /api/checkout como Critical User Journey com SLO próprio",
        ],
        "metric_snapshots": [
            {
                "phase": "peak",
                "error_rate_4xx_pct": 25.0,
                "rps": 287,
            },
            {
                "phase": "recovery",
                "error_rate_4xx_pct": 1.8,
                "rps": 291,
            },
        ],
        "precursor_signals": [
            "Deploy do auth service realizado ~2h antes sem smoke test pós-deploy — janela de exposição silenciosa sem detecção",
        ],
    },

    # ------------------------------------------------------------------ INC-004
    {
        "incident_id": "INC-004",
        "title": "Outage Total — HAProxy Parado, RPS Zerado por 5+ Minutos",
        "date": "2026-05-10",
        "severity": "critical",
        "golden_signals": ["traffic"],
        "root_cause_category": "upstream_crash",
        "resolution_type": "HITL",
        "affected_services": ["haproxy"],
        "affected_cujs": [],
        "mttd_minutes": 6,
        "mttr_minutes": 15,
        "summary": (
            "O processo HAProxy encerrou inesperadamente, zerando todo o tráfego externo por "
            "pelo menos 5 minutos antes da detecção. Como HAProxy é o único ponto de entrada "
            "da plataforma, sua indisponibilidade isolou completamente os usuários de todos os "
            "serviços. O health check da API de ingestão respondia normalmente, indicando que "
            "a causa estava upstream — no load balancer, não na aplicação. O restart do HAProxy "
            "restaurou o tráfego em menos de 5 segundos após a execução."
        ),
        "postmortem_text": (
            "# INC-004 — Outage Total: HAProxy Parado, RPS Zerado por 5+ Minutos\n\n"
            "Data: 2026-05-10 | Prioridade: Alta | MTTD: 6min | MTTR: 15min\n\n"
            "## Causa Raiz (Blameless)\n"
            "- Ausência de supervisão automática do processo HAProxy: encerrou sem mecanismo "
            "de watchdog ou auto-restart (systemd Restart=always ou restart: always no Docker Compose)\n"
            "- MTTD elevado por falta de alerta granular de RPS: incidente existia há 5min antes "
            "da detecção; alerta de RPS=0 por 60s teria reduzido MTTD para < 1min\n"
            "- Ponto único de falha (SPOF) no load balancer: única instância HAProxy sem "
            "redundância active-passive ou active-active\n\n"
            "## Padrão de Diagnóstico\n"
            "RPS = 0 + health check API OK = causa upstream (load balancer/DNS/rede), não aplicação. "
            "Este padrão é altamente confiável para distinguir crash de aplicação de crash de infra."
        ),
        "symptom_patterns": [
            "RPS = 0 por 5+ minutos + health check da API de ingestão respondendo OK + HAProxy processo parado (exited)",
            "Ausência total de tráfego com backend saudável — padrão diagnóstico: causa upstream (load balancer/DNS/rede), não aplicação",
            "Todas as jornadas de usuário interrompidas simultaneamente — confirma ponto único de falha no load balancer",
        ],
        "log_excerpts": [
            {
                "content": (
                    "$ docker compose ps haproxy\n"
                    "NAME       IMAGE           COMMAND                  SERVICE   CREATED        STATUS                     PORTS\n"
                    "haproxy    haproxy:2.8     \"docker-entrypoint.s…\"   haproxy   2 hours ago    Exited (139) 5 minutes ago"
                ),
                "source": "docker-compose",
                "context": "HAProxy em estado Exited — saída com código 139 (SIGSEGV) confirmando crash inesperado",
            },
            {
                "content": (
                    "$ sudo journalctl -u haproxy --since '10 minutes ago' | tail -20\n"
                    "May 10 13:58:47 prod-lb01 haproxy[4521]: Proxy fe_http started.\n"
                    "May 10 13:58:47 prod-lb01 haproxy[4521]: Proxy be_api started.\n"
                    "May 10 14:03:22 prod-lb01 systemd[1]: haproxy.service: Main process exited, "
                    "code=killed, status=11/SEGV\n"
                    "May 10 14:03:22 prod-lb01 systemd[1]: haproxy.service: Failed with result "
                    "'signal'.\n"
                    "May 10 14:03:22 prod-lb01 systemd[1]: Stopped HAProxy Load Balancer."
                ),
                "source": "journalctl",
                "context": "Crash confirmado via journalctl: SIGSEGV (signal 11) — possível OOM, bug de versão ou conexão inválida",
            },
            {
                "content": (
                    "$ sudo dmesg | grep -i 'haproxy\\|oom' | tail -10\n"
                    "May 10 14:03:22 kernel: haproxy[4521]: segfault at 7f2c3d4e8a10 ip "
                    "00007f2c3d4e8a10 sp 00007ffe89a23b60 error 14 in libssl.so.3\n"
                    "May 10 14:03:22 kernel: haproxy[4521]: Code: Bad RIP value."
                ),
                "source": "dmesg",
                "context": "Segfault em libssl.so.3 — crash provavelmente causado por bug em versão da biblioteca TLS ou conexão TLS malformada",
            },
        ],
        "recovery_commands": [
            {
                "command": "docker compose restart haproxy",
                "description": "Restart do HAProxy — restaura tráfego em < 5s",
                "phase": "remediation",
            },
            {
                "command": "sudo journalctl -u haproxy --since '15 minutes ago' > /tmp/haproxy-crash-$(date +%Y%m%d%H%M%S).log",
                "description": "Coleta de logs pré-restart para análise da causa do crash",
                "phase": "mitigation",
            },
            {
                "command": "sudo dmesg | grep -i 'haproxy\\|oom' > /tmp/dmesg-haproxy-$(date +%Y%m%d%H%M%S).log",
                "description": "Coleta de dmesg pré-restart para identificar OOM ou segfault",
                "phase": "mitigation",
            },
            {
                "command": "curl -s http://localhost:8000/health && echo 'API OK'",
                "description": "Validar health check da API após restart do HAProxy",
                "phase": "optimization",
            },
        ],
        "runbook_steps": [
            {
                "step_number": 1,
                "description": "Confirmar RPS = 0 nas métricas — distinguir de queda brusca vs gradual",
                "action_type": "HOTL",
            },
            {
                "step_number": 2,
                "description": "Verificar health check da API de ingestão — se OK, causa é upstream (HAProxy/DNS/rede)",
                "action_type": "HOTL",
                "command": "curl -sf http://localhost:8000/health",
            },
            {
                "step_number": 3,
                "description": "Confirmar estado do HAProxy via docker compose ps ou systemctl status",
                "action_type": "HOTL",
                "command": "docker compose ps haproxy",
            },
            {
                "step_number": 4,
                "description": "Coletar evidências do crash antes do restart (logs, dmesg) — preservar para RCA",
                "action_type": "HOTL",
                "command": "sudo journalctl -u haproxy --since '15 minutes ago' > /tmp/haproxy-crash.log",
            },
            {
                "step_number": 5,
                "description": "Apresentar evidências ao on-call e solicitar aprovação para restart do HAProxy",
                "action_type": "HITL",
            },
            {
                "step_number": 6,
                "description": "Executar restart do HAProxy",
                "action_type": "HOTL",
                "command": "docker compose restart haproxy",
            },
            {
                "step_number": 7,
                "description": "Validar retorno do RPS ao baseline histórico e normalização de 5xx e P99",
                "action_type": "HOTL",
            },
        ],
        "lessons_learned": [
            "Alerta de RPS = 0 por > 60s inexistente — criar alerta CRITICAL imediato com notificação ao on-call",
            "HAProxy sem auto-restart configurado — adicionar restart: always no docker-compose.yml ou Restart=always no systemd",
            "Ponto único de falha (SPOF) no load balancer — avaliar segunda instância HAProxy em modo active-passive",
            "MTTD de 5min com outage total — padrão RPS=0 + API OK é diagnóstico suficiente para restart imediato com HITL",
            "Crash por SIGSEGV em libssl.so.3 — investigar versão da biblioteca e atualizar ou fixar versão estável",
        ],
        "metric_snapshots": [
            {
                "phase": "detection",
                "rps": 0.0,
                "p99_ms": None,
                "error_rate_5xx_pct": None,
            },
            {
                "phase": "recovery",
                "rps": 295.0,
                "p99_ms": 310.0,
                "error_rate_5xx_pct": 0.2,
            },
        ],
        "precursor_signals": [
            "Nenhum sinal precursor detectado — crash abrupto por SIGSEGV sem degradação progressiva prévia",
        ],
    },
]


# ---------------------------------------------------------------------------
# Ingestion logic
# ---------------------------------------------------------------------------

async def seed_direct() -> None:
    """Ingest directly via app services — requires Qdrant on localhost:6333."""
    import sys
    sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0] + "/Knowledge-Base")

    from app.services.embeddings import EmbeddingService
    from app.services.ingestion import incident_to_chunks
    from app.services.qdrant_service import QdrantService
    from qdrant_client import AsyncQdrantClient

    print("Inicializando EmbeddingService (all-MiniLM-L6-v2)...")
    embeddings = EmbeddingService()

    print("Conectando ao Qdrant em localhost:6333...")
    qdrant = QdrantService(AsyncQdrantClient(url="http://localhost:6333"))
    await qdrant.ensure_collection()
    print("Coleção 'incidents' pronta.\n")

    from uuid import uuid4

    total_chunks = 0
    for incident_data in INCIDENTS:
        from app.models.chunk import IncidentIngestRequest
        incident = IncidentIngestRequest(**incident_data)
        chunks = incident_to_chunks(incident)

        print(f"  → {incident.incident_id}: {len(chunks)} chunks — embedando em batch...")
        vectors = await embeddings.embed_batch([c[0] for c in chunks])

        chunk_ids = []
        for (content, metadata), vector in zip(chunks, vectors):
            chunk_id = str(uuid4())
            await qdrant.upsert(chunk_id, vector, content, metadata)
            chunk_ids.append(chunk_id)

        total_chunks += len(chunk_ids)
        print(f"     ✓ {len(chunk_ids)} chunks armazenados")

    print(f"\n{'─'*50}")
    print(f"Ingestão concluída: {len(INCIDENTS)} incidentes, {total_chunks} chunks no total.")


async def seed_via_http(kb_url: str) -> None:
    """Ingest via HTTP API — requires KB service running."""
    import httpx

    async with httpx.AsyncClient(base_url=kb_url, timeout=120.0) as client:
        total_chunks = 0
        for incident_data in INCIDENTS:
            inc_id = incident_data["incident_id"]
            print(f"  → POST /kb/ingest/incident ({inc_id})...")
            response = await client.post("/kb/ingest/incident", json=incident_data)
            response.raise_for_status()
            data = response.json()
            total_chunks += data["chunks_created"]
            print(f"     ✓ {data['chunks_created']} chunks armazenados")

        print(f"\n{'─'*50}")
        print(f"Ingestão concluída: {len(INCIDENTS)} incidentes, {total_chunks} chunks no total.")


if __name__ == "__main__":
    kb_url = os.getenv("KB_URL", "http://localhost:8002")
    use_direct = os.getenv("USE_DIRECT", "0") == "1"

    print("=" * 50)
    print("Knowledge Base — Seed: 4 incidentes históricos")
    print("=" * 50)
    for inc in INCIDENTS:
        print(f"  {inc['incident_id']}: {inc['title']}")
    print()

    if use_direct:
        print("Modo: direto (sem HTTP)\n")
        asyncio.run(seed_direct())
    else:
        print(f"Modo: HTTP → {kb_url}\n")
        asyncio.run(seed_via_http(kb_url))
