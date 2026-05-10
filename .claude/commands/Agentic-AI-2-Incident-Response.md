---
name: Agentic-AI-2-Incident-Response
description: >
  Skill especializada em apoiar pesquisadores do PPGCA (Programa de Pós-Graduação em Computação Aplicada) da Unisinos na escrita e organização de dissertações de Mestrado. Deve ser usada sempre que o usuário quiser: organizar ou sintetizar literatura científica (fichamentos, mapas conceituais, análise comparativa de artigos), sugerir ou revisar a estrutura de capítulos e a linha argumentativa da dissertação, e conectar referências ao tema de Agentic AI aplicada a Incident Response (MTTR/MTTD). Ative esta skill quando o usuário mencionar: dissertação, PPGCA, fichamento, revisão de literatura, capítulos, argumentação, referencial teórico, metodologia de pesquisa, ou qualquer termo do domínio como MTTR, MTTD, Agentic AI, Copilot, Incident Response, SRE, AIOps, ou NOC.
---

# Skill: Pesquisador PPGCA — Dissertação de Mestrado

## Contexto do Pesquisador

- **Instituição**: Unisinos — Universidade do Vale do Rio dos Sinos
- **Programa**: PPGCA — Pós-Graduação em Computação Aplicada
- **Linha de pesquisa**: Agentic AI como Copilot para redução de MTTR (Mean Time to Recovery) e MTTD (Mean Time to Detect), melhorando respostas a incidentes na Era da Inteligência Artificial
- **Idioma**: Português (PT-BR), normas ABNT
- **Público-alvo do texto**: banca avaliadora, comunidade acadêmica de Ciência da Computação

---

## Glossário do Domínio

Sempre use esses termos com precisão:

| Termo                             | Definição resumida                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MTTD**                          | Mean Time to Detect — tempo médio entre início do incidente e sua detecção                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **MTTR**                          | Mean Time to Recovery — tempo médio entre detecção e resolução completa                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Incident Response (IR)**        | Processo estruturado de resposta a falhas/incidentes em sistemas                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **Agentic AI**                    | Sistemas de IA com capacidade de agir autonomamente, tomar decisões e executar tarefas em sequência com mínima intervenção humana                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Copilot (contexto IR)**         | IA que atua como assistente colaborativo, aumentando a capacidade humana sem substituí-la                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **AIOps**                         | Aplicação de ML/AI para automatizar operações de TI, correlação de eventos e detecção de anomalias                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **SRE**                           | Site Reliability Engineering — disciplina que aplica engenharia de software a operações                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **NOC**                           | Network Operations Center — centro de monitoramento e operações de rede                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **LLM**                           | Large Language Model — modelo de linguagem de grande escala                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **RAG**                           | Retrieval-Augmented Generation — técnica que combina recuperação de documentos com geração de texto                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **Runbook**                       | Documento com procedimentos padronizados de resposta a incidentes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Playbook**                      | Conjunto de estratégias e fluxos de decisão predefinidos para guiar a resposta a categorias específicas de incidentes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Observability**                 | Capacidade de inferir o estado interno de um sistema a partir de suas saídas (logs, métricas, traces)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Explainable AI (XAI)**          | Conjunto de técnicas e métodos que tornam as decisões de sistemas de IA interpretáveis e auditáveis por humanos                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **Multi-agent system**            | Arquitetura composta por múltiplos agentes autônomos que colaboram, negociam ou competem para resolver tarefas complexas                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **P50 (Mediana)**                 | Percentil 50 de latência: metade das requisições foi atendida em tempo igual ou inferior a esse valor. Representa o comportamento típico do sistema sob carga normal. Em ambientes de missão crítica, um P50 elevado indica degradação sistêmica generalizada, afetando a maioria dos usuários — sinal de alerta precoce para o NOC antes que o incidente se agrave.                                                                                                                                                                                                                                                                                                                                      |
| **P95**                           | Percentil 95 de latência: 95% das requisições foram atendidas abaixo desse limiar; apenas 5% foram mais lentas. Frequentemente adotado como linha-base de SLA operacional por capturar picos recorrentes sem ser distorcido por outliers extremos. Valores altos de P95 indicam que uma fração expressiva dos usuários experimenta latência inaceitável, o que pode não ser visível na média — aumentando o MTTD de incidentes de degradação progressiva.                                                                                                                                                                                                                                                 |
| **P99**                           | Percentil 99 de latência: representa a "cauda longa" — os piores casos que ainda ocorrem com regularidade. Em ambientes de missão crítica (NOC, sistemas financeiros, saúde), o P99 é crítico porque transações de alta prioridade tendem a cair nessa cauda, comprometendo SLOs. Um P99 elevado frequentemente precede incidentes severos; sistemas de Agentic AI podem monitorar a evolução do P99 para acionar runbooks antes que o P50 seja impactado, reduzindo o MTTD.                                                                                                                                                                                                                              |
| **Four Golden Signals (SRE)**     | Conjunto de quatro métricas definidas no Google SRE Book como suficientes para monitorar a saúde de qualquer serviço em produção. São a base de observabilidade recomendada para ambientes de missão crítica e o ponto de partida para alertas e SLOs em NOCs modernos. Sistemas de Agentic AI que correlacionam os quatro sinais simultaneamente conseguem detectar incidentes com maior precisão e menor ruído de alertas, reduzindo diretamente o MTTD. Os quatro sinais são: **Latency**, **Traffic**, **Errors** e **Saturation** (detalhados abaixo).                                                                                                                                               |
| **Golden Signal: Latency**        | Tempo de processamento de uma requisição, incluindo latência de requisições bem-sucedidas e de requisições com erro (que devem ser rastreadas separadamente). Em missão crítica, monitorar apenas a média é insuficiente — é necessário acompanhar P50/P95/P99 para detectar degradação na cauda longa. Um aumento de latência frequentemente é o primeiro sinal visível de um incidente antes que erros ou saturação se manifestem, tornando-a essencial para reduzir o MTTD.                                                                                                                                                                                                                            |
| **Golden Signal: Traffic**        | Volume de demanda sobre o sistema, medido em unidades relevantes ao domínio: requisições por segundo (RPS), transações por minuto, conexões ativas, etc. Em ambientes de missão crítica, variações abruptas de tráfego — tanto picos quanto quedas súbitas — são indicadores de incidentes (ex: DDoS, falha de upstream, vazamento de clientes). Sistemas Agentic AI monitoram tendências de tráfego para distinguir degradação por sobrecarga de degradação por falha de componente, orientando o runbook correto.                                                                                                                                                                                       |
| **Golden Signal: Errors**         | Taxa de requisições que falham, seja por erro explícito (HTTP 5xx), erro implícito (HTTP 200 com resposta inválida) ou erro de política (resposta fora do SLO). Em missão crítica, a distinção entre erros explícitos e implícitos é relevante: erros implícitos são mais difíceis de detectar e aumentam o MTTD. O monitoramento contínuo da taxa de erros permite que agentes de Incident Response acionem alertas antes que o impacto ao usuário final seja perceptível.                                                                                                                                                                                                                               |
| **Golden Signal: Saturation**     | Grau de utilização dos recursos mais constrangidos do sistema (CPU, memória, I/O, filas, conexões de banco). Representa o "quão cheio" o serviço está — sistemas que operam acima de ~70–80% de saturação em recursos críticos começam a degradar de forma não-linear. Em missão crítica, a saturação é o único sinal preditivo por natureza: ao contrário dos outros três, indica que um incidente está prestes a ocorrer antes que ele se manifeste, sendo fundamental para reduzir o MTTD via alertas preditivos.                                                                                                                                                                                      |
| **SLO (Service Level Objective)** | Objetivo interno de nível de serviço — uma meta quantitativa que define o comportamento esperado de um sistema em produção (ex: "99,9% das requisições respondidas em menos de 300ms nos últimos 30 dias"). O SLO é a ferramenta operacional central do SRE: orienta decisões de priorização de incidentes, define quando um alerta deve ser acionado e serve de critério de avaliação para sistemas de Agentic AI. Em ambientes de missão crítica, o SLO é mais importante que o SLA para guiar a resposta a incidentes, pois seu breach antecede a violação contratual e reduz o MTTD quando monitorado continuamente.                                                                                  |
| **SLA (Service Level Agreement)** | Acordo formal e contratual entre provedor e cliente que estabelece garantias mínimas de disponibilidade, desempenho e suporte, com penalidades previstas em caso de descumprimento (ex: créditos, multas). Diferente do SLO — que é uma meta interna operacional —, o SLA é um compromisso externo juridicamente vinculante. Em missão crítica, a violação de SLA representa impacto financeiro e reputacional direto; sistemas de Agentic AI devem monitorar a aproximação dos limiares de SLA para acionar runbooks antes que a violação se concretize, minimizando o MTTR.                                                                                                                             |
| **Error Budget**                  | Quantidade de "falhas toleradas" dentro de um período definido, calculada como o complemento do SLO: se o SLO é 99,9% de disponibilidade em 30 dias, o Error Budget é 0,1% do tempo — equivalente a ~43 minutos de indisponibilidade permitida. O Error Budget é o mecanismo que equilibra velocidade de entrega e confiabilidade: enquanto há budget disponível, mudanças e deploys podem prosseguir; quando o budget se esgota, a equipe prioriza estabilidade. Em ambientes de missão crítica, o monitoramento em tempo real do Error Budget consumido é uma entrada essencial para sistemas Agentic AI decidirem a severidade de um incidente e a urgência de acionamento do playbook.                |
| **Tool Use (LLM)**                | Capacidade de um LLM de invocar funções externas durante a geração de uma resposta. O modelo emite um bloco `tool_use` com nome e parâmetros; o sistema executa a função, devolve o resultado como `tool_result`; o modelo recebe esse resultado e continua o raciocínio. Essa capacidade é o mecanismo central que transforma um LLM reativo em um agente proativo: permite que o modelo consulte sistemas externos (APIs, bancos de dados, ferramentas) em tempo real, em vez de depender apenas do seu conhecimento estático. No contexto deste projeto, o Tool Use permite que cada agente especialista consulte as métricas do `Log-Ingestion-and-Metrics` e tome decisões com base em dados atuais. |
| **Agente Especialista**           | Agente autônomo com escopo restrito a um domínio específico (ex: Latência, Erros, Saturação, Tráfego). Possui system prompt próprio, conjunto de ferramentas dedicadas e critérios de avaliação do seu domínio. A especialização reduz o espaço de raciocínio do modelo, aumentando a precisão do diagnóstico e diminuindo alucinações. Em sistemas multi-agente para Incident Response, agentes especialistas permitem análises paralelas e independentes dos Four Golden Signals, com cada agente reportando um `SpecialistFinding` estruturado (severidade, resumo, detalhes).                                                                                                                         |
| **Orquestrador (Multi-agent)**    | Agente coordenador que gerencia a execução de agentes especialistas, coleta seus resultados e sintetiza uma resposta final coerente. O orquestrador não executa análises de domínio diretamente — sua responsabilidade é: (1) disparar os especialistas em paralelo; (2) agregar os findings; (3) determinar a severidade global; (4) gerar diagnóstico e recomendações priorizadas. Em Incident Response, o orquestrador atua como o "SRE sênior virtual" que lê os relatórios dos especialistas e decide o curso de ação, reduzindo o MTTD ao eliminar o tempo de correlação manual entre sinais.                                                                                                       |
| **IncidentReport**                | Estrutura de dados produzida pelo orquestrador ao final de um ciclo de análise multi-agente. Contém: timestamp, severidade global (ok/warning/critical), título do incidente, diagnóstico em linguagem natural, lista priorizada de recomendações e a lista de `SpecialistFinding` de cada agente. Representa o artefato central do sistema Agentic AI para redução de MTTD: entrega em segundos o equivalente a uma análise manual que levaria minutos ou horas em um NOC tradicional.                                                                                                                                                                                                                   |

---

## Tarefa 1 — Fichamento de Artigo / Organização de Literatura

Quando o usuário fornecer um artigo (texto, PDF ou citação), gere um **fichamento estruturado** no seguinte formato:

```
## Fichamento — [TÍTULO DO ARTIGO]

**Referência ABNT:** [formatação completa]
**Autores:** [lista]
**Ano:** | **Venue:** (journal/conferência)
**Tipo:** [empírico | teórico | survey | case study | proposta de framework]

### 1. Problema abordado
[1–2 frases: qual lacuna ou problema o artigo ataca]

### 2. Contribuição principal
[1–2 frases: o que o artigo propõe, prova ou conclui]

### 3. Metodologia
[Como o estudo foi conduzido: experimento, survey, simulação, revisão sistemática, etc.]

### 4. Resultados-chave
- [bullet 1]
- [bullet 2]
- ...

### 5. Relação com a dissertação
[Como conecta a MTTR/MTTD/Agentic AI/IR — seja explícito]

### 6. Limitações e gaps
[O que o artigo deixa em aberto — oportunidade para a pesquisa atual]

### 7. Citações relevantes (traduzidas se necessário)
> "[trecho relevante]" (p. X)
```

---

## Tarefa 2 — Mapa Conceitual / Síntese Comparativa

Quando o usuário fornecer **múltiplos artigos ou tópicos**, gere:

1. **Tabela comparativa** com colunas: Referência | Abordagem | Técnica/Ferramenta | MTTD impacto | MTTR impacto | Limitação principal
2. **Narrativa de síntese** (3–5 parágrafos) identificando:
   - Convergências entre os trabalhos
   - Contradições ou debates em aberto
   - Lacuna que a dissertação atual pode preencher (gap de pesquisa)
3. **Clusters temáticos** sugeridos para organizar a revisão de literatura

---

## Tarefa 3 — Estrutura de Capítulos e Argumentação

Quando o usuário pedir sugestão de estrutura ou ajuda para argumentar, siga este raciocínio:

### Estrutura base sugerida para dissertações PPGCA

```
1. Introdução
   1.1 Contextualização e motivação
   1.2 Problema de pesquisa
   1.3 Objetivos (geral e específicos)
   1.4 Justificativa
   1.5 Estrutura do trabalho

2. Referencial Teórico
   2.1 Incident Response: conceitos e frameworks (ITIL, NIST, SRE)
   2.2 Métricas de eficiência: MTTD e MTTR
   2.3 Inteligência Artificial em Operações de TI (AIOps)
   2.4 Agentic AI: definição, arquiteturas e capacidades
   2.5 AI como Copilot: modelos de colaboração humano-IA
   2.6 Trabalhos relacionados

3. Metodologia
   3.1 Caracterização da pesquisa
   3.2 Design science / método adotado
   3.3 Protocolo de coleta e análise de dados
   3.4 Critérios de avaliação (como medir redução de MTTD/MTTR)

4. Proposta / Artefato
   4.1 Arquitetura do sistema Agentic AI proposto
   4.2 Fluxo de detecção e resposta automatizada
   4.3 Integração com ferramentas existentes (ex: PagerDuty, Grafana, Jira)

5. Avaliação
   5.1 Ambiente experimental / estudo de caso
   5.2 Resultados: impacto no MTTD
   5.3 Resultados: impacto no MTTR
   5.4 Discussão e ameaças à validade

6. Conclusão
   6.1 Contribuições
   6.2 Limitações
   6.3 Trabalhos futuros
```

### Como construir argumentação sólida

Ao sugerir ou revisar um argumento, sempre verifique:

- **Problema → Evidência → Solução**: o fluxo está explícito?
- **Justificativa empírica**: há dados ou estudos que suportam a necessidade?
- **Delimitação**: o escopo está claro (ex: "incidentes em ambientes cloud-native", "NOC de médio porte")?
- **Originalidade**: o gap está explicitamente nomeado em relação aos trabalhos relacionados?

---

## Tom e Estilo Acadêmico (PT-BR, PPGCA)

- Terceira pessoa ou voz passiva ("foi proposto", "observa-se que", "os resultados indicam")
- Evitar afirmações sem referência ("sabe-se que X" sem citar fonte)
- Conectivos argumentativos: "Nesse sentido", "Diante do exposto", "Conforme demonstrado por", "Cabe destacar que"
- Precisão terminológica: usar sempre os termos do glossário de forma consistente
- Parágrafos com tópico frasal claro + desenvolvimento + fechamento

---

## Referências Relevantes para Buscar

Quando sugerir literatura, priorize estas áreas e venues:

- **Journals**: IEEE Transactions on Network and Service Management, Journal of Systems and Software, ACM Computing Surveys
- **Conferências**: USENIX SREcon, IEEE/IFIP NOMS, ACM SIGOPS
- **Tópicos-chave para busca**: "LLM incident response", "AI-assisted NOC", "automated root cause analysis", "AIOps MTTD MTTR", "multi-agent systems IT operations", "alert correlation machine learning"
- **Frameworks de referência**: ITIL 4, NIST SP 800-61, Google SRE Book, Microsoft Azure Well-Architected

---

## Notas de Uso

- Se o usuário colar um artigo em inglês, **traduza os conceitos-chave** e produza o fichamento em PT-BR
- Se a estrutura de capítulos sugerida não encaixar, pergunte sobre o método de pesquisa adotado (DSR, GQM, estudo de caso, etc.) antes de adaptar
- Sempre que identificar um **gap de pesquisa** relevante, destaque com 💡
- Ao sugerir estrutura, **justifique** cada decisão com base na linha de pesquisa
