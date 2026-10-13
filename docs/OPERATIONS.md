# Operação do repositório CKAN

Este documento cobre somente preparação, desenvolvimento local e validações de
CI. O deploy da implantação anterior em GCP não faz parte do Portal de Dados do
Movimento pela Base. O CD para AWS será definido depois que registro, domínio,
parâmetros e método de autenticação forem aprovados.

## Serviços do baseline

| Serviço | Função | Persistência esperada |
| --- | --- | --- |
| `nginx` | Proxy reverso e terminação HTTPS | Certificados externos ao container |
| `ckan` / `ckan-dev` | Aplicação CKAN | `ckan_storage` |
| `db` | PostgreSQL do CKAN e Datastore | `pg_data` |
| `solr` | Indexação e busca | `solr_data` |
| `redis` | Cache e filas | Não é fonte primária de dados |
| `datapusher` | Carga tabular no Datastore | Sem persistência própria |

PostgreSQL, Solr e Redis permanecem em redes Docker internas no Compose de
produção. A definição funcional dos plugins, metadados e experiência do portal
fica para a etapa de engenharia de aplicação.

## Desenvolvimento local

Pré-requisitos: Docker Engine, Docker Compose V2 e Git.

```bash
cp .env.example .env
bin/compose build
bin/install_src
bin/compose up -d --wait
```

O `.env` é local e ignorado pelo Git. Os valores `CHANGE_ME` devem ser usados
somente como marcadores; nenhum segredo real pode ser incluído no repositório.

Atalhos disponíveis:

| Comando | Operação |
| --- | --- |
| `bin/compose ...` | Executa Docker Compose no ambiente de desenvolvimento |
| `bin/ckan ...` | Executa a CLI do CKAN |
| `bin/shell` | Abre shell no container de desenvolvimento |
| `bin/install_src` | Instala extensões locais |
| `bin/reload` | Recarrega o processo Python |
| `bin/restart` | Reinicia somente o CKAN de desenvolvimento |

## Diagnóstico local

```bash
bin/compose ps
bin/compose logs --tail=200 ckan-dev db solr redis datapusher
```

Não execute `docker compose down -v` em ambiente com dados que precisem ser
preservados. A opção `-v` remove volumes nomeados.

## Validação de dependências, healthchecks e persistência

O CKAN de desenvolvimento só inicia depois que PostgreSQL, Solr e Redis estão
saudáveis. As sondas HTTP usam `127.0.0.1`: em Docker recente, `localhost`
resolve primeiro para IPv6 e faz o healthcheck falhar com o serviço no ar.
`start_period` cobre a inicialização do banco e da aplicação antes das
tentativas contarem como falha.

O `pg_isready` usa `-h 127.0.0.1` porque, pelo socket Unix, ele responde ao
servidor temporário do init antes de `ckandb` e `datastore` existirem. O Solr é
sondado em `/solr/ckan/admin/ping`, que só responde com o core do CKAN carregado.

| Dado | Volume | Sobrevive a `docker compose down` |
| --- | --- | --- |
| PostgreSQL | `pg_data` | sim |
| Índice Solr | `solr_data` | sim |
| Arquivos do CKAN | `ckan_storage` | sim |
| Redis | nenhum | não; cache e fila são recriados |
| DataPusher | nenhum | não |

No Compose de desenvolvimento, `site_packages`, `local_bin`, `home_dir` e
`pip_cache` guardam pacotes, extensões instaladas por `bin/install_src` e o
`ckan.ini`. Não são dados: depois de trocar a imagem base (por exemplo, nova
versão do CKAN), remova esses volumes para que a imagem nova não fique mascarada:

```bash
bin/compose down
project="$(basename "$PWD")"
docker volume rm "${project}_site_packages" "${project}_local_bin" "${project}_home_dir"
```

PostgreSQL, Solr e Redis ficam em redes internas. No Compose de desenvolvimento
o retorno do DataPusher aponta para `http://ckan-dev:5000`, porque o serviço
local não se chama `ckan`.

```bash
python3 tests/test_compose_contract.py
tests/test_compose_persistence.sh
```

O segundo comando usa o projeto Compose `mpbckanvalidacao` e apaga esses
volumes ao terminar. Ele não altera a stack de desenvolvimento já em execução.

## Automação atual

O CI executa validação de Compose e scripts, testes da extensão, build sem push
das imagens de produção e smoke test quando aplicável. Nenhum workflow atual
publica imagens ou faz deploy.

O script `bin/daily-restart` foi recebido no baseline e permanece apenas como
artefato legado testado. Reinício diário não é requisito da arquitetura V1.

## Pendências para o CD

Antes de criar qualquer workflow de implantação, definir e revisar:

- registro de imagens e autenticação sem chaves AWS estáticas;
- domínio, certificados e configuração final do Nginx;
- origem segura das variáveis e segredos de runtime;
- tag imutável da imagem vinculada ao commit ou release;
- procedimento de migration, validação pós-deploy e rollback;
- persistência EBS e rotina de backup/restauração;
- aprovação de ambiente no GitHub e responsáveis operacionais.

Consulte `docs/CI_CD.md` para a fronteira entre CI e CD e o repositório de
arquitetura para o runbook de produção V1.
