# Separação entre CI e CD

## CI desta etapa

Pull Requests validam arquivos Compose e scripts, executam testes da extensão,
constroem as imagens Docker sem publicá-las e podem executar o smoke test da
stack de desenvolvimento. Os workflows possuem apenas permissão de leitura do
conteúdo e não usam credenciais de cloud ou registro.

## CD futuro

Após o merge, o fluxo futuro poderá publicar imagens e implantar a EC2, mas
isso deve ficar em workflow separado, com aprovação de ambiente e credenciais
de curta duração. O registro definitivo (ECR, GHCR ou outro) ainda não foi
decidido e não deve ser presumido nesta etapa.

Imagens publicadas deverão receber uma tag imutável rastreável ao commit
(`sha-<commit>`) e, quando houver release, uma tag semântica. `latest` não deve
ser a única referência usada em produção. Publicação, migrations, atualização
da EC2, verificações pós-deploy e rollback pertencem ao CD e não estão
habilitados agora.

Secrets futuros, ainda não criados, dependerão da decisão de registro e do
método de autenticação AWS. Não usar AWS Access Keys de longa duração nem
reaproveitar secrets da implantação GCP do baseline.
