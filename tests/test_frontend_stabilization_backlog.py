import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = REPO_ROOT / "orgflow-ui"

FRONTEND_STABILIZATION_ARTIFACTS = [
    "styles/design-tokens.css",
    "lib/ui/toast.ts",
    "lib/ui/pagination.ts",
    "lib/ui/sorting.ts",
    "lib/ui/filtering.ts",
    "lib/ui/lazy.ts",
    "lib/ui/i18n.ts",
    "lib/ui/accessibility.ts",
    "lib/ui/browser-compat.ts",
    "providers/AppProviders.tsx",
    "providers/ThemeProvider.tsx",
    "providers/I18nProvider.tsx",
    "providers/OfflineProvider.tsx",
    "hooks/useAsyncData.ts",
    "hooks/usePagination.ts",
    "hooks/useInfiniteScroll.ts",
    "hooks/useSorting.ts",
    "hooks/useFiltering.ts",
    "hooks/useLazyLoad.ts",
    "components/ui/Button.tsx",
    "components/ui/Card.tsx",
    "components/ui/Skeleton.tsx",
    "components/ui/Spinner.tsx",
    "components/ui/LoadingState.tsx",
    "components/ui/EmptyState.tsx",
    "components/ui/RetryPanel.tsx",
    "components/ui/OfflineBanner.tsx",
    "components/ui/Pagination.tsx",
    "components/ui/FilterBar.tsx",
    "components/ui/SortSelect.tsx",
    "components/ui/OptimizedImage.tsx",
    "components/ui/ErrorBoundary.tsx",
    "components/ui/PageShell.tsx",
    "components/ui/ThemeToggle.tsx",
    "components/ui/LocaleToggle.tsx",
    "app/error.tsx",
    "app/global-error.tsx",
    "vitest.config.ts",
    "tests/lib/pagination.test.ts",
    "tests/lib/sorting.test.ts",
    "tests/lib/filtering.test.ts",
    "tests/lib/i18n.test.ts",
    "tests/lib/browser-compat.test.ts",
    "tests/lib/lazy.test.ts",
]


def test_frontend_stabilization_artifacts_exist():
    missing = [
        path
        for path in FRONTEND_STABILIZATION_ARTIFACTS
        if not (UI_ROOT / path).exists()
    ]

    assert not missing, f"Missing frontend artifacts: {missing}"


def test_loading_states_and_skeleton_loaders():
    loading_state = (UI_ROOT / "components/ui/LoadingState.tsx").read_text()
    skeleton = (UI_ROOT / "components/ui/Skeleton.tsx").read_text()

    assert "SkeletonList" in skeleton
    assert "variant" in loading_state


def test_global_error_boundary_and_toast_system():
    layout = (UI_ROOT / "app/layout.tsx").read_text()
    toast = (UI_ROOT / "lib/ui/toast.ts").read_text()

    assert "ErrorBoundary" in layout
    assert "Toaster" in layout
    assert "showToast" in toast
    assert (UI_ROOT / "app/error.tsx").exists()
    assert (UI_ROOT / "app/global-error.tsx").exists()


def test_accessibility_responsive_and_dark_mode():
    tokens = (UI_ROOT / "styles/design-tokens.css").read_text()
    dashboard_layout = (
        UI_ROOT / "app/(dashboard)/layout.tsx"
    ).read_text()

    assert "of-focus-ring" in tokens
    assert "of-sr-only" in tokens
    assert "lg:flex-row" in dashboard_layout
    assert "ThemeToggle" in dashboard_layout
    assert ".dark" in tokens


def test_reusable_ui_kit_design_system_and_empty_states():
    design_tokens = UI_ROOT / "styles/design-tokens.css"
    button = UI_ROOT / "components/ui/Button.tsx"
    empty_state = UI_ROOT / "components/ui/EmptyState.tsx"

    assert design_tokens.exists()
    assert button.exists()
    assert "EmptyState" in empty_state.read_text()


def test_retry_offline_pagination_infinite_scroll_sort_filter_lazy():
    artifacts = {
        "retry": UI_ROOT / "components/ui/RetryPanel.tsx",
        "offline": UI_ROOT / "components/ui/OfflineBanner.tsx",
        "pagination": UI_ROOT / "hooks/usePagination.ts",
        "infinite": UI_ROOT / "hooks/useInfiniteScroll.ts",
        "sorting": UI_ROOT / "hooks/useSorting.ts",
        "filtering": UI_ROOT / "hooks/useFiltering.ts",
        "lazy": UI_ROOT / "hooks/useLazyLoad.ts",
    }

    for name, path in artifacts.items():
        assert path.exists(), name


def test_bundle_image_browser_rtl_i18n_optimizations():
    next_config = (UI_ROOT / "next.config.ts").read_text()
    i18n = (UI_ROOT / "lib/ui/i18n.ts").read_text()
    browser_compat = (
        UI_ROOT / "lib/ui/browser-compat.ts"
    ).read_text()
    optimized_image = (
        UI_ROOT / "components/ui/OptimizedImage.tsx"
    ).read_text()

    assert "optimizePackageImports" in next_config
    assert "image/avif" in next_config
    assert "he" in i18n and "en" in i18n
    assert "rtl" in i18n
    assert "detectBrowserSupport" in browser_compat
    assert 'loading={props.loading ?? "lazy"}' in optimized_image


def test_projects_page_uses_frontend_stabilization_primitives():
    projects_page = (
        UI_ROOT / "app/(dashboard)/projects/page.tsx"
    ).read_text()

    assert "useAsyncData" in projects_page
    assert "LoadingState" in projects_page
    assert "EmptyState" in projects_page
    assert "PaginationControls" in projects_page
    assert "FilterBar" in projects_page
    assert "SortSelect" in projects_page


def test_frontend_stabilization_vitest_suite():
    result = subprocess.run(
        ["npm", "test"],
        cwd=UI_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
