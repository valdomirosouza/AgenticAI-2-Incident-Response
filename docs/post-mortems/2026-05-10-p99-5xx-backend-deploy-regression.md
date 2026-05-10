# Post-Mortem — P99 CRITICAL + Aumento de 5xx por Regressão de Deploy

**Data:** 2026-05-10
**Severidade:** CRITICAL → RESOLVED
**Duração do impacto:** ~1h15min
**Responsável pelo incidente:** Time SRE

---

## Resumo Executivo

Deploy realizado ~1 hora antes da detecção introduziu regressão de performance no backend HTTP. O P99 atingiu 1.800ms (threshold CRITICAL: 1.000ms), provocando cascata de timeouts no HAProxy e aumento de erros 5xx para usuários finais. Rollback para a versão anterior restaurou o comportamento esperado em ~15 minutos após detecção.

---

## Linha do Tempo

| Horário (relativo) | Evento                                                     |
| :----------------- | :--------------------------------------------------------- |
| T+0h               | Deploy da nova versão realizado                            |
| T+~1h              | Detecção: P99 = 1.800ms e aumento de 5xx reportados        |
| T+~1h05min         | Copilot acionado — contexto coletado, diagnóstico iniciado |
| T+~1h10min         | Causa raiz identificada: correlação temporal com o deploy  |
| T+~1h12min         | Rollback autorizado (HITL) e executado                     |
| T+~1h15min         | Pods da versão anterior healthy — incidente encerrado      |

---

## Diagnóstico por Golden Signal

- **Latência:** P99 = 1.800ms — 80% acima do threshold CRITICAL de 1.000ms. Regressão introduzida pelo deploy degradou o tempo de resposta da cauda longa.
- **Erros:** Taxa de 5xx em alta — HAProxy gerou erros de gateway (503/504) após backends excederem o `time_active` configurado.
- **Saturação:** Não coletada durante o incidente — lacuna identificada (ver Lições Aprendidas).
- **Tráfego:** Não coletado durante o incidente — lacuna identificada (ver Lições Aprendidas).

---

## Causa Raiz

O deploy realizado ~1 hora antes da detecção introduziu uma regressão de performance no backend. A degradação no P99 provocou cascata de timeouts no HAProxy, resultando em erros 5xx para usuários finais.

**Causa raiz provável** (a confirmar em análise do código revertido): consulta N+1, lógica síncrona bloqueante ou alteração de configuração de pool de conexões.

---

## Ações Executadas

1. **[HOTL]** Snapshot de métricas pré-rollback para documentação
2. **[HOTL]** Escalonamento defensivo de réplicas durante a transição
3. **[HITL — aprovado]** Rollback para versão anterior ao deploy
4. **[HOTL]** Validação de pods healthy e retorno ao baseline

---

## Consumo de Error Budget

| Período                              | Impacto estimado                 |
| :----------------------------------- | :------------------------------- |
| Tempo com P99 > 1.000ms              | ~1h15min                         |
| Consumo de budget mensal (SLO 99,9%) | ~1,7% do budget mensal consumido |

> Budget mensal esgotado. Prioridade de estabilidade deve se sobrepor a novos deploys até recuperação do budget.

---

## Lições Aprendidas

**O que funcionou bem:**

- Correlação temporal entre deploy e degradação identificada rapidamente
- Governança HITL/HOTL evitou ações destrutivas desnecessárias
- Rollback executado com janela de impacto controlada (~30s)

**O que precisa melhorar:**

| Gap Identificado                                      | Recomendação                                                                      |
| :---------------------------------------------------- | :-------------------------------------------------------------------------------- |
| MTTD de ~1h — degradação existia desde o deploy       | Implementar alertas automáticos de P99 > 1.000ms com disparo em < 5min            |
| Saturação e tráfego não coletados durante o incidente | Incluir `GET /metrics/saturation` e `/metrics/rps` no checklist padrão de triagem |
| Regressão não detectada antes do deploy em produção   | Adicionar teste de carga no pipeline CI/CD com validação de P99 em staging        |
| Causa raiz exata ainda não confirmada                 | Realizar análise do diff do deploy revertido antes de reabrir o branch            |

---

## Ações de Follow-up

| Prazo    | Ação                                                                                             | Responsável     |
| :------- | :----------------------------------------------------------------------------------------------- | :-------------- |
| 48h      | Analisar diff da versão revertida e identificar a linha responsável pela regressão               | Engenharia      |
| 72h      | Configurar alerta automático: P99 > 800ms por 3min consecutivos → CRITICAL                       | SRE             |
| 1 semana | Implementar smoke test de latência no pipeline CI/CD — bloquear deploy se P99 > 500ms em staging | Engenharia      |
| 1 semana | Revisar Error Budget restante e comunicar freeze de deploys não-críticos ao time                 | SRE / Tech Lead |
