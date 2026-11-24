# Toolkit de Tale of Immortal

Requer Python 3.10+ com SQLite e biblioteca padrão. O pré-teste abaixo é somente leitura. Foi executado no Windows x64. A primeira execução real no Ubuntu Server 24.04 ARM64 está pendente.

```sh
python3 translation-work/toolkit.py doctor --require-arm64
```

Antes de traduzir em volume, leia o [briefing](docs/briefing-do-jogo.md) e confirme o resultado do pré-teste. Se falhar, encaminhe a mensagem exata. Importe uma cópia privada das três tabelas obtidas do tutorial de configuração do jogo. No Windows, use o caminho real da instalação. No servidor, use a pasta privada copiada para lá.

```sh
python3 translation-work/toolkit.py update-sources --source-dir "/caminho/privado/das-tabelas"
python3 translation-work/toolkit.py status
python3 translation-work/toolkit.py resume
python3 translation-work/toolkit.py batch 1
python3 translation-work/toolkit.py check
```

No Windows, `update-sources` sem caminho procura a instalação da Steam pelo diretório atual e pelas bibliotecas registradas, verificando o App ID 1468810 e a presença das três tabelas. Se houver mais de uma instalação candidata ou se a descoberta falhar, indique o caminho do jogo com `--game-root`. Use `--source-dir` no servidor para a cópia privada das tabelas. Acrescente `--dry-run` para ver as diferenças sem gravar. `batch 1 --legacy-modexcel CAMINHO` apresenta a tradução anterior ao lado da fonte atual para revisão, incluindo os campos antigos de contexto. Apenas traduções revisadas devem entrar no payload de `apply 1 arquivo.jsonl`, que aceita um registro por linha com `id`, `revision` e `ptbr`. Mantenha conteúdo de origem e payloads de trabalho fora do Git. Aplique `--overwrite` só após rever correções e mudanças de revisão.

Os lotes iniciais têm até 500 entradas e o número de lote é estável dentro da mesma base SQLite. Use um backup consistente da base privada para transferir uma sessão já iniciada entre máquinas. Os registros aprovados são separados da origem e a aplicação substitui atomicamente apenas um lote. A transação SQLite protege alterações da fonte. A tabela de histórico guarda revisões diferentes, sem uma política de expurgo implementada. Não remova a base para reiniciar o fluxo, porque isso perde o histórico e pode alterar o vínculo das entradas com seus lotes.

Use `resume` para obter o primeiro lote com pendências ou revisões desatualizadas em `next_batch`. Quando o valor for `null`, verifique o resumo antes de gerar a entrada privada do editor. Registre as escolhas de termos e de estilo em `docs/glossario-ptbr.md` e `docs/diretrizes-de-traducao.md` à medida que forem revisadas.

## Formato e limites verificados

- Windows Steam, build local 21758240. Os artefatos instalados indicam Unity IL2CPP.
- `LocalText` usa `key`. Seu ID de linha pode variar sem alterar a revisão. `BattleSkillPrefixName` e `RoleLogLocal` usam `id`. Neste último, `keyID` agrupa variantes, com valores repetidos. A revisão também compara o conteúdo e os seletores.
- O SQLite guarda os bytes exatos dos JSONs de referência e o contexto de cada linha. O estado fica em `translation-work/local`, ignorado pelo Git. As contagens identificam registros pendentes, não a cobertura jogável.
- Marcadores e tags reconhecíveis são comparados estruturalmente. A verificação não modela toda a gramática do jogo nem prova concordância em português.
- A exportação antiga carrega `ModExportData.cache`, cujo formato e papel no carregamento ainda precisam ser verificados. O tutorial oficial de configuração (配置修改教程.docx) descreve a edição de JSON e manda usar a saída de depuração como referência de formato. Também descreve alterações de configuração por ID preenchendo só os campos modificados. Ainda é necessário confirmar se essa sobreposição funciona nas três tabelas de localização, incluindo a escolha de chave em `LocalText`, e confrontar a referência do tutorial com a exportação corrente do editor.

Na cópia histórica da Oficina (item 3300162134), `ModProject/ModExcel` contém 74.319 linhas JSON legíveis. Use essa pasta com `--legacy-modexcel`. Em `debug/Mod_FknHwV/ModExcel`, os três arquivos também têm a extensão `.json`, mas são binários: compartilham os primeiros 22 bytes e cada arquivo tem 21 bytes a mais que seu correspondente no projeto. O parser JSON não aceita esses arquivos. A diferença comprova que o ZIP de entrada do editor e a saída de depuração são formatos distintos. Para validar o instalável, é necessário obter do editor atual uma exportação mínima com uma substituição por tabela e confirmar no jogo como cada substituição é carregada. A distribuição integral da referência `EN` e de qualquer saída que inclua recursos originais depende de autorização dos respectivos titulares.

`python3 translation-work/toolkit.py build-editor` exige revisão de todos os registros com fonte visível. Gera `translation-work/local/editor-input.zip` com `ModExcel/*.json` para uso privado no projeto do editor. Se o inglês estiver vazio mas houver texto em chinês, o registro continua pendente e o chinês serve de referência estrutural. Linhas sem texto nas fontes consultadas são preservadas. O pacote preserva os campos fora de `en` e os bytes das tabelas que não sofreram alterações. Tabelas alteradas são reserializadas com a quebra de linha e BOM da origem.

O ZIP de entrada contém campos originais do jogo e fica fora do Git. A exportação instalável, o teste em execução e a automação de Releases estão pendentes de verificação de um pacote público enxuto. O `doctor` verifica a impressão digital normalizada do toolkit e exercita SQLite e a reconstrução com uma fixture sintética. Use Git para manter o histórico das traduções aceitas.
