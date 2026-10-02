# Contribuição

O repositório usa desenvolvimento baseado em `main`: a branch é protegida e
toda mudança entra por Pull Request a partir de uma branch curta.

## Branches

Use `feature/<descricao>`, `fix/<descricao>`, `chore/<descricao>` ou
`docs/<descricao>`. Mantenha a branch pequena, atualize-a com `main` quando
necessário e remova-a após o merge. Não há branches permanentes `develop` ou
`release/*`.

## Antes de abrir o PR

```bash
cp .env.example .env
docker compose --env-file .env.example -f docker-compose.yml config --quiet
docker compose --env-file .env.example -f docker-compose.dev.yml config --quiet
tests/test_operations.sh
```

O CI também testa a extensão e constrói as imagens sem publicá-las. Deploy,
publicação em registro, migrations e alterações na EC2 pertencem a um fluxo de
CD separado, ainda não habilitado.

Segredos e `.env` nunca são versionados. Mudanças de contrato entre os três
repositórios devem ser documentadas no PR. Mudanças em decisões arquiteturais
existentes exigem ADR e revisão da liderança técnica.

Pull Requests abertos pelo Dependabot seguem os mesmos checks e revisão; não
há merge automático de atualizações.
