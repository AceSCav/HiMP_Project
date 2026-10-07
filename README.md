# HIMP Web

Aplicação Web Python/Django com interface responsiva em português. Uma instalação serve os navegadores de Windows, macOS e dispositivos móveis, sem compilar executáveis para cada plataforma. O desktop fica como referência durante a transição; a documentação original está em [docs/DESKTOP.md](docs/DESKTOP.md). O ponto de entrada Web é `web/manage.py`.

## Funcionalidades

- Painel com agenda, documentos pendentes e pagamentos em atraso.
- Relatórios financeiros com filtros por período/cliente, evolução mensal, distribuição dos valores, recebimentos por motivo e tempo de atraso. Gráficos acessíveis e valores consultáveis no navegador, sem exportação obrigatória.
- Pesquisa, criação, consulta, edição e eliminação protegida de clientes, processos, etapas, pagamentos, agendamentos e documentos solicitados.
- Histórico de etapas e registos associados ao cliente.
- Listas na base: estados civis, géneros, motivos/durações de agenda e documentos solicitados. Entidades, tipos de processo, fases, motivos e estados de pagamento reutilizam as tabelas atuais.
- Modelos DOCX na administração, download autenticado e renderização num ambiente de templates restrito.
- Google Calendar por OAuth Web, credenciais cifradas e sincronização explícita por agendamento.
- Django Auth: senhas protegidas, sessões no servidor, CSRF, limite de tentativas, permissões e auditoria.
- Montantes decimais e referências textuais para preservar zeros iniciais em novos registos.

## Desenvolvimento local

Python 3.13 recomendado. SQLite é permitido para desenvolvimento sem dados reais quando `DJANGO_DEBUG=true` e `DATABASE_URL` está vazia.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-web.txt
Copy-Item web/.env.example web/.env
python web/manage.py migrate
python web/manage.py bootstrap_roles
python web/manage.py createsuperuser
python web/manage.py runserver
```

Em macOS/Linux, use `source .venv/bin/activate` e `cp web/.env.example web/.env`; os comandos Python são iguais. Abra `http://127.0.0.1:8000`. A chave temporária de desenvolvimento só funciona com DEBUG e não deve ser usada em produção.

Não há registo público de contas. O administrador cria utilizadores em `/admin/`, atribui funções e define senhas temporárias de pelo menos 12 caracteres; cada pessoa altera a senha no menu da conta.

| Função | Acesso |
|---|---|
| Consulta | Consultar as seis áreas de gestão |
| Gestão | Consulta + criar/editar registos, gerar DOCX e sincronizar agenda |
| Administração | Gestão + eliminar registos e gerir listas |

O acesso ao admin exige também `is_staff`. Só o responsável técnico deve ser superuser: upload/edição dos modelos e ligação Google estão restritos a superusers de confiança. Contas sem função não veem registos. Esta versão assume **um único escritório**, com permissões por área; não implementa isolamento por organização, cliente ou advogado.

## Relatórios financeiros

Abra **Relatórios** no menu (exige `office.view_pagamento`). Escolha este mês, últimos seis meses, este ano ou um intervalo personalizado de até 36 meses; também pode filtrar por cliente.

Recebimentos usam a **data de conclusão**. Valores por receber usam a **data limite**, e os atrasados são um subconjunto dos pendentes, não um valor adicional a somar. A previsão inclui todos os pagamentos com vencimento no período, mesmo os já recebidos. Por isso, um pagamento recebido num mês diferente do vencimento aparece em meses distintos nas duas séries.

Os gráficos não dependem dos nomes hardcoded dos estados. Registos sem montante/data ou com montantes negativos são identificados; não são inventados valores. Há valores por mês acessíveis abaixo do gráfico. Despesas e lucro não são calculados, pois a aplicação só tem pagamentos de clientes.

## Base de dados e listas

Consulte [docs/MIGRATION.md](docs/MIGRATION.md) antes de ligar uma base Supabase existente. O ORM preserva nomes de tabelas e colunas. A Web liga diretamente ao PostgreSQL no servidor, sem chave Supabase de serviço no navegador. O `.env` do desktop continha exemplos e foi retirado do controlo de versões; `web/.env` é separado e não carrega esse ficheiro.

As listas são editadas em **Opções configuráveis**. Durações precisam de `minutes` para sincronizar com Google. Desativar uma opção mantém o valor histórico no respetivo registo; renomeá-la não reescreve dados antigos. `legacy_defaults.json` é o snapshot da migração `0004`, não a fonte em execução. Não o altere depois de aplicar migrações; faça mudanças futuras no admin/base.

## Documentos

O repositório original não inclui ficheiros DOCX. Os nove modelos são importados **inativos**; um superuser deve carregar os ficheiros reais (até 5 MB) e ativá-los. Configure `required_fields` como lista JSON, por exemplo `["nome", "nif", "endereço", "data_documento"]`. Os campos dos modelos originais são preservados. Dados do cliente são preenchidos automaticamente; contratos também aceitam valor, prestações e início. Documentos são gerados em memória e descarregados por uma rota autenticada.

`processo_anexo_principal` conserva uma referência textual. A área Documentos controla entregas, gera DOCX e permite guardar ficheiros de clientes no Google Drive. Valores por prestação são arredondados a cêntimos; confirme eventuais acertos no contrato.

## Google Drive por cliente

Ative a **Google Drive API** no mesmo projeto Google Cloud e adicione o escopo `https://www.googleapis.com/auth/drive.file` à configuração OAuth. Nas credenciais **Web application**, registe também o URI exato `https://seu-dominio/google/drive/callback/`. Configure `GOOGLE_DRIVE_REDIRECT_URI` no `web/.env` local ou no gestor de segredos da instalação, além de `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` e `TOKEN_ENCRYPTION_KEY` usados pela integração Google. Reinicie o servidor após alterar variáveis. Para testar em localhost, registe exatamente `http://127.0.0.1:8017/google/drive/callback/` e use esse valor; em produção use HTTPS.

Um superuser liga a conta em **Visão geral → Integração Google Drive → Ligar Google Drive**. A autorização do Drive é separada da agenda. O HIMP cria uma pasta principal **HIMP**, com subpastas **cliente_id - Nome**. No detalhe do cliente, **Criar pasta Google Drive** prepara a pasta; quando já existe, **Atualizar nome da pasta** conserva o ID e ajusta o nome. O primeiro upload também cria as pastas automaticamente.

Ao criar um registo em Documentos, pode enviar um ficheiro opcional; no detalhe de um registo sem ficheiro também existe **Guardar no Google Drive**. Aceita PDF, DOCX sem macros, JPG e PNG até 10 MB. O ficheiro é enviado pelo servidor; a base de dados guarda apenas IDs/referências e nome. **Gerar documento**, a partir do cliente, permite guardar o DOCX diretamente no Drive. No fluxo Cliente → Documentos → Ver todos → Novo registo, o cliente já fica associado e não precisa de ser escolhido novamente. Pesquisa, cancelamento e retorno à lista mantêm o contexto.

Os tokens OAuth são cifrados e não aparecem nos formulários/admin. Não torne públicas as pastas: abrir ficheiros no Drive exige uma conta Google com acesso. A integração trabalha com ficheiros criados pelo HIMP, sem importar automaticamente ficheiros adicionados manualmente pelo Drive nem gerir partilhas. Se o upload falhar, o registo local é preservado e pode repetir o envio; referências e hash permitem recuperar um envio remoto concluído sem duplicar o mesmo ficheiro. Cada registo aceita um ficheiro; para nova versão crie outro registo. Um documento ligado ao Drive não pode mudar de cliente pelo formulário. Eliminar um registo local preserva o ficheiro/pasta no Drive.

A migração `0005` adiciona as referências de pastas/ficheiros e a tabela privada de ligação. Reveja também `docs/supabase_hardening.sql` para bloquear acesso público à nova tabela. Nenhuma conta Google é ligada automaticamente; é necessário configurar as credenciais e autorizar a conta do escritório. A aplicação continua a funcionar sem Drive para os registos locais.

## Google Calendar

No Google Cloud, crie um OAuth client **Web application** com o URI HTTPS exato `/google/callback/` da instalação. Configure no servidor `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `GOOGLE_CALENDAR_ID` e `TOKEN_ENCRYPTION_KEY`. Gere a chave com:

```sh
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Guarde a chave num gestor de segredos e backup seguro; sem ela os tokens não são recuperáveis. O superuser liga a conta pelo painel; a agenda é partilhada pelo escritório. O escopo é apenas `calendar.events`. No detalhe, **Sincronizar agendamento** envia criação/alteração para Google. Falhas preservam o registo local; IDs determinísticos tornam reenvios mais seguros.

Não há sincronização automática/inversa das alterações feitas no Google. Eliminar localmente não elimina o evento remoto; a confirmação informa-o. IDs legados do Google são preservados.

## Publicação

```sh
docker compose build
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py bootstrap_roles
docker compose run --rm web python manage.py createsuperuser
docker compose up -d
```

Para bases existentes use o procedimento de migração documentado. Migrações não correm no arranque. O container usa Gunicorn e um utilizador sem privilégios; o volume de modelos é privado.

Em `web/.env` defina `DJANGO_DEBUG=false`, uma `DJANGO_SECRET_KEY` aleatória, `DATABASE_URL` PostgreSQL com TLS (`sslmode=verify-full` e CA apropriada), `DJANGO_ALLOWED_HOSTS` com o domínio real e `DJANGO_CSRF_TRUSTED_ORIGINS=https://seu-dominio`. Use HTTPS num reverse proxy; Compose publica HTTP apenas em `127.0.0.1`. `TRUST_HTTPS_PROXY=true` só deve ser ativado quando o proxy remove o cabeçalho recebido do cliente e define `X-Forwarded-Proto` corretamente. HSTS inclui subdomínios, que também devem usar HTTPS.

Use uma role PostgreSQL de runtime com acesso apenas às tabelas necessárias, sem DDL nem superuser; execute migrações com outra role. Depois da transição, reveja [docs/supabase_hardening.sql](docs/supabase_hardening.sql) para retirar acesso público às tabelas HIMP e Django pela API Supabase. As permissões Django não protegem outros canais de acesso à base.

Faça backups da base, de `private_media` e da chave de cifragem. Execute `clearsessions` e `axes_reset_logs` segundo a política de retenção. `/health/` confirma que o processo responde, não verifica a base. Não versione credenciais, modelos reais nem logs privados.

## Validação

```sh
python web/manage.py test office
python web/manage.py makemigrations --check --dry-run
python web/manage.py collectstatic --noinput
python web/manage.py check --deploy --fail-level WARNING
```

O último comando deve usar configurações de produção. O workflow GitHub Actions testa PostgreSQL 16. Consulte a [lista oficial de publicação do Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).

Antes de usar dados reais: testar a migração numa cópia, verificar contas/permissões, carregar DOCX e testar OAuth com a conta do escritório. MFA, recuperação por email, anexos e isolamento entre escritórios são evoluções adicionais.
