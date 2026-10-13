# ckanext-mpb

Extensão CKAN do Portal de Dados Movimento pela Base. Registra os templates,
arquivos públicos e assets do portal (plugin `mpb`).

Compatível com CKAN 2.11, a versão das imagens em `ckan/Dockerfile*`.

## Uso

A extensão é instalada pelas imagens do repositório e não precisa de passos
manuais:

- produção: `ckan/Dockerfile` copia `src/ckanext-mpb` e instala com `pip install -e`;
- desenvolvimento: `docker-compose.dev.yml` monta `./src` em
  `/srv/app/src_extensions` e o container instala cada extensão ao iniciar.

Para ativar, inclua `mpb` em `CKAN__PLUGINS` (ver `.env.example`).

## Testes

A suíte roda no job `Extension and API tests` (`.github/workflows/test.yml`),
com bancos e Solr próprios de teste e relatório de cobertura.

Não execute os testes no container `ckan-dev` sem ajustar a configuração: as
fixtures limpam o banco e o índice configurados, e o `.env` aponta para os
dados de desenvolvimento.

## Licença

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
