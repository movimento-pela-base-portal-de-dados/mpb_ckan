# abc_ckan — documentação do projeto

Este repositório contém a configuração Docker do CKAN usado pelo projeto ABC,
incluindo a extensão `ckanext-abc`, os serviços de dados, a configuração de
desenvolvimento e o pipeline de deploy para uma VM no Google Cloud.

## Visão geral

O projeto possui dois modos de execução:

| Modo | Compose | Uso |
| --- | --- | --- |
| Produção/base | `docker-compose.yml` | Executar CKAN com imagens publicadas no Artifact Registry |
| Desenvolvimento | `docker-compose.dev.yml` | Desenvolver o CKAN e extensões com o código local montado |

### Serviços

| Serviço | Função | Persistência |
| --- | --- | --- |
| `nginx` | Proxy reverso e terminação HTTPS | Certificados montados de `/etc/letsencrypt` |
| `ckan` / `ckan-dev` | Aplicação CKAN | Volume `ckan_storage` |
| `db` | PostgreSQL, banco do CKAN e Datastore | Volume `pg_data` |
| `solr` | Indexação e busca | Volume `solr_data` |
| `redis` | Cache e filas | Não persistido |
| `datapusher` | Importação de dados para o Datastore | Não persistido |

Na produção, as redes `solrnet`, `dbnet` e `redisnet` são internas. O NGINX
é o ponto de entrada externo e depende de o CKAN estar saudável.

## Estrutura do repositório

```text
.
├── ckan/                 # Dockerfiles, patches e scripts de inicialização do CKAN
├── nginx/                # Imagem e configuração do proxy reverso
├── postgresql/           # Imagem e inicialização dos bancos
├── src/ckanext-abc/      # Extensão customizada do projeto
├── bin/                  # Atalhos para operações no ambiente de desenvolvimento
├── docker-compose.yml    # Stack base/produção
├── docker-compose.dev.yml# Stack de desenvolvimento
├── .env.example          # Modelo de configuração
├── .github/scripts/      # Scripts de build, publicação e deploy
└── .github/workflows/    # Workflows do GitHub Actions
```

## Pré-requisitos

- Docker Engine instalado e em execução.
- Docker Compose V2 (`docker compose`, com espaço).
- Usuário com permissão para executar Docker sem `sudo`.
- Git, para desenvolvimento.

Verifique a instalação:

```bash
docker version
docker compose version
docker run --rm hello-world
```

## Configuração do ambiente

Crie o arquivo local de configuração:

```bash
cp .env.example .env
```

O `.env` não deve ser versionado. Antes de disponibilizar o serviço, altere
obrigatoriamente:

- `POSTGRES_PASSWORD`, `CKAN_DB_PASSWORD` e as demais senhas do banco;
- `CKAN_SYSADMIN_NAME`, `CKAN_SYSADMIN_PASSWORD` e `CKAN_SYSADMIN_EMAIL`;
- `CKAN___BEAKER__SESSION__SECRET`;
- os segredos JWT de API;
- `CKAN_SITE_URL`, portas e configurações SMTP;
- `REGISTRY`, quando as imagens forem publicadas no Artifact Registry.

As variáveis com prefixo `CKAN__` ou `CKAN___` são convertidas pelo
`ckanext-envvars` em configurações do `ckan.ini`. Por exemplo:

```dotenv
CKAN__PLUGINS="image_view text_view datatables_view datastore datapusher envvars"
CKAN__DATAPUSHER__CALLBACK_URL_BASE=http://ckan:5000
```

Valores como `db`, `redis` e `solr` são nomes de serviço Docker e devem ser
usados nas URLs internas. Eles não devem ser substituídos por `localhost`
dentro dos containers.

## Execução local em modo base

Esse modo simula a execução da aplicação com o serviço `ckan` e as imagens de
produção. Na primeira execução:

```bash
cp .env.example .env
docker compose build
docker compose up -d --wait
docker compose ps
```

O endereço depende de `NGINX_PORT_HOST` e `NGINX_SSLPORT_HOST`; com a
configuração padrão, o acesso HTTPS é `https://localhost:8443`.

Para acompanhar os logs:

```bash
docker compose logs -f ckan
docker compose logs -f nginx
```

Para parar o stack sem apagar os dados dos volumes:

```bash
docker compose down
```

Não use `docker compose down -v` sem confirmar a necessidade: essa opção
remove os volumes nomeados e pode apagar o banco, os índices do Solr e os
arquivos armazenados pelo CKAN.

## Desenvolvimento

O modo de desenvolvimento monta `./src` no container `ckan-dev`. Alterações na
extensão podem ser testadas sem reconstruir toda a imagem.

```bash
cp .env.example .env
# Para desenvolvimento, normalmente use CKAN_SITE_URL=http://localhost:5000
bin/compose build
bin/install_src
bin/compose up -d --wait
```

Atalhos disponíveis:

| Comando | Operação |
| --- | --- |
| `bin/compose ...` | Executa comandos Compose no stack de desenvolvimento |
| `bin/ckan ...` | Executa a CLI do CKAN em `ckan-dev` |
| `bin/shell` | Abre um shell Bash em `ckan-dev` |
| `bin/install_src` | Instala as extensões encontradas em `src/` |
| `bin/generate_extension` | Cria uma nova extensão dentro de `src/` |
| `bin/reload` | Recarrega o processo Python do CKAN |
| `bin/restart` | Reinicia o serviço `ckan-dev` |

Exemplos:

```bash
bin/shell
bin/ckan user list
bin/ckan sysadmin add nome-do-usuario
bin/compose logs -f ckan-dev
```

Para desenvolver a extensão existente, altere os arquivos em
`src/ckanext-abc/`. A configuração de plugins deve ser atualizada em
`CKAN__PLUGINS` no `.env` quando um novo plugin for adicionado.

## Extensão `ckanext-abc`

O código da extensão está em `src/ckanext-abc/ckanext/abc/`. Os principais
recursos customizados são:

- `plugin.py`: registro e configuração do plugin;
- `templates/`: sobrescritas e componentes de interface do CKAN;
- `public/`: imagens, CSS e JavaScript;
- `ckan_dataset_schema.yaml`: schema customizado de datasets;
- `tests/`: testes da extensão.

O `Dockerfile.dev` instala o conteúdo de `src/` no container de desenvolvimento.
O `Dockerfile` de produção instala o que for definido na imagem publicada.
Scripts em `ckan/docker-entrypoint.d/` são executados durante a inicialização
da imagem CKAN e fazem configurações específicas do projeto.

## Comandos administrativos do CKAN

Em produção/base:

```bash
docker compose exec ckan ckan user add usuario email=usuario@example.org
docker compose exec ckan ckan sysadmin add usuario
docker compose exec ckan ckan user remove usuario
```

Em desenvolvimento, substitua o primeiro trecho por `bin/ckan`:

```bash
bin/ckan user add usuario email=usuario@example.org
```

## Deploy automático

O workflow `.github/workflows/deploy-ckan.yml` é executado em pushes para
`main` ou manualmente por `workflow_dispatch`. O fluxo é:

1. Faz checkout do repositório.
2. Autentica no Google Cloud.
3. Gera o `.env` a partir do secret `ENV_FILE`.
4. Constrói e publica as imagens `ckan`, `nginx` e `db` no Artifact Registry.
5. Mantém as tags `latest` e `previous` e remove imagens antigas.
6. Empacota o repositório e copia o arquivo para a VM.
7. Extrai o projeto em `~/abc_ckan` e executa `.github/scripts/deploy.sh`.

Na VM, o deploy autentica o Docker usando a service account da instância,
faz pull das imagens e executa:

```bash
docker compose -f docker-compose.yml up -d --remove-orphans
```

O workflow depende destes secrets:

| Secret | Finalidade |
| --- | --- |
| `GCP_SA_KEY` | Credencial do GitHub Actions no Google Cloud |
| `GCP_PROJECT_ID` | Projeto GCP |
| `GAR_REGION` | Região do Artifact Registry |
| `GAR_REPOSITORY` | Repositório das imagens |
| `VM_NAME` | Nome da VM |
| `VM_ZONE` | Zona da VM |
| `ENV_FILE` | Conteúdo do `.env` de produção |

O deploy copia o repositório inteiro, portanto scripts versionados, incluindo
`bin/daily-restart`, ficam disponíveis na VM após o pipeline.

## Reinício diário

O script `bin/daily-restart` reinicia o stack de produção e espera os
healthchecks:

```bash
~/abc_ckan/bin/daily-restart
```

Para executar diariamente às 4h no usuário que possui permissão no Docker:

```bash
crontab -e
```

Adicione, ajustando o caminho e o fuso horário da VM:

```cron
0 4 * * * /home/USUARIO/abc_ckan/bin/daily-restart >> /home/USUARIO/abc_ckan/daily-restart.log 2>&1
```

O cron deve ser configurado uma única vez na VM. O deploy atualiza o script,
mas não cria nem altera o crontab. O arquivo precisa estar versionado como
executável (`100755`).

## Saúde e troubleshooting

Ver status e healthchecks:

```bash
docker compose ps
docker inspect --format='{{json .State.Health}}' \
  "$(docker compose ps -q ckan)"
```

Ver logs dos serviços que falharam:

```bash
docker compose logs --tail=200 ckan db solr redis datapusher nginx
```

Se o CKAN não iniciar:

1. Confirme se o `.env` existe e contém as variáveis necessárias.
2. Verifique se o PostgreSQL, Solr e Redis estão `healthy`.
3. Confira conflitos nas portas definidas por `NGINX_PORT_HOST`,
   `NGINX_SSLPORT_HOST` e `CKAN_PORT_HOST`.
4. Confirme permissões do usuário sobre o Docker.
5. Recrie apenas os containers, preservando os volumes:

   ```bash
   docker compose up -d --force-recreate --wait
   ```

Se houver falha no deploy, verifique os logs do GitHub Actions e, depois, na
VM:

```bash
cd ~/abc_ckan
bash .github/scripts/deploy.sh
docker compose ps
```

## Backup e dados persistentes

Os dados principais ficam nos volumes nomeados `pg_data`, `solr_data` e
`ckan_storage`. O Compose não substitui uma política de backup. Antes de
operações destrutivas, identifique os volumes e faça backup do PostgreSQL e
dos arquivos de armazenamento do CKAN.

O comando `docker compose down` preserva esses volumes. A remoção explícita
com `docker compose down -v` é destrutiva para os dados locais.

## Segurança

- Nunca publique o `.env` nem secrets do GitHub.
- Troque todas as credenciais de exemplo antes de expor o CKAN.
- Restrinja as portas da VM com firewall e exponha preferencialmente apenas o
  NGINX.
- Em produção, use certificados válidos montados em `/etc/letsencrypt`.
- Revise permissões e proprietário dos arquivos antes de executar scripts na
  VM.

## Referências técnicas

- [README principal](../README.md): detalhes gerais do template CKAN Docker.
- [Docker Compose de produção](../docker-compose.yml)
- [Docker Compose de desenvolvimento](../docker-compose.dev.yml)
- [Workflow de deploy](../.github/workflows/deploy-ckan.yml)
- [Scripts do pipeline](../.github/scripts/)
