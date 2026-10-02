# mpb-ckan

Aplicação CKAN do Portal de Dados Movimento pela Base.

Este repositório deriva do baseline CKAN da ABC. A implantação alvo da V1 é AWS EC2 + Docker Compose. O workflow GCP existente no baseline foi removido para impedir implantação acidental na infraestrutura anterior.

## Responsabilidade
Dockerfiles, Docker Compose, Nginx, configuração CKAN, extensão MPB, templates, assets, schema de metadados, testes, verificações de integridade e scripts de deploy da aplicação.

## Repositórios relacionados
- `mpb-infra`: infraestrutura AWS/Terraform.
- `mpb-data-pipelines`: aquisição, transformação, qualidade e publicação de dados.

## Desenvolvimento local

```bash
cp .env.example .env
bin/compose build
bin/compose up -d --wait
```

O CKAN de desenvolvimento fica disponível em `http://localhost:5000`. Os
valores `CHANGE_ME` do exemplo são apenas para uso local e devem ser
substituídos por segredos fornecidos em runtime nos demais ambientes.

Os workflows do repositório validam os arquivos Compose, os scripts e a
extensão CKAN. O deploy AWS ainda deve ser implementado em conjunto com o
contrato entregue pelo `mpb-infra`; os scripts GCP do baseline não fazem parte
deste repositório.

Consulte `CONTRIBUTING.md`, `.github/BRANCH_PROTECTION.md` e `docs/CI_CD.md`
para o fluxo de Pull Request, quality gates e separação entre CI e CD.

## Baseline original
O README recebido com o projeto ABC foi preservado em `README.baseline.md`. Consulte também `docs/BASELINE_ABC.md` e `docs/CONTRACTS.md`.
