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
- O tutorial oficial de configuração (配置修改教程.docx) descreve alterações por ID preenchendo só os campos modificados. O exemplo oficial `DLC修改配置例子` traz um `LocalText.json` desse tipo, com `id`, `key` e o campo do idioma alterado. O cache nativo contém metadados do mod e um objeto de itens vazio para mods de dados como o histórico.

Na cópia histórica da Oficina (item 3300162134), `ModProject/ModExcel` contém 74.319 linhas JSON legíveis. Use essa pasta com `--legacy-modexcel`. As três tabelas em `debug/Mod_FknHwV/ModExcel` voltaram, byte a byte, aos arquivos do projeto após decodificação. O codec usa o mesmo formato documentado no [Tale of Immortal Tool](https://github.com/nozwock/tale-of-immortal-tool/blob/e7435fb756201afb3a23c96676a9f90f2955f855/src/EncryptTool.cs) e foi conferido também no cache e em uma tabela do exemplo oficial.

`python3 translation-work/toolkit.py build-editor` exige revisão de todos os registros com fonte visível. Gera `translation-work/local/editor-input.zip` com `ModExcel/*.json` para uso privado no projeto do editor. Se o inglês estiver vazio mas houver texto em chinês, o registro continua pendente e o chinês serve de referência estrutural. Linhas sem texto nas fontes consultadas são preservadas. O pacote preserva os campos fora de `en` e os bytes das tabelas que não sofreram alterações. Tabelas alteradas são reserializadas com a quebra de linha e BOM da origem.

Para gerar o mod local depois que todas as traduções estiverem revisadas:

```sh
python3 translation-work/toolkit.py build-mod
```

O comando gera `translation-work/local/PTBR.zip` com `Mod_YuPtBr/ModExportData.cache` e `Mod_YuPtBr/ModExcel/` na estrutura nativa. Os registros incluem apenas o ID, a chave em `LocalText` e o campo `en` traduzido. Para instalar, extraia a pasta `Mod_YuPtBr` dentro de `ModExportData`, abra o menu de mods, ative a tradução e selecione inglês. Para voltar ao original, desative o mod e reinicie o jogo. Evite ativar simultaneamente o item antigo da Oficina, pois ambos alteram as mesmas tabelas.

O ZIP de entrada do editor e as referências originais são privados. O `doctor` verifica as impressões digitais, SQLite e o empacotamento nativo com uma fixture. O carregamento das três substituições no jogo e a automação de Releases ainda precisam de verificação.
