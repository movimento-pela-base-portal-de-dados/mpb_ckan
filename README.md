# mpb-ckan

Aplicação CKAN do Portal de Dados Movimento pela Base.

Este repositório deriva do baseline CKAN da ABC. A implantação alvo da V1 é AWS EC2 + Docker Compose. O workflow GCP existente no baseline foi removido para impedir implantação acidental na infraestrutura anterior.

## Responsabilidade
Dockerfiles, Docker Compose, Nginx, configuração CKAN, extensão MPB, templates, assets, schema de metadados, testes, verificações de integridade e scripts de deploy da aplicação.

## Repositórios relacionados
- `mpb-infra`: infraestrutura AWS/Terraform.
- `mpb-data-pipelines`: aquisição, transformação, qualidade e publicação de dados.

## Baseline original
O README recebido com o projeto ABC foi preservado em `README.baseline.md`. Consulte também `docs/BASELINE_ABC.md` e `docs/CONTRACTS.md`.
