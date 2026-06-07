"""
Canonical schema metadata for OrgFlow Supabase tables.
Used by database hardening services for migrations, RLS, FK, and indexes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForeignKeyDef:
    column: str
    references_table: str
    references_column: str = "id"
    on_delete: str = "RESTRICT"


@dataclass(frozen=True)
class IndexDef:
    name: str
    columns: tuple[str, ...]
    unique: bool = False


@dataclass(frozen=True)
class RlsPolicyDef:
    name: str
    command: str
    using_expression: str
    check_expression: str | None = None


@dataclass(frozen=True)
class TableSchema:
    name: str
    tenant_column: str | None = None
    soft_delete_column: str | None = "deleted_at"
    foreign_keys: tuple[ForeignKeyDef, ...] = ()
    indexes: tuple[IndexDef, ...] = ()
    rls_policies: tuple[RlsPolicyDef, ...] = ()
    audited: bool = True


SCHEMA_VERSION = "2026060702"

# Matches deploy/sql/20260604_enable_rls_best_practice.sql (authenticated SELECT + service_role bypass).
ORGFLOW_TENANT_ISOLATION = (
    "organization_id = public.orgflow_jwt_organization_id()"
)
ORGFLOW_ORGANIZATION_ISOLATION = (
    "id = public.orgflow_jwt_organization_id()"
)
ORGFLOW_PROFILE_SELF = "id = auth.uid()"
ORGFLOW_PROJECT_SCOPE = (
    "project_id IN ("
    "SELECT p.id FROM public.projects AS p "
    "WHERE p.organization_id = public.orgflow_jwt_organization_id()"
    ")"
)

TABLES: dict[str, TableSchema] = {
    "organizations": TableSchema(
        name="organizations",
        tenant_column=None,
        soft_delete_column="deleted_at",
        indexes=(
            IndexDef("organizations_pkey", ("id",), unique=True),
            IndexDef("organizations_name_idx", ("name",)),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="organizations_authenticated_select",
                command="SELECT",
                using_expression=ORGFLOW_ORGANIZATION_ISOLATION,
            ),
        ),
    ),
    "projects": TableSchema(
        name="projects",
        tenant_column="organization_id",
        foreign_keys=(
            ForeignKeyDef("organization_id", "organizations"),
        ),
        indexes=(
            IndexDef("projects_pkey", ("id",), unique=True),
            IndexDef("projects_org_idx", ("organization_id",)),
            IndexDef("projects_org_name_idx", ("organization_id", "project_name")),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="projects_tenant_isolation",
                command="SELECT",
                using_expression=ORGFLOW_TENANT_ISOLATION,
            ),
        ),
    ),
    "profiles": TableSchema(
        name="profiles",
        tenant_column="organization_id",
        foreign_keys=(
            ForeignKeyDef("organization_id", "organizations"),
        ),
        indexes=(
            IndexDef("profiles_pkey", ("id",), unique=True),
            IndexDef("profiles_org_idx", ("organization_id",)),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="profiles_authenticated_select",
                command="SELECT",
                using_expression=ORGFLOW_PROFILE_SELF,
            ),
        ),
    ),
    "weekly_reports": TableSchema(
        name="weekly_reports",
        tenant_column=None,
        foreign_keys=(
            ForeignKeyDef("project_id", "projects"),
        ),
        indexes=(
            IndexDef("weekly_reports_pkey", ("id",), unique=True),
            IndexDef("weekly_reports_project_idx", ("project_id",)),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="weekly_reports_authenticated_select",
                command="SELECT",
                using_expression=ORGFLOW_PROJECT_SCOPE,
            ),
        ),
    ),
    "ai_interpretations": TableSchema(
        name="ai_interpretations",
        tenant_column=None,
        foreign_keys=(
            ForeignKeyDef("report_id", "weekly_reports"),
            ForeignKeyDef("project_id", "projects"),
        ),
        indexes=(
            IndexDef("ai_interpretations_pkey", ("id",), unique=True),
            IndexDef("ai_interpretations_report_idx", ("report_id",)),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="ai_interpretations_authenticated_select",
                command="SELECT",
                using_expression=(
                    "report_id IN ("
                    "SELECT wr.id FROM public.weekly_reports AS wr "
                    "INNER JOIN public.projects AS p ON p.id = wr.project_id "
                    "WHERE p.organization_id = public.orgflow_jwt_organization_id())"
                ),
            ),
        ),
    ),
    "operational_actions": TableSchema(
        name="operational_actions",
        tenant_column="organization_id",
        foreign_keys=(
            ForeignKeyDef("project_id", "projects"),
        ),
        indexes=(
            IndexDef("operational_actions_pkey", ("id",), unique=True),
            IndexDef("operational_actions_project_status_idx", ("project_id", "status")),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="operational_actions_tenant_isolation",
                command="SELECT",
                using_expression=ORGFLOW_TENANT_ISOLATION,
            ),
        ),
    ),
    "automation_runs": TableSchema(
        name="automation_runs",
        tenant_column="organization_id",
        foreign_keys=(
            ForeignKeyDef("project_id", "projects", on_delete="SET NULL"),
        ),
        indexes=(
            IndexDef("automation_runs_pkey", ("id",), unique=True),
            IndexDef("automation_runs_status_idx", ("status", "created_at")),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="automation_runs_tenant_isolation",
                command="SELECT",
                using_expression=ORGFLOW_TENANT_ISOLATION,
            ),
        ),
    ),
    "circuit_breakers": TableSchema(
        name="circuit_breakers",
        tenant_column=None,
        soft_delete_column=None,
        indexes=(
            IndexDef("circuit_breakers_pkey", ("id",), unique=True),
            IndexDef("circuit_breakers_key_idx", ("breaker_key",), unique=True),
        ),
        rls_policies=(),
        audited=False,
    ),
    "ai_execution_logs": TableSchema(
        name="ai_execution_logs",
        tenant_column="organization_id",
        indexes=(
            IndexDef("ai_execution_logs_pkey", ("id",), unique=True),
            IndexDef("ai_execution_logs_org_created_idx", ("organization_id", "created_at")),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="ai_execution_logs_tenant_isolation",
                command="SELECT",
                using_expression=ORGFLOW_TENANT_ISOLATION,
            ),
        ),
    ),
    "organization_field_report_modules": TableSchema(
        name="organization_field_report_modules",
        tenant_column="organization_id",
        foreign_keys=(
            ForeignKeyDef("organization_id", "organizations"),
        ),
        indexes=(
            IndexDef(
                "organization_field_report_modules_pkey",
                ("organization_id",),
                unique=True,
            ),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="organization_field_report_modules_tenant_isolation",
                command="SELECT",
                using_expression=ORGFLOW_TENANT_ISOLATION,
            ),
        ),
        audited=False,
    ),
    "field_visit_reports": TableSchema(
        name="field_visit_reports",
        tenant_column="organization_id",
        foreign_keys=(
            ForeignKeyDef("organization_id", "organizations"),
            ForeignKeyDef("project_id", "projects"),
        ),
        indexes=(
            IndexDef("field_visit_reports_pkey", ("id",), unique=True),
            IndexDef("field_visit_reports_org_idx", ("organization_id",)),
            IndexDef("field_visit_reports_project_idx", ("project_id",)),
            IndexDef(
                "field_visit_reports_org_status_idx",
                ("organization_id", "status"),
            ),
            IndexDef(
                "field_visit_reports_client_report_uuid_uniq",
                ("client_report_uuid",),
                unique=True,
            ),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="field_visit_reports_tenant_isolation",
                command="SELECT",
                using_expression=ORGFLOW_TENANT_ISOLATION,
            ),
        ),
    ),
    "field_visit_report_lines": TableSchema(
        name="field_visit_report_lines",
        tenant_column="organization_id",
        foreign_keys=(
            ForeignKeyDef("organization_id", "organizations"),
            ForeignKeyDef("report_id", "field_visit_reports"),
        ),
        indexes=(
            IndexDef(
                "field_visit_report_lines_pkey",
                ("id",),
                unique=True,
            ),
            IndexDef(
                "field_visit_report_lines_report_idx",
                ("report_id", "sort_order"),
            ),
            IndexDef(
                "field_visit_report_lines_org_idx",
                ("organization_id",),
            ),
            IndexDef(
                "field_visit_report_lines_client_line_uuid_uniq",
                ("client_line_uuid",),
                unique=True,
            ),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="field_visit_report_lines_tenant_isolation",
                command="SELECT",
                using_expression=ORGFLOW_TENANT_ISOLATION,
            ),
        ),
    ),
    "field_visit_report_line_photos": TableSchema(
        name="field_visit_report_line_photos",
        tenant_column="organization_id",
        foreign_keys=(
            ForeignKeyDef("organization_id", "organizations"),
            ForeignKeyDef("report_id", "field_visit_reports"),
            ForeignKeyDef("line_id", "field_visit_report_lines"),
        ),
        indexes=(
            IndexDef(
                "field_visit_report_line_photos_pkey",
                ("id",),
                unique=True,
            ),
            IndexDef(
                "field_visit_report_line_photos_line_idx",
                ("line_id", "sort_order"),
            ),
            IndexDef(
                "field_visit_report_line_photos_org_idx",
                ("organization_id",),
            ),
        ),
        rls_policies=(
            RlsPolicyDef(
                name="field_visit_report_line_photos_tenant_isolation",
                command="SELECT",
                using_expression=ORGFLOW_TENANT_ISOLATION,
            ),
        ),
    ),
    "notifications": TableSchema(
        name="notifications",
        tenant_column=None,
        soft_delete_column=None,
        rls_policies=(
            RlsPolicyDef(
                name="notifications_authenticated_select",
                command="SELECT",
                using_expression="profile_id = auth.uid()",
            ),
        ),
        audited=False,
    ),
    "action_comments": TableSchema(
        name="action_comments",
        tenant_column=None,
        soft_delete_column=None,
        rls_policies=(
            RlsPolicyDef(
                name="action_comments_authenticated_select",
                command="SELECT",
                using_expression=(
                    "EXISTS (SELECT 1 FROM operational_actions o "
                    "JOIN projects p ON p.id = o.project_id "
                    "WHERE o.id = action_comments.action_id "
                    "AND p.organization_id = public.orgflow_jwt_organization_id())"
                ),
            ),
        ),
        audited=False,
    ),
    "workspace_activity": TableSchema(
        name="workspace_activity",
        tenant_column=None,
        soft_delete_column=None,
        rls_policies=(
            RlsPolicyDef(
                name="workspace_activity_authenticated_select",
                command="SELECT",
                using_expression=ORGFLOW_PROJECT_SCOPE,
            ),
        ),
        audited=False,
    ),
    "reports": TableSchema(
        name="reports",
        tenant_column=None,
        soft_delete_column=None,
        rls_policies=(
            RlsPolicyDef(
                name="reports_authenticated_select",
                command="SELECT",
                using_expression=ORGFLOW_PROJECT_SCOPE,
            ),
        ),
        audited=False,
    ),
    "findings": TableSchema(
        name="findings",
        tenant_column=None,
        soft_delete_column=None,
        rls_policies=(
            RlsPolicyDef(
                name="findings_authenticated_select",
                command="SELECT",
                using_expression=ORGFLOW_PROJECT_SCOPE,
            ),
        ),
        audited=False,
    ),
    "automation_locks": TableSchema(
        name="automation_locks",
        tenant_column=None,
        soft_delete_column=None,
        rls_policies=(),
        audited=False,
    ),
    "approval_requests": TableSchema(
        name="approval_requests",
        tenant_column=None,
        soft_delete_column=None,
        rls_policies=(),
        audited=False,
    ),
    "workflow_runs": TableSchema(
        name="workflow_runs",
        tenant_column=None,
        soft_delete_column=None,
        rls_policies=(),
        audited=False,
    ),
    "ai_logs": TableSchema(
        name="ai_logs",
        tenant_column=None,
        soft_delete_column=None,
        rls_policies=(),
        audited=False,
    ),
    "ai_operation_fingerprints": TableSchema(
        name="ai_operation_fingerprints",
        tenant_column="organization_id",
        rls_policies=(
            RlsPolicyDef(
                name="ai_operation_fingerprints_authenticated_select",
                command="SELECT",
                using_expression=ORGFLOW_TENANT_ISOLATION,
            ),
        ),
        audited=False,
    ),
}


MIGRATION_SCRIPTS: list[dict] = [
    {
        "version": "2026052901",
        "name": "initial_hardening_baseline",
        "description": "Baseline schema registry and tenant isolation columns",
        "tables": list(TABLES.keys()),
    },
    {
        "version": "2026052902",
        "name": "add_soft_delete_columns",
        "description": "Add deleted_at to tenant-scoped tables",
        "tables": [
            name
            for name, schema in TABLES.items()
            if schema.soft_delete_column
        ],
    },
    {
        "version": "2026053101",
        "name": "profiles_tenant_isolation",
        "description": "Add organization_id to profiles and owner_profile_id to organizations",
        "tables": ["profiles", "organizations"],
    },
    {
        "version": "2026053102",
        "name": "add_project_stakeholder_columns",
        "description": "Add developer_name, contractor_name, and lawyer_name to projects",
        "tables": ["projects"],
    },
    {
        "version": "2026053103",
        "name": "backfill_project_stakeholder_defaults",
        "description": "Backfill missing project stakeholder fields with placeholder values",
        "tables": ["projects"],
    },
    {
        "version": "2026053104",
        "name": "enforce_single_client_admin",
        "description": "Demote duplicate client admins and enforce one ADMIN per organization",
        "tables": ["profiles", "organizations"],
    },
    {
        "version": "2026060101",
        "name": "organization_field_report_module",
        "description": (
            "Field report module toggle per organization "
            "+ optional report header columns on organizations"
        ),
        "tables": [
            "organization_field_report_modules",
            "organizations",
        ],
    },
    {
        "version": "2026060102",
        "name": "field_visit_reports",
        "description": "Weekly field visit reports for the production module",
        "tables": ["field_visit_reports"],
    },
    {
        "version": "2026060103",
        "name": "field_visit_report_lines",
        "description": "Finding rows on field visit reports",
        "tables": ["field_visit_report_lines"],
    },
    {
        "version": "2026060301",
        "name": "field_visit_report_line_grouping",
        "description": (
            "Row grouping columns on field visit report lines (FR-3.1)"
        ),
        "tables": ["field_visit_report_lines"],
    },
    {
        "version": "2026060302",
        "name": "field_visit_report_line_photos",
        "description": (
            "Multiple photos per field visit report line (FR-3.3)"
        ),
        "tables": ["field_visit_report_line_photos"],
    },
    {
        "version": "2026060303",
        "name": "project_field_report_scheme",
        "description": (
            "TAMA38 scheme on projects for field report metadata prefill (FR-4.3)"
        ),
        "tables": ["projects"],
    },
    {
        "version": "2026060304",
        "name": "field_visit_report_client_uuids",
        "description": (
            "Client UUID columns on field visit reports and lines (offline sync)"
        ),
        "tables": [
            "field_visit_reports",
            "field_visit_report_lines",
        ],
    },
    {
        "version": "2026060401",
        "name": "enable_rls_best_practice",
        "description": (
            "Enable RLS on public tables; authenticated SELECT only; "
            "service_role backend unchanged"
        ),
        "tables": list(TABLES.keys()),
    },
    {
        "version": "2026060701",
        "name": "project_field_report_metadata_columns",
        "description": (
            "Extended project metadata for field-report prefill "
            "(scheme, stakeholders, dates, city, housing units)"
        ),
        "tables": ["projects"],
    },
    {
        "version": "2026060702",
        "name": "field_visit_report_pdf_archive",
        "description": (
            "Permanent PDF archive pointers on field visit reports"
        ),
        "tables": ["field_visit_reports"],
    },
]


def get_table_names() -> list[str]:
    return list(TABLES.keys())


def get_tenant_scoped_tables() -> list[str]:
    return [
        name
        for name, schema in TABLES.items()
        if schema.tenant_column
    ]
