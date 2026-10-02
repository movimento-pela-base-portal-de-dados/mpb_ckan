# CI/CD — Deploy CKAN

## Visão geral

O pipeline de deploy roda automaticamente a cada push na branch `main` e pode ser disparado manualmente via `workflow_dispatch`. Ele é responsável por construir novas imagens Docker, publicá-las no Google Artifact Registry (GAR), copiar o repositório para a VM de produção e iniciar o ckan.

## Etapas do workflow

### 1. Escrever o .env

O arquivo `.env` é montado a partir de duas fontes:

- **Secret `ENV_FILE`** — bloco com todas as variáveis da aplicação (credenciais do banco, configurações do CKAN, lista de plugins, etc.). É escrito literalmente via heredoc para que valores com aspas (ex.: `CKAN__PLUGINS="..."`) sejam preservados exatamente como estão no secret.
- **`REGISTRY`** — derivado de outros secrets (`GAR_REGION`, `GCP_PROJECT_ID`, `GAR_REPOSITORY`) e adicionado ao final do arquivo. O Docker Compose da VM usa essa variável para saber onde fazer push/pull das imagens.

### 2. Build e push das imagens

O Docker Compose constrói os três serviços a partir dos Dockerfiles e faz o push das imagens resultantes para o GAR com a tag `:latest`. A variável `REGISTRY` do `.env` indica para onde fazer o push.

### 3. Gerenciamento de imagens

Após o build, as imagens de cada serviço são ordenadas por data de criação (mais recente primeiro) e gerenciadas conforme a regra:

- **1 imagem** → recebe a tag `:latest`
- **2 imagens** → a mais recente recebe `:latest`, a segunda recebe `:previous`
- **3+ imagens** → as duas mais recentes são tagueadas (`:latest` e `:previous`), as demais são deletadas

Isso garante que o registry sempre tenha exatamente no máximo duas imagens por serviço após cada deploy, com um ponto de rollback sempre disponível.

### 4. Copiar o repositório para a VM

O repositório inteiro (exceto `.git`) é comprimido em um tarball e copiado para a VM via `gcloud compute scp`. Isso garante que a VM sempre tenha o `docker-compose.yml`, scripts e arquivos de configuração atualizados.

### 5. Deploy na VM

Um comando SSH extrai o tarball e executa o `deploy.sh` na VM. Esse script:

1. Carrega o `.env` para obter `REGISTRY` e outras variáveis.
2. Autentica o Docker no GAR usando a service account vinculada à VM (via endpoint de metadados do GCP — nenhuma credencial é armazenada na VM).
3. Faz o pull das imagens `:latest` de todos os serviços.
4. Executa `docker compose up -d --remove-orphans` para reiniciar o stack com as novas imagens.
5. Remove imagens dangling para liberar espaço em disco.

## Rollback

Para voltar à versão anterior, acesse a VM via SSH e execute:

```bash
cd ~/abc_ckan
source .env
docker tag ${REGISTRY}/ckan:previous ${REGISTRY}/ckan:latest
docker tag ${REGISTRY}/nginx:previous ${REGISTRY}/nginx:latest
docker tag ${REGISTRY}/db:previous ${REGISTRY}/db:latest
docker compose up -d
```

Ou simplesmente dispare um novo pipeline a partir do commit anterior — a etapa de rotação preservará o estado corretamente.

## Secrets necessários

| Secret | Finalidade |
|---|---|
| `GCP_SA_KEY` | JSON da service account para autenticação do `gcloud` no CI |
| `GCP_PROJECT_ID` | ID do projeto GCP |
| `GAR_REGION` | Região do Artifact Registry (ex.: `southamerica-east1`) |
| `GAR_REPOSITORY` | Nome do repositório dentro do GAR |
| `VM_NAME` | Nome da instância do Compute Engine |
| `VM_ZONE` | Zona do Compute Engine |
| `ENV_FILE` | Conteúdo completo do arquivo `.env` da aplicação |

## Scripts

Toda a lógica shell fica em `.github/scripts/` para manter o YAML do workflow legível:

| Script | O que faz |
|---|---|
| `rotate-tags.sh` | Promove `:latest` → `:previous` no GAR antes de cada build |
| `build-push.sh` | Constrói e faz push das imagens via Docker Compose |
| `cleanup-images.sh` | Deleta digests sem tag (órfãos) do GAR |
| `deploy.sh` | Roda na VM: autentica, faz pull e reinicia o stack |