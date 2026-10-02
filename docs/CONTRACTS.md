# Contratos entre repositórios

## mpb-infra -> mpb-ckan
A infraestrutura fornece host EC2, EBS persistente, acesso a S3, IAM Role, parâmetros/segredos, observabilidade e endpoint de rede necessários à execução da aplicação.

## mpb-ckan -> mpb-infra
A aplicação fornece Docker Compose, imagens/versionamento, portas internas, healthchecks, requisitos de persistência e variáveis de ambiente necessárias ao deploy.

## mpb-data-pipelines -> mpb-ckan
As pipelines publicam e atualizam metadados e referências por API CKAN. A lógica de aquisição e transformação não deve ser incorporada ao ciclo de vida da aplicação CKAN.
