-- OrgFlow: enable RLS on public tables (best practice, idempotent).
--
-- Safe with current architecture:
--   * Backend uses Supabase service_role → bypasses RLS (no API breakage).
--   * Browser uses anon + Supabase Auth only for Realtime; SELECT policies below.
--   * Policies match ACTUAL columns (organization_id vs project_id vs joins).
--
-- Apply in Supabase Dashboard → SQL Editor. Safe to re-run.

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.orgflow_jwt_organization_id()
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT COALESCE(
    NULLIF(auth.jwt() -> 'app_metadata' ->> 'organization_id', '')::uuid,
    (SELECT p.organization_id FROM public.profiles AS p WHERE p.id = auth.uid())
  );
$$;

REVOKE ALL ON FUNCTION public.orgflow_jwt_organization_id() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.orgflow_jwt_organization_id() TO authenticated;

CREATE OR REPLACE FUNCTION public._orgflow_table_has_column(
  p_table text,
  p_column text
)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM information_schema.columns AS c
    WHERE c.table_schema = 'public'
      AND c.table_name = p_table
      AND c.column_name = p_column
  );
$$;

CREATE OR REPLACE FUNCTION public._orgflow_enable_rls(p_table text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  EXECUTE format(
    'ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',
    p_table
  );
  EXECUTE format(
    'ALTER TABLE public.%I FORCE ROW LEVEL SECURITY',
    p_table
  );
END;
$$;

-- Enable RLS and one authenticated SELECT policy based on available columns.
CREATE OR REPLACE FUNCTION public._orgflow_apply_table_rls(p_table text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  policy_name text := p_table || '_authenticated_select';
  using_expr text;
BEGIN
  IF to_regclass('public.' || p_table) IS NULL THEN
    RETURN;
  END IF;

  PERFORM public._orgflow_enable_rls(p_table);
  EXECUTE format(
    'DROP POLICY IF EXISTS %I ON public.%I',
    policy_name,
    p_table
  );

  IF public._orgflow_table_has_column(p_table, 'organization_id') THEN
    using_expr := 'organization_id = public.orgflow_jwt_organization_id()';
  ELSIF public._orgflow_table_has_column(p_table, 'project_id') THEN
    using_expr :=
      'project_id IN ('
      || 'SELECT p.id FROM public.projects AS p '
      || 'WHERE p.organization_id = public.orgflow_jwt_organization_id())';
  ELSIF public._orgflow_table_has_column(p_table, 'report_id')
    AND to_regclass('public.weekly_reports') IS NOT NULL
    AND public._orgflow_table_has_column('weekly_reports', 'project_id') THEN
    using_expr :=
      'report_id IN ('
      || 'SELECT wr.id FROM public.weekly_reports AS wr '
      || 'INNER JOIN public.projects AS p ON p.id = wr.project_id '
      || 'WHERE p.organization_id = public.orgflow_jwt_organization_id())';
  ELSIF public._orgflow_table_has_column(p_table, 'action_id')
    AND to_regclass('public.operational_actions') IS NOT NULL
    AND public._orgflow_table_has_column('operational_actions', 'project_id') THEN
    using_expr := format(
      'EXISTS ('
      || 'SELECT 1 FROM public.operational_actions AS o '
      || 'INNER JOIN public.projects AS p ON p.id = o.project_id '
      || 'WHERE o.id = %I.action_id '
      || 'AND p.organization_id = public.orgflow_jwt_organization_id())',
      p_table
    );
  ELSE
    -- Backend-only table for authenticated clients (service_role still bypasses).
    RETURN;
  END IF;

  EXECUTE format(
    'CREATE POLICY %I ON public.%I FOR SELECT TO authenticated USING (%s)',
    policy_name,
    p_table,
    using_expr
  );
END;
$$;

-- ---------------------------------------------------------------------------
-- Application tables (keep in sync with app/db/schema_registry.py)
-- ---------------------------------------------------------------------------

DO $migration$
DECLARE
  app_tables text[] := ARRAY[
    'projects',
    'weekly_reports',
    'ai_interpretations',
    'operational_actions',
    'automation_runs',
    'ai_execution_logs',
    'organization_field_report_modules',
    'field_visit_reports',
    'field_visit_report_lines',
    'field_visit_report_line_photos',
    'ai_operation_fingerprints',
    'circuit_breakers',
    'automation_locks',
    'approval_requests',
    'workflow_runs',
    'ai_logs',
    'reports',
    'findings'
  ];
  t text;
BEGIN
  FOREACH t IN ARRAY app_tables LOOP
    PERFORM public._orgflow_apply_table_rls(t);
  END LOOP;
END;
$migration$;

-- organizations
DO $organizations$
BEGIN
  IF to_regclass('public.organizations') IS NOT NULL THEN
    PERFORM public._orgflow_enable_rls('organizations');
    DROP POLICY IF EXISTS organizations_authenticated_select ON public.organizations;
    CREATE POLICY organizations_authenticated_select ON public.organizations
      FOR SELECT
      TO authenticated
      USING (id = public.orgflow_jwt_organization_id());
  END IF;
END;
$organizations$;

-- profiles: own row only
DO $profiles$
BEGIN
  IF to_regclass('public.profiles') IS NOT NULL THEN
    PERFORM public._orgflow_enable_rls('profiles');
    DROP POLICY IF EXISTS profiles_authenticated_select ON public.profiles;
    CREATE POLICY profiles_authenticated_select ON public.profiles
      FOR SELECT
      TO authenticated
      USING (id = auth.uid());
  END IF;
END;
$profiles$;

-- notifications (Realtime)
DO $notifications$
BEGIN
  IF to_regclass('public.notifications') IS NOT NULL THEN
    PERFORM public._orgflow_enable_rls('notifications');
    DROP POLICY IF EXISTS notifications_authenticated_select ON public.notifications;
    CREATE POLICY notifications_authenticated_select ON public.notifications
      FOR SELECT
      TO authenticated
      USING (profile_id = auth.uid());
  END IF;
END;
$notifications$;

-- action_comments (Realtime) — explicit join (action_id column)
DO $action_comments$
BEGIN
  IF to_regclass('public.action_comments') IS NOT NULL THEN
    PERFORM public._orgflow_enable_rls('action_comments');
    DROP POLICY IF EXISTS action_comments_authenticated_select ON public.action_comments;
    IF public._orgflow_table_has_column('action_comments', 'action_id')
      AND to_regclass('public.operational_actions') IS NOT NULL THEN
      CREATE POLICY action_comments_authenticated_select ON public.action_comments
        FOR SELECT
        TO authenticated
        USING (
          EXISTS (
            SELECT 1
            FROM public.operational_actions AS o
            INNER JOIN public.projects AS p ON p.id = o.project_id
            WHERE o.id = action_comments.action_id
              AND p.organization_id = public.orgflow_jwt_organization_id()
          )
        );
    END IF;
  END IF;
END;
$action_comments$;

-- workspace_activity (Realtime)
DO $workspace_activity$
BEGIN
  IF to_regclass('public.workspace_activity') IS NOT NULL THEN
    PERFORM public._orgflow_apply_table_rls('workspace_activity');
  END IF;
END;
$workspace_activity$;

-- Cleanup helper functions used only during install (keep orgflow_jwt_organization_id)
DROP FUNCTION IF EXISTS public._orgflow_table_has_column(text, text);
DROP FUNCTION IF EXISTS public._orgflow_enable_rls(text);
DROP FUNCTION IF EXISTS public._orgflow_apply_table_rls(text);
DROP FUNCTION IF EXISTS public._orgflow_policy_tenant_select(text);
