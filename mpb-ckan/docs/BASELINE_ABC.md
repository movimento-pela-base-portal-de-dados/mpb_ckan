# Baseline ABC

Este repositório foi inicializado a partir do projeto CKAN da ABC disponibilizado como referência técnica.

## Mantido como padrão inicial
- Docker Compose para execução da stack.
- CKAN, Nginx, PostgreSQL, Solr, Redis e DataPusher.
- Healthchecks e redes internas Docker.
- Estrutura de extensão CKAN em `src/`.
- Testes automatizados existentes.

## Não herdado como decisão arquitetural
- Implantação específica em Google Cloud.
- Workflow de deploy para VM GCP.
- Reinício diário do stack como requisito operacional.

A implantação do Movimento pela Base será definida pelo contrato com `mpb-infra` e executada em AWS EC2 na V1.
