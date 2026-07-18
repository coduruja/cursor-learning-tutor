Sondagem ativa: descubra o que eu sei vs o que o projeto exige, e ajuste o perfil.

Sem pesquisar na web. Prefira a CLI estável.

## Passos
1. Leia o perfil global e o contexto do projeto:
   ```bash
   python3 ~/.cursor/learning/cli.py show
   python3 ~/.cursor/learning/cli.py project-show
   ```
   Se não houver `LEARNING-PROJECT` / arquivo de projeto e o repo tiver stack
   clara, sincronize 3–8 candidatos específicos (sem linguagens base):
   ```bash
   python3 ~/.cursor/learning/cli.py project-sync --stack "A;B" --candidates "t1;t2;t3"
   ```

2. Monte uma hipótese curta (não mostre como lista enorme):
   - o que eu **provavelmente sei** (nível/foco + coberto)
   - o que eu **deveria saber** neste projeto (candidatos + stack)
   Priorize 5–8 tópicos no total.

3. Faça **3–5 perguntas curtas em um único bloco** (não uma por mensagem).
   Perguntas práticas, não trivia. Aceite “não sei”.

4. Com as minhas respostas, ajuste:
   - acertou com confiança →
     `python3 ~/.cursor/learning/cli.py covered --topic "..." --level "..." --note "study-probe"`
     e, se era candidato do projeto:
     `python3 ~/.cursor/learning/cli.py project-drop --topic "..."`
   - errou / “não sei” →
     `python3 ~/.cursor/learning/cli.py want --topic "..." --note "lacuna no study-probe"`
   - parcial →
     `python3 ~/.cursor/learning/cli.py want --topic "..." --note "reforço (study-probe)"`

5. Atualize a sondagem do projeto:
   ```bash
   python3 ~/.cursor/learning/cli.py project-sync --probe-summary "..."
   ```

## Resposta final
Em 2–3 linhas: o que foi para **coberto**, o que entrou na **fila**, e o
próximo passo sugerido (`/study-deep` no primeiro item da fila, se houver).
