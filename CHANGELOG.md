# Changelog

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
