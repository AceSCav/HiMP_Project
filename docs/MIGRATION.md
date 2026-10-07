# Migrar HIMP desktop para Web

## Preparar staging

1. Exporte a base com dados, constraints, sequences e políticas; teste o restauro.
2. Crie uma cópia isolada de staging. Mantenha o desktop na base original durante os testes.
3. Configure `DATABASE_URL` para a cópia, usando PostgreSQL diretamente, não a chave Supabase de serviço.
4. Execute `python web/manage.py check_legacy_schema`. É só de leitura: verifica tabelas/colunas e montantes inválidos. Compare também tipos, constraints e políticas reais com `0001_legacy_schema`.

## Aplicar as migrações

```sh
python web/manage.py migrate office 0001 --fake-initial
python web/manage.py migrate --plan
python web/manage.py migrate
python web/manage.py bootstrap_roles
python web/manage.py createsuperuser
```

`0001` contém apenas as onze tabelas originais de negócio. `--fake-initial` reconhece-as sem recriar. `0002` cria as tabelas Web; Django cria Auth/Sessions; `0003` altera tipos financeiros/horários; `0004` importa catálogos e metadados de modelos; `0005` adiciona referências de pastas/ficheiros Google Drive e a tabela privada de ligação Google Drive. A pré-verificação compara as colunas de `0001`, sem exigir antecipadamente os novos campos Web. A tabela antiga `users` não é usada pela Web.

Numa **base vazia**, execute apenas `migrate`. Num esquema parcial/diferente, não use `--fake` para contornar erros nem apague tabelas: prepare uma migração explícita para a estrutura real.

## Alterações a verificar

- `pagamento.montante`: `real` passa a `numeric(14,2)`, com arredondamento a cêntimos. Exporte/reconcilie valores e totais. Corrija NaN, infinitos, negativos e montantes fora do limite antes de migrar.
- `pagamento.referencia` e `entidade`: inteiros passam a texto. Novos valores preservam zeros; zeros históricos já perdidos exigem consulta à fonte original.
- `agendamento.data_inicio`: timestamps sem fuso passam a `timestamptz`, interpretados como hora local **Europe/Lisbon**, conforme o código desktop. Confirme esta hipótese; se eram UTC/outro fuso, ajuste a migração antes de executá-la. Revise transições de horário de verão.
- Catálogos recebem valores fixos e históricos sem reescrever dados dos clientes. Os campos textuais mantêm a compatibilidade com o esquema atual.
- Não se importam as senhas em texto simples de `public.users`. Recrie contas no Django Auth, atribua funções e entregue novas senhas por um canal seguro. A mudança inicial de senha é um procedimento operacional, não uma obrigação automática da aplicação.
- Os nove modelos DOCX são criados inativos; carregue os ficheiros reais no admin, pois não constam do repositório.

`0003` é deliberadamente irreversível. Voltar aos tipos antigos perde precisão/referências; use backup/restauro para recuperação.

## Validar e fazer a transição

Compare quantidades e IDs de todas as tabelas, relações, valores financeiros, acentos, identificadores vazios e datas antes/depois. Teste as funções Consulta/Gestão/Administração e contas sem função. Valide HTTPS/cookies, DOCX reais e OAuth em staging. Esta versão tem um único escritório e sincronização Google explícita de criação/alteração; a remoção local não apaga o evento remoto.

Agende uma janela de manutenção, pare escritas no desktop e faça um novo backup. Aplique o procedimento validado na base final. Publique sob HTTPS e distribua contas/endereço.

Reveja `supabase_hardening.sql`: retire acesso público HIMP/Django pela API Supabase, incluindo grants herdados, funções RPC e RLS. O script não configura roles nem altera senhas; a role Web precisa de grants e políticas adequados, sem privilégios globais. Retire a chave de serviço do desktop de circulação. Arquive/remova a tabela `public.users` com senhas antigas depois de confirmar todas as contas novas.

Em caso de erro, pare as escritas Web e restaure o backup pré-migração numa base isolada antes de redirecionar o desktop. Reconcile alterações feitas depois da transição; restaurar sem reconciliação perde dados. Ensaie esse procedimento em staging.
