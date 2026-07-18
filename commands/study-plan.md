Raio-x rápido do meu aprendizado. Sem pesquisar na web.

## Se o LEARNING-PROFILE estiver vazio / quase vazio
Não invente domínios. Faça onboarding em no máximo 3 perguntas curtas:
1. Nível geral (iniciante / intermediário / avançado)
2. Foco atual (ex: Python backend, React, CS fundamentals)
3. 1–3 tópicos que quero estudar agora

Com as respostas, rode:
```bash
python3 ~/.cursor/learning/cli.py init --level "..." --focus "..."
python3 ~/.cursor/learning/cli.py want --topic "..." --note "..."
```
Confirme o que salvou e pare. Eu posso pedir o raio-x de novo depois.

## Se houver perfil
Produza:
- **Domino** — avançado / estáveis
- **Em progresso** — intermediário, ou cobertos repetidos sem subir de nível
- **Fila** — itens abertos em "Fila de estudo"
- **Stack do projeto** — se existir `LEARNING-PROJECT` / `.cursor/learning-project.md`
- **Candidatos** — tópicos do projeto ainda não promovidos à fila global
- **Lacunas** — surgiram no contexto mas não estão na fila nem no coberto
- **Próximos 3 passos** — priorizados; cada um com 1 recurso específico

Lembre: calibração ativa = `/study-probe`. Trilha aprofundada = `/study-deep`.
Registrar na mão = `/study-log`.
