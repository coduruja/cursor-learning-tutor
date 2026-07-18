Delegue ao subagent `study-researcher` a criação de uma trilha de estudo
aprofundada e curada.

- Tópico: use o que eu escrever após o comando. Se eu não especificar:
  1. rode `python3 ~/.cursor/learning/cli.py queue-next`
  2. se houver item aberto na fila, use esse tópico (diga em uma linha qual)
  3. senão, pergunte em uma linha qual tópico
- Nível: pegue do `LEARNING-PROFILE`. Se não houver, infira da conversa ou pergunte.
- Se houver `LEARNING-PROJECT`, mencione stack/candidatos relevantes no prompt
  do subagent (contexto, não substituem o tópico).

Passe tópico + nível ao subagent e traga de volta só a trilha final (ponto de
partida, trilha ordenada, sinais de avanço). Não refaça a pesquisa no chat.

Ao final, pergunte em uma linha se quero colocar o tópico na **fila** com
`/study-log` (ou rode `want` se eu disser que sim).
