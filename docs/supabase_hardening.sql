-- Run only after cutover, on the HIMP database, reviewed with your DB administrator.
-- The desktop used the service-role API; the Web app uses direct PostgreSQL.
-- Block public Supabase Data API access to HIMP and Django authentication tables.
-- This does not alter other applications' tables, create users, or change passwords.
DO $$
DECLARE
  table_name text;
  role_name text;
BEGIN
  FOREACH table_name IN ARRAY ARRAY[
    'cliente','processo','etapa_processo','entidade','tipo_do_processo',
    'lista_fases_processo','pagamento','motivo','status_pagamento',
    'agendamento','documentos_cliente','users',
    'office_configuration','office_documenttemplate','office_calendarconnection',
    'office_auditevent','auth_user','auth_group','auth_permission',
    'auth_user_groups','auth_user_user_permissions','auth_group_permissions',
    'django_session','django_admin_log','django_content_type','django_migrations',
    'axes_accessattempt','axes_accesslog','axes_accessfailurelog'
  ] LOOP
    IF to_regclass(format('public.%I', table_name)) IS NOT NULL THEN
      EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC', table_name);
      FOREACH role_name IN ARRAY ARRAY['anon','authenticated'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
          EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I', table_name, role_name);
        END IF;
      END LOOP;
    END IF;
  END LOOP;
END $$;
-- Use a dedicated runtime role with SELECT/INSERT/UPDATE/DELETE + sequence USAGE
-- on these tables only, no DDL, no superuser, and no Supabase service-role key.
-- Apply migrations using a separate schema-owner role. Explicit RLS policies
-- must be reviewed if RLS is already enabled; this script does not disable RLS.
-- Retire public.users after all accounts have been recreated in Django Auth.
