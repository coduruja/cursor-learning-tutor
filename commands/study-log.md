Registre algo no meu perfil de aprendizado (`~/.cursor/learning/profile.md`).

## O que registrar
- Se eu passar um tópico (ou descrever o que aprendemos): **coberto**.
- Se eu disser "quero estudar X" / "coloca X na fila": **fila**.
- Se o perfil estiver vazio e eu só rodar o comando: faça onboarding em 2
  perguntas (nível geral + foco) e rode `init`, depois pergunte o primeiro tópico.

## Como gravar (obrigatório)
Use a CLI estável (não edite o markdown na mão a menos que a CLI falte):

```bash
python3 ~/.cursor/learning/cli.py covered --topic "..." --level "iniciante|intermediário|avançado" --note "..."
# ou
python3 ~/.cursor/learning/cli.py want --topic "..." --note "..."
# ou
python3 ~/.cursor/learning/cli.py init --level "..." --focus "..."
```

Se a CLI não existir, avise que preciso abrir um **novo chat** para o
`sessionStart` instalar `~/.cursor/learning/cli.py`, ou copie o helper do plugin.

## Resposta
Seja curto: confirme com `Salvei no perfil: …` e mostre se foi **coberto** ou **fila**.
Não pesquise na web.
