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
