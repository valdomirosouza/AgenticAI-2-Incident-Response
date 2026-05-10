# Post-Mortem: INC-003 Regressão no Serviço de Autenticação — 401 no /api/checkout

---

## Informações Gerais

| Campo                  | Valor                         |
| :--------------------- | :---------------------------- |
| **Status**             | Concluído                     |
| **Projeto**            | AgenticAI-2-Incident-Response |
| **Plataforma/Produto** | API de Checkout               |
| **Proprietário**       | Time SRE                      |
| **Prioridade**         | Alta                          |
| **Data de Criação**    | 2026-05-10                    |

---

## Resumo do Incidente

Deploy realizado no serviço de autenticação há ~2 horas introduziu uma regressão na validação de tokens JWT, fazendo com que tokens válidos passassem a ser rejeitados com `401 Unauthorized`. O endpoint `POST /api/checkout` — jornada crítica de finalização de compra — atingiu 25% de taxa de erros 4xx, impactando diretamente a conversão de vendas. O rollback para a versão anterior do auth service restaurou o comportamento esperado em ~15 minutos após a detecção.

---

## Cronologia

**Data: 2026-05-10**

| Horário    | Evento                                                                     |
| :--------- | :------------------------------------------------------------------------- |
| T+0h       | Deploy realizado no serviço de autenticação                                |
| T+~2h      | Detecção: taxa de 4xx em 25% no endpoint `/api/checkout`                   |
| T+~2h05min | Copilot acionado — contexto coletado, diagnóstico iniciado                 |
| T+~2h08min | Código `401` identificado como dominante nas métricas de status codes      |
| T+~2h10min | Causa raiz identificada: correlação temporal com deploy do auth service    |
| T+~2h11min | Confirmação de ausência de rotação de chaves ou migração de banco de dados |
| T+~2h12min | Rollback autorizado (HITL) e executado no auth service                     |
| T+~2h15min | Pods da versão anterior healthy — taxa de 401 normalizada                  |
| T+~2h17min | Taxa de 4xx no `/api/checkout` retorna abaixo de 20%                       |
| T+~2h20min | Desmobilização da equipe de crise e definição do plano de monitoramento    |

---

## Análise de Causa Raiz (Blameless Root Cause)

> Foque em causas sistêmicas, não em falhas individuais.

- **Ausência de testes de contrato no pipeline CI/CD:** O deploy do auth service não incluía testes que validassem a compatibilidade dos tokens emitidos antes e após o deploy, permitindo que uma regressão silenciosa chegasse à produção.

- **Falta de smoke test pós-deploy em endpoints críticos:** Não havia verificação automática de que o `/api/checkout` continuava retornando `2xx` imediatamente após o deploy do auth service, aumentando o MTTD para ~2 horas.

- **Ausência de alerta de 4xx por endpoint:** O sistema de alertas monitorava a taxa global de erros, mas não a taxa por endpoint crítico — o impacto no checkout poderia ter sido detectado em minutos com alertas granulares.

---

## Impactos

| Dimensão         | Descrição                                                                                                                                      |
| :--------------- | :--------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operacional**  | Time de suporte sobrecarregado com reclamações de usuários incapazes de finalizar compras durante ~15 minutos após a detecção.                 |
| **Financeiro**   | Todas as tentativas de checkout durante o período retornaram erro — impacto direto em receita proporcional ao volume de transações do período. |
| **Integridade**  | Nenhuma inconsistência de dados identificada — 401 rejeita antes de qualquer escrita.                                                          |
| **Reputacional** | Jornada crítica de compra comprometida — potencial impacto em NPS e confiança na plataforma.                                                   |

---

## Resposta e Recuperação

| Fase           | Ação Executada                                                                                                          |
| :------------- | :---------------------------------------------------------------------------------------------------------------------- |
| **Mitigação**  | Coleta imediata de telemetria para confirmar escopo do impacto (sistêmico vs. isolado no checkout).                     |
| **Remediação** | Rollback do deploy do auth service para a versão anterior, restaurando a validação correta de tokens.                   |
| **Otimização** | Validação de ausência de rotação de chaves e migração de banco antes de aprovar o rollback, garantindo execução segura. |

---

## Lições Aprendidas e Próximos Passos

| Área                  | Aprendizado / Ação                                                                                                                      | Prazo      | Responsável            |
| :-------------------- | :-------------------------------------------------------------------------------------------------------------------------------------- | :--------- | :--------------------- |
| Pipeline CI/CD        | Adicionar testes de contrato de token JWT (emissão e validação) no pipeline do auth service — bloquear deploy se compatibilidade falhar | 2026-05-17 | Engenharia             |
| Monitoramento         | Criar alerta granular: taxa de 4xx por endpoint crítico (`/api/checkout`, `/api/login`) > 5% por 2min → CRITICAL                        | 2026-05-17 | SRE                    |
| Smoke Test Pós-Deploy | Implementar smoke test automático após deploy do auth service: validar que endpoints dependentes retornam `2xx` com token real          | 2026-05-24 | Engenharia             |
| Plano de Ação         | Revisão técnica do diff do deploy revertido para identificar a mudança exata que causou a regressão de validação de token               | 2026-05-12 | Engenharia / Auth Team |
