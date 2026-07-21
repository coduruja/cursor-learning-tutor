# Learning Tutor (Cursor Plugin)

Tutor leve: calibra explicações ao seu nível, captura lacunas conceituais na
fila, mantém stack/candidatos por projeto, e só aprofunda pesquisa quando você
pede.

## Uso rápido

| Ação | Como |
|---|---|
| Chat normal | Classifica intent; “o que é X?” → explica + `want` automático |
| Registrar na mão | `/study-log` |
| Raio-x / onboarding | `/study-plan` |
| Sondagem (perguntas-teste) | `/study-probe` |
| Trilha curada | `/study-deep <tópico>` (sem tópico → primeiro da fila) |

Não precisa “ligar” o tutor: a rule vem com `alwaysApply: true`.

## O que fica onde

### Global (`~/.cursor/learning/`)

| Arquivo | Papel |
|---|---|
| `profile.md` | Meta, **fila de estudo** e **coberto** |
| `cli.py` + `lib_profile.py` | CLI estável (instalada no `sessionStart`) |

### Por projeto (híbrido)

| Arquivo | Papel |
|---|---|
| `.cursor/learning/project.md` | Dados do Learning Tutor: stack, **candidatos** locais e última sondagem |

Candidatos do projeto só viram fila global via pergunta conceitual,
`/study-probe`, ou pedido explícito.
O cabeçalho identifica o arquivo como **dados**, não como rule ou instrução
para outros agentes.

```bash
python3 ~/.cursor/learning/cli.py show
python3 ~/.cursor/learning/cli.py covered --topic "Closures" --level intermediário
python3 ~/.cursor/learning/cli.py want --topic "Docker" --note "pro deploy"
python3 ~/.cursor/learning/cli.py project-show
python3 ~/.cursor/learning/cli.py project-sync --stack "Next.js;Prisma" --candidates "App Router;Prisma migrations"
```

## O que vem no plugin

| Componente | Papel |
|---|---|
| `rules/tutor.mdc` | Intent (`concept_gap` / `repo_local` / `agent_task`) + auto-want + calibração |
| `commands/study-log.md` | Registro explícito |
| `commands/study-plan.md` | Raio-x ou onboarding se vazio |
| `commands/study-probe.md` | Sondagem ativa → ajusta covered/want |
| `commands/study-deep.md` | Dispara trilha via subagent |
| `agents/study-researcher.md` | Pesquisa curada em contexto isolado |
| `hooks/*` | Injeta perfil + projeto, instala CLI, captura marcadores backup |

## Instalação

### Marketplace / Plugins
Instale **Learning Tutor** na seção User. Abra um **novo chat** depois — o
`sessionStart` copia a CLI para `~/.cursor/learning/`.

### Cópia direta (sem marketplace)
```bash
mkdir -p ~/.cursor/rules ~/.cursor/agents ~/.cursor/commands ~/.cursor/hooks ~/.cursor/learning
cp rules/tutor.mdc            ~/.cursor/rules/
cp agents/study-researcher.md ~/.cursor/agents/
cp commands/*.md              ~/.cursor/commands/
cp hooks/lib_profile.py hooks/learning_cli.py hooks/capture_learning.py hooks/inject_profile.py ~/.cursor/hooks/
cp hooks/learning_cli.py ~/.cursor/learning/cli.py
cp hooks/lib_profile.py ~/.cursor/learning/lib_profile.py
```
Aponte um `hooks.json` global para os scripts em `~/.cursor/hooks/`.

### Requisitos
- `python3` no PATH (Windows: use `python` no `hooks.json` se preciso).

## Como o registro funciona

1. **CLI** (preferida): o agente roda `python3 ~/.cursor/learning/cli.py …`
2. **Marcadores** (backup): `<!-- LEARNING-LOG … -->` / `<!-- LEARNING-WANT … -->`
   lidos pelo hook `afterAgentResponse`

Intent rápido:
- “o que é PR / HTTP / Docker?” → fila (`want`) + feedback
- “o que faz o módulo X?” → só código, sem log
- “implemente Y” → executa; log só se ensinou conceito novo

A CLI normaliza aliases (ex.: `pull request` ↔ `PR`) e ignora tópicos genéricos
ou linguagens base sozinhas.

## Caveats
- Se a CLI ainda não existir, abra um novo chat (para o `sessionStart` rodar)
  ou use a cópia direta acima.
- Se `$CURSOR_PLUGIN_ROOT` falhar na sua versão do Cursor, use a cópia direta.
- Hooks são scripts locais curtos — audite antes se quiser.
