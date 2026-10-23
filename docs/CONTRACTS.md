# Contratos entre repositórios

## mpb-infra -> mpb-ckan
A infraestrutura fornece host EC2, EBS persistente, acesso a S3, IAM Role, parâmetros/segredos, observabilidade e endpoint de rede necessários à execução da aplicação.

## mpb-ckan -> mpb-infra
A aplicação fornece Docker Compose, imagens/versionamento, portas internas, healthchecks, requisitos de persistência e variáveis de ambiente necessárias ao deploy.

## mpb-data-pipelines -> mpb-ckan
As pipelines publicam e atualizam metadados e referências por API CKAN. A lógica de aquisição e transformação não deve ser incorporada ao ciclo de vida da aplicação CKAN.

As pipelines autenticam com token de API do usuário de serviço `mpb-pipelines`, editor da organização `movimento-pela-base`. Usuário e organização são criados na subida do CKAN por `ckan mpb setup-portal`. O token é gerado por um sysadmin com `ckan user token add mpb-pipelines <nome>` e entregue às pipelines pelo armazenamento de segredos da infraestrutura; nunca é versionado.

O schema do tipo `pesquisa` (`src/ckanext-mpb/ckanext/mpb/schemas/pesquisa.yaml`) implementa o mapeamento `src/mpb_data_pipelines/schemas/pesquisa.yaml` do mpb-data-pipelines. Os `field_name` e as `choices` dos dois arquivos devem ser iguais; uma mudança de campo exige mudança nos dois repositórios.
