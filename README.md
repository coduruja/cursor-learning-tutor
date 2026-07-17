# Learning Tutor (Cursor Plugin)

Empacota o sistema de tutoria de aprendizado num plugin único e instalável.
Vantagem sobre o setup manual: a rule instala já ativa (`alwaysApply: true`) —
você não cola nada em Settings.

## O que vem dentro

| Componente | Caminho | Papel |
|---|---|---|
| Rule (sempre ativa) | `rules/tutor.mdc` | Calibra ao seu nível, sugere material, emite marcador de log |
| Subagent | `agents/study-researcher.md` | Pesquisa trilha de estudo aprofundada em contexto isolado |
| Command `/study-plan` | `commands/study-plan.md` | Raio-x rápido do que você já sabe |
| Command `/study-deep` | `commands/study-deep.md` | Dispara a trilha aprofundada (delega ao subagent) |
| Hooks | `hooks/hooks.json` + `.py` | Captura o marcador e injeta o perfil entre projetos |

**Dado pessoal fica de fora do plugin:** o `profile.md` mora em
`~/.cursor/learning/profile.md` e é criado pelo hook na primeira gravação. O
plugin carrega só o código; seu histórico de aprendizado é seu.

## Instalação

### Opção A — via marketplace local (recomendado)
1. Coloque a pasta `cursor-learning-tutor/` onde quiser guardar (ex: um repo
   git pessoal, ou uma pasta local).
2. No Cursor: `Settings > Plugins` (ou a aba **Plugins** do marketplace) >
   adicionar marketplace/fonte apontando para essa pasta (ou para o repo git).
3. Instale o plugin **cursor-learning-tutor** na seção User.

### Opção B — cópia direta para ~/.cursor (sem marketplace)
Se preferir não usar o fluxo de marketplace, copie os componentes para os
diretórios globais (é o mesmo efeito, sem o "pacote"):
```bash
mkdir -p ~/.cursor/rules ~/.cursor/agents ~/.cursor/commands ~/.cursor/hooks
cp rules/tutor.mdc            ~/.cursor/rules/
cp agents/study-researcher.md ~/.cursor/agents/
cp commands/*.md             ~/.cursor/commands/
cp hooks/*.py                ~/.cursor/hooks/
# nesse caso, use um hooks.json global apontando para ~/.cursor/hooks/*.py
```

### Requisitos
- `python3` no PATH (Windows: troque `python3` por `python` no `hooks.json`).

## Caveats honestos
- Os hooks do plugin chamam os scripts via `$CURSOR_PLUGIN_ROOT`. Se na sua
  versão essa variável não resolver, use a **Opção B** (hooks globais em
  `~/.cursor`) ou fixe o caminho absoluto da pasta instalada do plugin no
  `hooks.json`.
- `alwaysApply: true` teve bug de rebaixamento silencioso em alguma versão do
  Cursor (3.0.16). Se notar que a rule não está ativa, confira em
  `Settings > Rules` se ela aparece como sempre-ativa.
- O hook `sessionStart` (injeção do perfil) teve bug reportado no início de
  2026. Se o agente não calibrar, a captura ainda funciona; use `/study-plan`
  ou cole o topo do `profile.md` ao começar algo novo.
- Hooks executam scripts locais — os dois aqui são curtos de propósito, pra
  você auditar antes de instalar.
