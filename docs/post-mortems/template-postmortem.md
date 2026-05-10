# Post-Mortem: [CÓDIGO-ID] [Título Resumido do Incidente]

---

## Informações Gerais

| Campo                  | Valor                           |
| :--------------------- | :------------------------------ |
| **Status**             | Ex: Em Aprovação / Concluído    |
| **Projeto**            | Nome do Projeto ou Departamento |
| **Plataforma/Produto** | Nome do Produto Afetado         |
| **Proprietário**       | Cargo ou Nome do Responsável    |
| **Prioridade**         | Alta / Média / Baixa            |
| **Data de Criação**    | YYYY-MM-DD                      |

---

## Resumo do Incidente

> Descreva em 2–4 frases o que ocorreu, qual foi o impacto percebido pelos usuários e a causa técnica principal identificada.

---

## Cronologia

**Data: YYYY-MM-DD**

| Horário | Evento                                                                  |
| :------ | :---------------------------------------------------------------------- |
| HH:MM   | Início da mobilização das equipes                                       |
| HH:MM   | [Ação de mitigação ou descoberta]                                       |
| HH:MM   | [Ação de mitigação ou descoberta]                                       |
| HH:MM   | [Ação de mitigação ou descoberta]                                       |
| HH:MM   | [Ação de mitigação ou descoberta]                                       |
| HH:MM   | [Ação de mitigação ou descoberta]                                       |
| HH:MM   | [Ação de mitigação ou descoberta]                                       |
| HH:MM   | [Ação de mitigação ou descoberta]                                       |
| HH:MM   | Normalização do serviço                                                 |
| HH:MM   | Desmobilização da equipe de crise e definição do plano de monitoramento |

---

## Análise de Causa Raiz (Blameless Root Cause)

> Foque em causas sistêmicas, não em falhas individuais.

- **[Causa 1]:** Descrição detalhada da causa técnica ou de processo.
- **[Causa 2]:** Descrição detalhada da causa técnica ou de processo.
- **[Causa 3]:** Descrição detalhada da causa técnica ou de processo.

---

## Impactos

| Dimensão         | Descrição                                            |
| :--------------- | :--------------------------------------------------- |
| **Operacional**  | Quais times ou processos foram afetados e como.      |
| **Integridade**  | Dados corrompidos, duplicados ou perdidos.           |
| **Financeiro**   | Estimativa de impacto financeiro, se aplicável.      |
| **Reputacional** | Impacto em SLA, clientes ou parceiros, se aplicável. |

---

## Resposta e Recuperação

| Fase           | Ação Executada                                                                     |
| :------------- | :--------------------------------------------------------------------------------- |
| **Mitigação**  | Ação imediata para reduzir o impacto sem resolver a causa raiz.                    |
| **Remediação** | Ação para corrigir os efeitos colaterais do incidente (ex: deduplicação de dados). |
| **Otimização** | Correção da causa raiz técnica (ex: reescrita de queries, rollback).               |

---

## Lições Aprendidas e Próximos Passos

| Área                     | Aprendizado / Ação                                | Prazo      | Responsável |
| :----------------------- | :------------------------------------------------ | :--------- | :---------- |
| Design de Infraestrutura | [Descreva a melhoria estrutural identificada]     | YYYY-MM-DD | [Time]      |
| Segregação de Recursos   | [Descreva a melhoria de isolamento identificada]  | YYYY-MM-DD | [Time]      |
| Monitoramento            | [Descreva o alerta ou métrica a ser implementada] | YYYY-MM-DD | [Time]      |
| Plano de Ação            | [Revisão técnica ou refatoração pendente]         | YYYY-MM-DD | [Time]      |
