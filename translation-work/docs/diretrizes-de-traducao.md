# Diretrizes de Tradução — Tale of Immortal (PT-BR)

Este documento consolida as decisões editoriais, estilísticas, gramaticais e técnicas para a localização de *Tale of Immortal (鬼谷八荒)* em português brasileiro.

---

## 1. Hierarquia de Fontes

1. **Inglês (`en`) como fonte principal:** toda entrada traduzida parte do texto atual em inglês.
2. **Chinês simplificado (`ch` / `text`) e tradicional (`tc`) como referência de desambiguação:** consultar sempre para esclarecer:
   - relações hierárquicas, parentesco e títulos de tratamento;
   - referências mitológicas do *Shan Hai Jing* (山海经) e termos de cultivo (xianxia/wuxia);
   - sujeitos ocultos, gênero de NPCs fixos ou ambiguidades da adaptação inglesa.
3. **Entradas com `en` vazio ou contendo texto em chinês não traduzido:**
   - Quando `en` estiver vazio mas houver texto em `ch`/`tc` (ex.: notas de atualização `startGameTipDesc*`, questionários `wenjuan*`, eventos `drama*`, títulos `AppellationTitle*`), traduzir diretamente a partir do chinês com fidelidade ao glossário.
   - Quando `en` trouxer texto chinês não localizado (ex.: `skill_content_*`, `honor_text*`, `grade_verse_desc*`, `effect_name*`, `npc_diagogue*`, `skillPrefixDesc*`), traduzir diretamente do chinês para português brasileiro natural.
   - Para geradores de nomes de seitas em pinyin (`schoolFirstName*`, `schoolNameFirst*`, `schoolNameSecond*`), preservar as sílabas em pinyin para manter a identidade chinesa das seitas procedurais.
   - Para prefixos compostos de técnicas (`BattleSkillPrefixName` e `skillPrefixName`/`stepPrefixName`), manter termos curtos, evocativos e combináveis em português (evitando gerar nomes quebrados na composição).

---

## 2. Tom, Voz e Registro

- **Ambientação xianxia / fantasia mitológica chinesa:** português brasileiro fluido, expressivo e natural, com sabor épico/tradicional nos diálogos de cultivo, sem cair em arcaísmos artificiais ou em gírias modernas deslocadas.
- **Diferenciação por tipo de texto:**
  - **Interface (menus, botões, atributos, abas):** conciso, direto e padronizado; respeitar o espaço visual de botões e cabeçalhos (ex.: `Confirmar`, `Cancelar`, `Atributos`, `ATQ`, `DEF`, `CRÍT`).
  - **Descrições mecânicas e tooltips (técnicas, elixires, destinos, efeitos):** clareza absoluta sobre valores, condições, gatilhos e efeitos, mantendo termos do glossário consistentes.
  - **Lore, mitologia e poemas (`item_desc*`, `grade_verse_desc*`, textos do *Shan Hai Jing*):** registro literário cuidado, preservando a beleza poética e os nomes mitológicos.
  - **Diálogos fixos e procedurais (`drama_*`, `RoleLogLocal`):** adaptar o registro ao perfil e à emoção da fala:
    - Respeitoso / formal: tratamento polido (`você` formal ou título como `Mestre`, `Ancião`, `Sênior`, `Companheiro de Dao`).
    - Íntimo / amigável / romântico: natural, acolhedor e fluido (`você`).
    - Arrogante / hostil / demoníaco: cortante, altivo ou ameaçador, preservando a personalidade (`characterGroup`, `emotionID`, `vocal`).
  - **Registros de vida (`RoleLogLocal`, `MonthLog*`):** narrativa concisa e natural de diário/crônica, evitando estruturas truncadas ou literais do inglês.
  - **Editor de Mods (`mod*`, `modEnum*`, `modCondition*`, `modFunction*`):** terminologia técnica clara e consistente para criadores de mods em pt-BR.

---

## 3. Tratamento, Protagonista Variável e Concordância

- **Pronome padrão de tratamento:** `você` (com concordância verbal de 3.ª pessoa: *você pode*, *seu cultivo*, *lhe disse*), evitando misturar `tu` e `você` na mesma fala.
- **Protagonista variável:** como o jogador escolhe gênero e aparência, evitar marcações desnecessárias de gênero para o protagonista quando o texto não restringir gênero:
  - Preferir construções naturalmente neutras (*"Você venceu"*, *"Boas-vindas"*, *"Agradeço sua ajuda"*, *"Que força impressionante"*) em vez de marcas artificiais como `o(a)` ou `x/@` em diálogos.
  - Em substantivos de papel/título sem restrição de gênero (ex.: *Cultivador*, *Discípulo*, *Aprendiz*, *Líder da Seita*), usar a forma padrão do glossário (masculino genérico editorial do português) quando não houver flexão dinâmica do motor, evitando quebrar a fluidez literária.
- **Identificação em diálogos (`RoleLogLocal` e `LocalText`):**
  - Em `RoleLogLocal`, inspecionar `keyID`, `active`, `goal`, `characterGroup`, `relation`, `condition`, `vocal` e `emotionID` antes de traduzir.
  - Papéis típicos nos marcadores de `RoleLogLocal`:
    - `A`: geralmente o jogador / alvo / interlocutor (conferir sempre no contexto de cada `keyID`).
    - `B`: geralmente o NPC falante / autor da ação.
    - `C` ou `X`: terceiro personagem mencionado (parente, amigo, rival, vítima etc.).
    - `{call|B|A}`: como `B` chama `A` (ex.: nome, título, `Mestre`, `Ancião X`, `Marido`, `Esposa`).
    - `{relation|X|B}`: relação de `X` com `B` (ex.: *meu {relation|X|B}*).

### Regras gramaticais para `{gender|...}`, `{gender1|...}` e `{gender2|...}`

Com `common_ta1 = "ele"`, `common_ta2 = "ela"`, `common_ta3 = "dele"`, `common_ta4 = "dela"`, `common_ta5 = "ele"` e `common_ta6 = "ela"`:

1. **`{gender|X}` (`ele`/`ela`):** usar em posição de sujeito (*"{gender|C} é meu {relation|C|B}"* → *"ele/ela é..."*).
2. **`{gender1|X}` (`dele`/`dela`):** posicionar **após** o substantivo possuído! Como `dele`/`dela` concorda com o possuidor (e não com o substantivo), funciona perfeitamente tanto com substantivos masculinos quanto femininos:
   - `"spared {gender1|C} life"` → `"poupei a vida {gender1|C}"` (*a vida dele / a vida dela*).
   - `"{gender1|X} spirit can rest in peace"` → `"o espírito {gender1|X} possa descansar em paz"`.
   - `"for {gender1|C} sake"` → `"em consideração à amizade {gender1|C}"` ou `"pelo bem {gender1|C}"`.
3. **`{gender2|X}` (`ele`/`ela`):** **NUNCA** colocar `de` ou `em` imediatamente antes de `{gender2|X}` ou `{gender|X}` (o que geraria *"de ele"* ou *"em ela"*!). Usar sempre preposições que não sofrem contração obrigatória (`a`, `para`, `por`, `com`, `sobre`, `contra`, `perante`, `diante de` — evitando `de` direto):
   - `"avenge {gender2|X}"` → `"fazer justiça por {gender2|X}"` ou `"vingar o que fizeram a {gender2|X}"`.
   - `"ask {gender2|C} to..."` → `"pedir a {gender2|C} que..."`.
   - `"talk about {gender2|C}"` → `"falar sobre {gender2|C}"`.
   - `"care for {gender2|A}"` → `"cuidar bem de quem importa"` (NÃO remover o token!) → `"velar por {gender2|A}"` ou `"dar apoio a {gender2|A}"`.

---

## 4. Preservação Técnica Obrigatória

1. **Formato JSONL:** uma linha por registro em `translation-work/translations/batch-XXXX.jsonl`, ordenada por `id`, UTF-8 sem BOM, quebra de linha `LF`, contendo exatamente `{"id":"...","revision":"...","ptbr":"..."}`.
2. **IDs e revisões:** preservar exatamente `id` e `revision` do lote correspondente em `translation-work/lotes/`.
3. **Marcadores e tags:** preservar integralmente (mesma grafia e mesma multiplicidade):
   - `{0}`, `{1}`, `{name|A}`, `{call|B|A}`, `{relation|X|B}`, `{gender|C}`, `{#areaName8}`, etc.
   - `<g>...</g>`, `<r>...</r>`, `<b>...</b>`, `<o>...</o>`, `<size=...>...</size>`, `<color=...>...</color>`, `<root0>...</root0>`, `<ta1>`, etc.
   - `%s`, `%d`, `%1$s`, etc.
   - `$s_huo$`, `$s_jian$`, etc.
   - `&61111_dmg&`, `&61111_hhsj&`, etc.
4. **Quebras de linha e tabulações:**
   - As fontes usam `\n` e `\t` **literais** (barra invertida + letra `n`/`t` dentro da string), nunca quebras de linha brutas. Preservar `\n` e `\t` literais e nunca inserir caracteres de quebra de linha bruta (`\n` real / `\r`).
5. **Aspas internas:**
   - Na fonte original do jogo, aspas duplas internas são escapadas como `\"` literal (`plain_dq=0` em `en` e `ch`). Ao usar aspas dentro de um texto traduzido, preferir aspas tipográficas (`“` `”`) ou preservar `\"` quando espelhar citações da fonte, evitando incompatibilidades com o parser do jogo.
6. **Sentinelas e valores estruturais:**
   - Preservar verbatim valores puramente estruturais ou de teclas sem carga semântica traduzível quando idênticos em `en` e `ch` (ex.: `"0"` em descrições vazias, `"..."`, `"???"`, `"X"` em slots reservados de `spriteTalentDesc*`, símbolos de teclas em `keyboard_*`).
   - Atenção a falsos sentinelas: conferir sempre o chinês e chaves vizinhas (ex.: `skill_mastery10` tem `en="X"`, `ch="觉醒"`, parte da sequência romana `I`–`XII`, logo permanece `"X"` como numeral romano 10).

---

## 5. Política para Entradas Pendentes de Contexto

- Quando uma entrada apresentar ambiguidade real que não possa ser resolvida nem pelo inglês, nem pelo chinês, nem pelas chaves vizinhas ou metadados do evento (por exemplo: referência pronominal impossível de determinar, jogo de palavras dependente de cena ausente, erro grave/truncamento na fonte que impeça inferir o sentido), **deixar a entrada fora do arquivo revisado do lote (pendente)** e registrar o `id`, o número do lote e a dúvida exata para revisão posterior com contexto de jogo.
