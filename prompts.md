# Prompts da Sessão

Registro cronológico de todos os prompts desta sessão de trabalho com Claude Code.

---

1. `/skills`
2. porque não está sendo reconhecido o meu skill que está em .claude/skill dentro deste projeto?
3. sim, move o arquivo para o lugar certo
4. inclua no glossario do meu skill Agentic-AI-2-Incident-Response a explicação do percentil P50, P95 e P99, e a importância deles em ambientes de missão crítica.
5. inclua no glossario do meu skill Agentic-AI-2-Incident-Response a explicação sobre os Goldens Signals de SRE (Latency, Error, Traffic and Saturation), e a importância de medir eles em ambientes de missão crítica.
6. inclua também SLO, SLA e Error Budget no glossário
7. commit this
8. push it
9. create a remote repo and push it
10. `brew install gh`
11. `! gh auth login`
12. podemos seguir com a minha configuracao /Users/valdomirosouza/.gitconfig?
13. já fiz o login, pode seguir
14. adiciona um README ao projeto
15. adiciona um `.env.example` ao projeto
16. adiciona um `.gitignore` ao projeto
17. cria um Docker Compose para rodar o projeto localmente
18. testa o docker compose
19. Docker Desktop está aberto
20. pare o Redis na porta 6379, ele foi usado apenas para um teste.
21. sim, pode parar
22. reverte o Redis para 6379:6379 no docker-compose
23. pare o docker compose
24. adiciona a instrução `docker compose up --build` no README
25. adiciona instruções de como parar o compose no README
26. roda os testes do projeto
27. corrige o warning do `datetime.utcnow()`
28. adiciona o `.venv` no `.gitignore`
29. push it
30. o meu projeto já tem um API health-check exposta, para conseguirmos monitorar a saúde das API, REDIS e outros componentes? Se não tiver, implemente.
31. adiciona o endpoint `/health` no README
32. commit this
33. push it
34. adiciona instruções de como rodar os testes no README
35. roda os testes
36. commit this
37. rode testes SAST e DAST no projeto
38. adiciona instruções de SAST e DAST no README
39. roda os testes
40. commit this
41. adiciona instruções de SAST e DAST no README
42. roda os testes
43. commit this
44. Valide se os logs estão com a implementação das melhores práticas de Metricas, Logs e Traces. Caso não estejam, implemente.
45. atualiza o README com as instruções de observabilidade
46. roda os testes
47. commit this
48. roda o docker compose e testa os endpoints de observabilidade
49. commit this
50. As melhores praticas dos Golden Signals (Metrics, Errors, Saturation and Latency) foram implementadas? Em caso negativo, implemente!
51. atualiza o README com o endpoint `/metrics/saturation`
52. roda os testes
53. commit this
54. rode testes SAST e DAST no projeto
55. commit this
56. roda o docker compose e testa o endpoint `/metrics/saturation`
57. commit this
58. Agora precisamos gerar a documentação visual do projeto com uma big picture da arquitetura.
59. Agora compile no arquivo prompts.md todos os meus prompts desta sessão.
60. agora vamos implementar o agente de IA
61. push it
62. atualiza o README com o novo módulo
63. rode testes SAST e DAST no projeto
64. commit this
65. Agora compile e adicione no arquivo prompts.md todos os novos prompts desde a ultima atualizaçao nesta sessão.
66. roda o docker compose e testa o endpoint `/analyze`
67. já fiz o login, pode seguir
68. Onde eu devo ir no site da Anthropic para criar a API KEY?
69. Arquivo .env criado com a API KEY. Favor incluir no .gitignore para não copiar para o repositorio o arquivo .env
70. já fiz o login, pode seguir
71. A documentacao já foi atualizada?
72. commit this
73. Agora compile no arquivo prompts.md todos os novos prompts desta sessão.
74. O meu Skill e harness estão atualizados?
75. commit this
76. Tem como montar um novo diagrama mais visual e didatico para pessoas leigas no tema, mostrando desde a inserção do log na API até o trabalho do agentes?
77. Agora compile no arquivo prompts.md todos os novos prompts desta sessão.
78. roda os testes
79. Todas as ferramentas, tecnologias de programação e bibliotecas estão documentadas? Em caso negativo documente.
80. commit this
81. Agora compile no arquivo prompts.md todos os novos prompts desta sessão.
82. Fiz alguns ajustes no meu Skill. Avalie ele e diga se preciso mudar alguma coisa.
83. Adiciona as seções que faltam
84. Faz o commit dessas mudanças
85. Faz o push
86. Testa o skill com um cenário de incidente
87. O P99 está em 1.800ms e temos aumento de erros 5xx
88. Sim, fiz um deploy há 1 hora
89. Sim, autorizo o rollback
90. Pods Healthy. Gere o post-mortem
91. Faz o commit do post-mortem
92. Faz o push
93. Testa o skill com outro cenário
94. Redis com 90% de memória, alertas de saturação disparando
95. maxmemory-policy é noeviction, RESPONSE_TIME_MAX_ENTRIES está no padrão
96. Sim, autorizo
97. Gera o post-mortem
98. Faz o commit e push
99. Testa o skill com mais um cenário e use o novo template de postmortem no final
100. Taxa de erros 4xx acima de 25%, endpoint `/api/checkout`
101. Código 401, deploy no serviço de autenticação há 2 horas
102. Não, pode fazer o rollback
103. já estão healthy
104. Adiciona os 3 cenários de incidente ao README
105. Testa o skill com mais um cenário
106. RPS zerado nos últimos 5 minutos, possível outage
107. health check responde, não houve deploy
108. HAProxy está parado
109. Sim, autoriza
110. RPS voltou ao normal, gera o post-mortem
111. Skill, Readme, glossário e documentação estão atualizados?
112. Adiciona INC-004 ao README
113. vale adicionar os INC de 001 até 004 ao Skill?
114. Adiciona os 4 cenários de incidente no CLAUDE.md
115. Agora compile no arquivo prompts.md todos os novos prompts desta sessão.
116. Rode o TDD, SAST e DAST de todo os projeto.
117. Faz o commit e push
118. Agora compile no arquivo prompts.md todos os novos prompts desta sessão.
119. Adicione esta nova visão de arquitetura no Architecture do README.md flowchart LR [...] mas antes de inserir valide e melhore.
120. commit this
121. push it
122. update the session prompts log
123. fix um ajuste no README.md para corrigir o código mermaid do ultimo diagrama de arquitetura adicionado.
124. commit this
125. push it
126. update the session prompts log
127. Evoluindo o meu AgenticAI-2-Incident-Response, preciso criar uma base de conhecimento dos incidentes em um banco de dados vetorial. Onde devemos armazenar os trechos de logs usados como evidências das falhas históricas, os comandos executados para recuperação dos serviços e os arquivos de postmortem criados para cada caso. Sugira outras informações e/ou dados importantes para armazenarmos e criarmos uma KB robusta.
128. Implemente o módulo Knowledge-Base com Qdrant
129. Agora ingesta os 4 incidentes históricos na KB
130. Faz um commit com tudo isso
131. Atualiza o CLAUDE.md com o novo módulo
132. Integra a KB no Incident-Response-Agent
133. Atualiza o CLAUDE.md com a integração
134. Atualiza o README com a arquitetura dos 3 módulos
135. Faz um push pro GitHub
136. Atualiza o Glossário e inclua "Vector Database", Postmortem e KB (Knowledge Base), e outros termos que julgar necessário pela inclusão do Vector Database e KB no projeto.
137. faz push pro GitHub
138. Atualiza o prompts.md com as sessões de hoje
139. Avalie se o código do projeto está seguindo as melhores práticas de desenvolvimento seguro, seguindo o guideline de OWASP e outros frameworks de segurança reconhecidos globalmente.
140. Faz o commit e push dessas correções
141. Atualiza o prompts.md com as sessões de hoje
142. Rode os testes de TDD, SAST e DAST em todo o projeto
143. Atualiza o prompts.md com as sessões de hoje
