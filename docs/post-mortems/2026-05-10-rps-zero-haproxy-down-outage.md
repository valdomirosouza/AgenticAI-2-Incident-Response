# Post-Mortem: INC-004 Outage Total — HAProxy Parado, RPS Zerado por 5 Minutos

---

## Informações Gerais

| Campo                  | Valor                         |
| :--------------------- | :---------------------------- |
| **Status**             | Concluído                     |
| **Projeto**            | AgenticAI-2-Incident-Response |
| **Plataforma/Produto** | Plataforma Completa           |
| **Proprietário**       | Time SRE                      |
| **Prioridade**         | Alta                          |
| **Data de Criação**    | 2026-05-10                    |

---

## Resumo do Incidente

O processo HAProxy encerrou inesperadamente, zerando todo o tráfego externo por pelo menos 5 minutos antes da detecção. Como HAProxy é o único ponto de entrada da plataforma, sua indisponibilidade isolou completamente os usuários de todos os serviços. O health check da API de ingestão respondia normalmente, indicando que a causa estava upstream — no load balancer, não na aplicação. O restart do HAProxy restaurou o tráfego em menos de 5 segundos após a execução.

---

## Cronologia

**Data: 2026-05-10**

| Horário  | Evento                                                                        |
| :------- | :---------------------------------------------------------------------------- |
| T+0min   | HAProxy encerra inesperadamente — RPS cai a zero                              |
| T+~5min  | Alerta de RPS = 0 disparado — possível outage detectado                       |
| T+~6min  | Copilot acionado — contexto coletado, diagnóstico iniciado                    |
| T+~8min  | Health check da API responde — causa upstream identificada como mais provável |
| T+~10min | HAProxy confirmado parado via `systemctl status` / `docker compose ps`        |
| T+~11min | Evidências pré-restart coletadas (logs, dmesg)                                |
| T+~12min | Restart do HAProxy autorizado (HITL) e executado                              |
| T+~13min | HAProxy ativo — RPS retorna ao baseline histórico                             |
| T+~15min | Taxa de 5xx e P99 dentro dos thresholds — incidente encerrado                 |
| T+~20min | Desmobilização da equipe de crise e definição do plano de monitoramento       |

---

## Análise de Causa Raiz (Blameless Root Cause)

> Foque em causas sistêmicas, não em falhas individuais.

- **Ausência de supervisão automática do processo HAProxy:** O processo encerrou sem que nenhum mecanismo de watchdog ou auto-restart (ex: `systemd` com `Restart=always`, ou restart policy no Docker Compose) o recuperasse automaticamente, prolongando o impacto desnecessariamente.

- **MTTD elevado por falta de alerta granular de RPS:** O incidente existia há pelo menos 5 minutos antes da detecção. Um alerta de RPS = 0 por mais de 60s teria reduzido o MTTD de ~5min para menos de 1min.

- **Ponto único de falha (SPOF) no load balancer:** A arquitetura atual possui uma única instância de HAProxy sem redundância (active-passive ou active-active), tornando sua falha um outage total para todos os usuários.

---

## Impactos

| Dimensão         | Descrição                                                                                                             |
| :--------------- | :-------------------------------------------------------------------------------------------------------------------- |
| **Operacional**  | Todas as jornadas de usuário interrompidas durante ~8min (5min antes da detecção + ~3min de resposta).                |
| **Financeiro**   | Todas as transações e operações bloqueadas durante o período — impacto proporcional ao volume histórico do intervalo. |
| **Integridade**  | Nenhuma inconsistência de dados — HAProxy não persiste estado transacional.                                           |
| **Reputacional** | Outage total visível para todos os usuários ativos no período.                                                        |

---

## Resposta e Recuperação

| Fase           | Ação Executada                                                                                             |
| :------------- | :--------------------------------------------------------------------------------------------------------- |
| **Mitigação**  | Identificação imediata da causa upstream via health check da API — descartou crash de aplicação em < 3min. |
| **Remediação** | Coleta de evidências (logs do HAProxy, dmesg) para identificar causa do crash antes do restart.            |
| **Otimização** | Restart do HAProxy com janela de impacto de ~5s, seguido de validação de RPS, 5xx e P99.                   |

---

## Lições Aprendidas e Próximos Passos

| Área                 | Aprendizado / Ação                                                                                               | Prazo      | Responsável    |
| :------------------- | :--------------------------------------------------------------------------------------------------------------- | :--------- | :------------- |
| Monitoramento        | Criar alerta: RPS = 0 por mais de 60s → CRITICAL imediato com notificação ao on-call                             | 2026-05-17 | SRE            |
| Resiliência          | Configurar política de auto-restart no HAProxy: `Restart=always` (systemd) ou `restart: always` (Docker Compose) | 2026-05-17 | Engenharia     |
| Alta Disponibilidade | Avaliar implantação de segunda instância HAProxy em modo active-passive para eliminar SPOF                       | 2026-05-24 | Engenharia/SRE |
| Plano de Ação        | Investigar a causa raiz do crash do HAProxy (OOM, sinal externo, bug) com base nos logs coletados                | 2026-05-12 | SRE            |
