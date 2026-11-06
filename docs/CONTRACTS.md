# Contratos entre repositórios

## mpb-infra -> mpb-ckan
A infraestrutura fornece, em `sa-east-1`:

- **EC2** Amazon Linux 2023 com Docker, plugin Compose, `git`, `jq`, AWS CLI, `certbot` e agente SSM. Clone do repositório em `/opt/mpb_ckan`.
- **Disco**: EBS gp3 criptografado, com `delete_on_termination=false`. Os volumes Docker `pg_data`, `solr_data` e `ckan_storage` ficam nele.
- **Rede**: Elastic IP; Security Group com entrada só em `443` e `80` (desafio do Let's Encrypt e redirecionamento para HTTPS), sem SSH; PostgreSQL, Solr e Redis sem exposição.
- **Acesso**: administração e deploy por Session Manager. A instância tem a tag `Project=mpb`, exigida pela política do grupo de engenharia para `ssm:StartSession`.
- **Instance role** com:
  - `ssm:GetParametersByPath` em `/mpb/ckan/*`;
  - `s3:ListBucket`, `s3:GetObject` e `s3:PutObject` em `s3://<mpb-data>/backups/postgresql/*` e `backups/ckan/*`;
  - `logs:CreateLogStream` e `logs:PutLogEvents` nos log groups `/mpb/ckan/*`;
  - `cloudwatch:PutMetricData` no namespace `MPB`;
  - `AmazonSSMManagedInstanceCore`.
- **Parâmetros**: um parâmetro por chave do `.env` de produção, em `/mpb/ckan/<CHAVE>`, com `SecureString` para senhas, URLs de banco com senha, segredos de sessão e JWT, senha do sysadmin e `CKAN__DATAPUSHER__API_TOKEN`. Os valores secretos são gravados pela operação, fora do state do Terraform.
- **Logs**: log groups `/mpb/ckan/nginx` e `/mpb/ckan/ckan`, com retenção de 14 dias.
- **Backup**: lifecycle que expira `backups/postgresql/` e `backups/ckan/` após 30 dias. Alarme quando a métrica `MPB/BackupSuccess` não chega em 26 horas.
- **Monitoramento**: alarmes de status da instância, CPU, memória e disco acima de 80%.
- **DNS**: registro A do domínio do portal apontando para o Elastic IP.

## mpb-ckan -> mpb-infra
A aplicação fornece:

- **Stack**: `docker-compose.yml` com Nginx, CKAN, PostgreSQL, Solr, Redis e DataPusher, todos com healthcheck. Só o Nginx publica portas (`80` e `443`).
- **Imagens**: construídas na EC2 a partir de uma tag do git, com `IMAGE_TAG` igual à tag. O registro (ECR) entra quando a infraestrutura fornecer repositório e OIDC.
- **Deploy**: script executado na EC2 que gera o `.env` a partir de `/mpb/ckan/`, faz dump do PostgreSQL, sobe a nova versão, verifica `/api/action/status_show` e a página inicial pelo Nginx e volta à versão anterior em caso de falha.
- **Certificado**: emissão e renovação pelo `certbot` do host, com desafio HTTP pela porta 80. Os certificados ficam em `/etc/letsencrypt`, lidos pelo Nginx.
- **Backup**: rotina diária na EC2 que envia `pg_dump` a `backups/postgresql/` e o volume `ckan_storage` a `backups/ckan/`, e publica `MPB/BackupSuccess` a cada execução bem-sucedida. Script de restauração, com reconstrução do índice de busca (`ckan search-index rebuild -c`).
- **Logs**: Nginx e CKAN enviam logs aos log groups `/mpb/ckan/nginx` e `/mpb/ckan/ckan` pelo driver `awslogs`.

Os arquivos das pesquisas ficam no volume `ckan_storage` e são servidos só pelo CKAN, que aplica a permissão de cada arquivo. O bucket não tem link público.

## mpb-data-pipelines -> mpb-ckan
As pipelines publicam e atualizam metadados e referências por API CKAN. A lógica de aquisição e transformação não deve ser incorporada ao ciclo de vida da aplicação CKAN.

As pipelines autenticam com token de API do usuário de serviço `mpb-pipelines`, editor da organização `movimento-pela-base`. Usuário e organização são criados na subida do CKAN por `ckan mpb setup-portal`. O token é gerado por um sysadmin com `ckan user token add mpb-pipelines <nome>` e entregue às pipelines pelo armazenamento de segredos da infraestrutura; nunca é versionado.

As categorias (grupos) são criadas e mantidas no portal pelos editores da organização `movimento-pela-base`. O `mpb-pipelines` não cria categorias nem pode ser membro delas: assim, o `package_update` das pipelines não remove pesquisas das categorias.

O schema do tipo `pesquisa` (`src/ckanext-mpb/ckanext/mpb/schemas/pesquisa.yaml`) implementa o mapeamento `src/mpb_data_pipelines/schemas/pesquisa.yaml` do mpb-data-pipelines. Os `field_name` e as `choices` dos dois arquivos devem ser iguais; uma mudança de campo exige mudança nos dois repositórios.

A exceção é `license_id`, que existe só no CKAN: a pesquisa criada sem licença recebe `cc-by-4.0` (CC BY 4.0), e uma atualização sem o campo mantém a licença atual. As pipelines não enviam o campo; a licença é editada pela equipe no portal.

Os campos com `mpb_private: true` no schema seguem o `access_roles` sem `publico` do mapeamento: só membros da organização dona da pesquisa e sysadmins os veem. Dos arquivos, só o tipo `documento` é público; `relatorio`, `sumario_executivo` e `ficha_site` são privados, e um arquivo sem `tipo_documento` também é tratado como privado.

Arquivos que precisam ser baixados pelo portal são enviados pela API do CKAN (upload no recurso), e não como link para o S3. A equipe também envia arquivos pelo portal; por isso, depois da primeira carga, as pipelines atualizam a pesquisa com `package_patch` sem `resources`. Um `package_update` com a lista de arquivos das pipelines apaga os arquivos enviados pela equipe.
