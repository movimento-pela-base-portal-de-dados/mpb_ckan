# Proteção recomendada para `main`

Aplicar uma ruleset de branch direcionada a `main` com:

- Pull Request obrigatório, com pelo menos uma aprovação;
- conversas resolvidas antes do merge;
- aprovação anterior descartada quando novos commits alterarem o PR;
- checks obrigatórios `Repository and Compose validation`,
  `Extension and API tests` e `Production image build`;
- branch atualizada com `main` antes do merge (`strict status checks`);
- bloqueio de force push e de deleção da branch;
- nenhuma exceção permanente para push direto;
- revisão por CODEOWNERS somente depois que `.github/CODEOWNERS` possuir owners reais.

O smoke test completo pode ser mantido como check adicional até sua duração e
estabilidade serem conhecidas. A ruleset depende de permissão administrativa
no GitHub e deve ser conferida em **Settings → Rules → Rulesets**.
