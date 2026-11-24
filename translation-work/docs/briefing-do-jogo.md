# Briefing de Tale of Immortal

## Cenário e estrutura narrativa

Tale of Immortal (鬼谷八荒) é um RPG sandbox de cultivo em um mundo de fantasia inspirado na mitologia chinesa. O jogador define seu cultivador e constrói uma trajetória por encontros, missões, exploração e relações com outros cultivadores. A loja descreve decisões que alteram o percurso narrativo e a possibilidade de levar uma seita a uma posição de maior poder. Isso fundamenta duas leituras distintas para os textos: cenas com personagens e objetivos próprios, e registros gerados por sistemas que combinam participantes e condições variáveis. [Página oficial do jogo no Steam](https://store.steampowered.com/app/1468810/Tale_of_Immortal/)

## Cultivo, técnicas e relações

A apresentação oficial situa o início da jornada em Yukong Village, com um cultivador no estágio de Qi Refining, e aponta Tian Yuan Mountain como destino na busca pelo entendimento do Caminho. As feras remetem ao *Shan Hai Jing* (山海经), o Clássico das Montanhas e dos Mares. O progresso alterna avanços de cultivo, exploração de domínios místicos e busca por recursos e tesouros. Preserve a diferença entre topônimo, estágio de progressão e referência mitológica ao reunir termos para o glossário. [Apresentação oficial no Steam](https://store.steampowered.com/app/1468810/Tale_of_Immortal/#about_this_game)

Os textos das tabelas locais incluem atributos, reinos de cultivo, nomes de técnicas e interações sociais. Confira a função de cada termo na tela: o nome de uma técnica, seu efeito e o atributo que ela altera podem aparecer em entradas relacionadas. Distinga a habilidade para uma arma ou escola, a técnica individual e o nível de progresso de um personagem. As seitas são também organizações com membros e posições, de modo que a mesma expressão pode ser título de tratamento em diálogo e cargo em interface.

Os registros de vida incluem disputas entre personagens, afinidade e ações como roubo de itens. Cada ocorrência pode ter variantes de condição, relação, grupo, voz e emoção. Um único identificador de evento reúne alternativas e a ordem de apresentação precisa ser verificada antes de concluir que dois registros compõem a mesma cena. Em textos curtos de interface, confira limites de espaço e contraste. No combate, consulte os nomes completos resultantes da combinação de prefixos com os demais componentes.

## Personagens, narrador e concordância

O protagonista é criado pelo jogador. Em cenas geradas, papéis como autor da ação, alvo, interlocutor e pessoa mencionada podem ser ocupados por NPCs diferentes. O fato de um evento usar uma voz ou emoção específica não identifica por si só a pessoa descrita. Compare variantes que compartilham `keyID` e inspecione os campos `active`, `goal`, `characterGroup`, `relation`, `condition` e `vocal`. Esses nomes são indícios do esquema. O vínculo exato entre valor, personagem e gênero precisa de confirmação no contexto.

Em episódios fixos, procure nome e fala anterior, identifique quem está falando e a quem se refere. Compare o chinês quando o inglês não explicitar a relação. Preserve alternativas para protagonista variável e mantenha casos ambíguos em revisão até haver evidência. Em `LocalText`, use também a família da chave para localizar interface, evento ou falas vizinhas, sem tomar a proximidade na tabela como ordem narrativa.

## Edições e referências

O Steam lista conteúdo adicional como Five Blooms, Ground of No Return e BaHuang Chronicle. As tabelas distribuídas com o tutorial são uma referência de trabalho. A presença de uma linha nessas tabelas ainda precisa ser confrontada com os conteúdos ativos e com o jogo para atribuir a linha a uma edição ou DLC. A cobertura por DLC permanece em verificação. [Catálogo oficial de DLCs no Steam](https://store.steampowered.com/dlc/1468810/)

O projeto histórico carrega a localização pelo campo `en`, com chinês simplificado e tradicional disponíveis para consulta. Decisões de terminologia e de voz devem entrar no glossário e nas diretrizes após revisão linguística. [Ficha histórica na Oficina Steam](https://steamcommunity.com/workshop/filedetails/?id=3300162134)
