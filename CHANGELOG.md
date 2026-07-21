# Changelog

## 2.1.1
- Move a ficha local para `.cursor/learning/project.md`, em namespace próprio.
- Cabeçalho identifica explicitamente a ficha como dados do Learning Tutor,
  não como rule, prompt ou instrução.
- CLI migra automaticamente o caminho legado `.cursor/learning-project.md`.

## 2.1.0
- Classificação de intent na rule: `concept_gap` → auto-`want`; `repo_local` /
  `agent_task` sem poluir a fila.
- Modelo híbrido: `.cursor/learning-project.md` (stack + candidatos + sondagem)
  + perfil global (fila/coberto).
- CLI: `project-show`, `project-sync`, `project-drop`, `queue-next`;
  normalização/dedupe de tópicos (aliases, anti-ruído).
- `sessionStart` injeta `LEARNING-PROJECT` quando o arquivo existe.
- Novo comando `/study-probe` (perguntas-teste → covered/want).
- `/study-deep` sem tópico usa o primeiro item aberto da fila.
- `/study-plan` inclui stack/candidatos do projeto.

## 2.0.0
- Perfil com **Meta**, **Fila de estudo** e **Coberto**.
- CLI estável em `~/.cursor/learning/cli.py` (instalada no `sessionStart`).
- Novo comando `/study-log` para registro explícito.
- `/study-plan` faz onboarding quando o perfil está vazio.
- Feedback visível (`Salvei no perfil: …`) e marcadores `LEARNING-WANT`.
- Hooks usam `lib_profile.py` compartilhada (menos frágil).

## 1.0.0
- Primeira versão. Empacota: rule de tutoria (alwaysApply), subagent
  `study-researcher`, commands `/study-plan` e `/study-deep`, e hooks de
  captura + injeção do perfil de aprendizado.
