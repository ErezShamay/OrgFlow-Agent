"use client";

import {
  startTransition,
  useCallback,
  useEffect,
  useState,
} from "react";

import { toast } from "sonner";

import { apiFetch } from "@/lib/api/client";
import { useAuth } from "@/contexts/AuthContext";
import {
  readWorkspaceCache,
  writeWorkspaceCache,
  type WorkspaceCacheSnapshot,
} from "@/lib/ui/workspace-cache";

type Project = {
  id: string;
  project_name: string;
  developer_name?: string | null;
  contractor_name?: string | null;
  lawyer_name?: string | null;
  supervisor_name: string;
  supervisor_email?: string | null;
  developer_pm_name?: string | null;
  accompanying_lawyer?: string | null;
  architect_name?: string | null;
  site_manager_name?: string | null;
  city?: string | null;
  housing_units_count?: number | null;
  status: string;
  created_at: string;
};

type Review = {
  id: string;
  business_impact: string;
  tenant_risk: string;
  recommended_action: string;
  review_status: string;
};

type Action = {
  id: string;
  action_type: string;
  title: string;
  description: string;
  status: string;

  assigned_to:
    string | null;

  due_date:
    string | null;

  priority:
    string;
};

type Summary = {
  reviews_count: number;
  actions_count: number;
  escalations_count: number;
  reports_count: number;
};

type Health = {
  score: number;
  status: string;
};

type Activity = {
  id: string;
  activity_type: string;
  title: string;
  description: string | null;
  created_at: string;
};

type Insight = {
  type: string;
  title: string;
  description: string;
};

type OperationalSummary = {
  project_id: string;
  summary: string;
};

type LoadWorkspaceOptions = {
  silent?: boolean;
};

function applyWorkspaceSnapshot(
  workspace: WorkspaceResponse,
  setters: {
    setProject: (value: Project | null) => void;
    setReviews: (value: Review[]) => void;
    setActions: (value: Action[]) => void;
    setExceptions: (value: Action[]) => void;
    setActivities: (value: Activity[]) => void;
    setInsights: (value: Insight[]) => void;
    setSummary: (value: Summary) => void;
    setHealth: (value: Health) => void;
  }
) {
  setters.setProject(workspace.project);
  setters.setReviews(workspace.reviews);
  setters.setActions(workspace.actions);
  setters.setExceptions(workspace.exceptions);
  setters.setActivities(workspace.activities);
  setters.setInsights(workspace.insights);
  setters.setSummary(workspace.summary);
  setters.setHealth(workspace.health);
}

function hydrateWorkspaceState(
  cached: WorkspaceCacheSnapshot,
  setters: {
    setProject: (value: Project | null) => void;
    setReviews: (value: Review[]) => void;
    setActions: (value: Action[]) => void;
    setExceptions: (value: Action[]) => void;
    setActivities: (value: Activity[]) => void;
    setInsights: (value: Insight[]) => void;
    setSummary: (value: Summary) => void;
    setHealth: (value: Health) => void;
  }
) {
  setters.setProject(cached.project as Project | null);
  setters.setReviews(cached.reviews as Review[]);
  setters.setActions(cached.actions as Action[]);
  setters.setExceptions(cached.exceptions as Action[]);
  setters.setActivities(cached.activities as Activity[]);
  setters.setInsights(cached.insights as Insight[]);
  setters.setSummary(cached.summary);
  setters.setHealth(cached.health);
}

const WORKSPACE_POLLING_MS =
  10 * 60 * 1000;

type WorkspaceResponse = {
  project: Project;
  reviews: Review[];
  actions: Action[];
  exceptions: Action[];
  activities: Activity[];
  insights: Insight[];
  summary: Summary;
  health: Health;
};

export function useProjectWorkspace(
  projectId: string
) {
  const {
    profile,
    user,
    loading: authLoading,
  } = useAuth();

  // =========================
  // STATE
  // =========================

  const cachedWorkspace = readWorkspaceCache(projectId);

  const [project, setProject] = useState<Project | null>(
    (cachedWorkspace?.project as Project | null) ?? null
  );

  const [reviews, setReviews] = useState<Review[]>(
    (cachedWorkspace?.reviews as Review[]) ?? []
  );

  const [actions, setActions] = useState<Action[]>(
    (cachedWorkspace?.actions as Action[]) ?? []
  );

  const [exceptions, setExceptions] = useState<Action[]>(
    (cachedWorkspace?.exceptions as Action[]) ?? []
  );

  const [activities, setActivities] = useState<Activity[]>(
    (cachedWorkspace?.activities as Activity[]) ?? []
  );

  const [insights, setInsights] = useState<Insight[]>(
    (cachedWorkspace?.insights as Insight[]) ?? []
  );

  const [
    operationalSummary,
    setOperationalSummary
  ] = useState<
    OperationalSummary | null
  >(null);

  const [summary, setSummary] = useState<Summary>(
    cachedWorkspace?.summary ?? {
      reviews_count: 0,
      actions_count: 0,
      escalations_count: 0,
      reports_count: 0,
    }
  );

  const [health, setHealth] = useState<Health>(
    cachedWorkspace?.health ?? {
      score: 100,
      status: "HEALTHY",
    }
  );

  const [loading, setLoading] = useState(!cachedWorkspace);

  const [isValidating, setIsValidating] = useState(false);

  const [
    operationalSummaryLoading,
    setOperationalSummaryLoading,
  ] = useState(false);

  const stateSetters = {
    setProject,
    setReviews,
    setActions,
    setExceptions,
    setActivities,
    setInsights,
    setSummary,
    setHealth,
  };

  useEffect(() => {
    const cached = readWorkspaceCache(projectId);

    if (cached) {
      hydrateWorkspaceState(cached, stateSetters);
      setLoading(false);
      return;
    }

    setProject(null);
    setReviews([]);
    setActions([]);
    setExceptions([]);
    setActivities([]);
    setInsights([]);
    setSummary({
      reviews_count: 0,
      actions_count: 0,
      escalations_count: 0,
      reports_count: 0,
    });
    setHealth({
      score: 100,
      status: "HEALTHY",
    });
    setLoading(true);
  }, [projectId]);

  const loadOperationalSummary =
    useCallback(async () => {
      if (!projectId || !user) {
        return;
      }

      try {
        setOperationalSummaryLoading(true);

        const summaryResponse =
          await apiFetch(
            `/projects/${projectId}/operational-summary`
          );

        if (summaryResponse.ok) {
          const operationalSummaryData:
            OperationalSummary =
              await summaryResponse.json();

          setOperationalSummary(
            operationalSummaryData
          );
        } else {
          console.warn(
            "Failed loading operational summary:",
            summaryResponse.status
          );
          setOperationalSummary(null);
        }
      } catch (summaryError) {
        console.warn(
          "Failed loading operational summary:",
          summaryError
        );
        setOperationalSummary(null);
      } finally {
        setOperationalSummaryLoading(false);
      }
    }, [projectId, user]);

  const loadWorkspace =
    useCallback(async (
      options: LoadWorkspaceOptions = {}
    ) => {
      const { silent = false } = options;

      if (!projectId) {
        return;
      }

      if (authLoading) {
        return;
      }

      if (!user) {
        setLoading(false);
        return;
      }

      const cached = readWorkspaceCache(projectId);

      try {

        if (!silent && !cached) {
          setLoading(true);
        } else if (!silent) {
          setIsValidating(true);
        }

        const workspaceResponse =
          await apiFetch(
            `/projects/${projectId}/workspace`
          );

        if (!workspaceResponse.ok) {
          if (workspaceResponse.status === 404) {
            setProject(null);
            return;
          }

          console.error(
            "Failed loading workspace:",
            workspaceResponse.status
          );

          if (!silent) {
            toast.error(
              "שגיאה בטעינת סביבת העבודה"
            );
          }

          return;
        }

        const workspace:
          WorkspaceResponse =
            await workspaceResponse.json();

        applyWorkspaceSnapshot(workspace, stateSetters);

        writeWorkspaceCache(projectId, {
          project: workspace.project,
          reviews: workspace.reviews,
          actions: workspace.actions,
          exceptions: workspace.exceptions,
          activities: workspace.activities,
          insights: workspace.insights,
          summary: workspace.summary,
          health: workspace.health,
        });

      } catch (error) {

        console.error(
          "Failed loading workspace:",
          error
        );

        if (!silent) {
          toast.error(
            "שגיאה בטעינת סביבת העבודה"
          );
        }

      } finally {
        setLoading(false);
        setIsValidating(false);
      }

    }, [authLoading, projectId, user]);

  // =========================
  // INITIAL LOAD
  // =========================

  useEffect(() => {

    startTransition(() => {
      void loadWorkspace();
    });

  }, [loadWorkspace]);

  // =========================
  // OPERATIONAL SUMMARY (background)
  // =========================

  useEffect(() => {

    if (
      authLoading
      || loading
      || !project
    ) {
      return;
    }

    startTransition(() => {
      void loadOperationalSummary();
    });

  }, [
    authLoading,
    loading,
    project,
    loadOperationalSummary,
  ]);

  // =========================
  // AUTO REFRESH (every 10 minutes)
  // =========================

  useEffect(() => {

    const interval =
      setInterval(() => {

        void loadWorkspace({ silent: true });

      }, WORKSPACE_POLLING_MS);

    return () => {

      clearInterval(interval);

    };

  }, [loadWorkspace]);

  // =========================
  // APPROVE REVIEW
  // =========================

  async function approveReview(
    reviewId: string
  ) {

    const existingReview =
      reviews.find(
        review => review.id === reviewId
      );

    if (!existingReview) {
      return;
    }

    setReviews(current =>
      current.filter(
        review => review.id !== reviewId
      )
    );

    setSummary(current => ({
      ...current,

      reviews_count:
        Math.max(
          current.reviews_count - 1,
          0
        ),

      actions_count:
        current.actions_count + 1,
    }));

    try {

      const response =
        await apiFetch(
          `/reviews/${reviewId}/approve`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              reviewed_by:
                profile?.id ||
                profile?.email ||
                "reviewer",

              review_notes:
                "Approved from workspace",
            }),
          }
        );

      if (!response.ok) {

        throw new Error(
          "Failed approving review"
        );
      }

      await loadWorkspace({ silent: true });

      toast.success(
        "הביקורת אושרה בהצלחה"
      );

    } catch (error) {

      console.error(
        "Failed approving review:",
        error
      );

      toast.error(
        "שגיאה באישור הביקורת"
      );

      await loadWorkspace({ silent: true });
    }
  }

  // =========================
  // CLOSE ACTION
  // =========================

  async function closeAction(
    actionId: string
  ) {

    setActions(current =>
      current.filter(
        action => action.id !== actionId
      )
    );

    setSummary(current => ({
      ...current,

      actions_count:
        Math.max(
          current.actions_count - 1,
          0
        ),
    }));

    try {

      const response =
        await apiFetch(
          `/actions/${actionId}/close`,
          {
            method: "POST",
          }
        );

      if (!response.ok) {

        throw new Error(
          "Failed closing action"
        );
      }

      await loadWorkspace({ silent: true });

      toast.success(
        "הפעולה נסגרה בהצלחה"
      );

    } catch (error) {

      console.error(
        "Failed closing action:",
        error
      );

      toast.error(
        "שגיאה בסגירת הפעולה"
      );

      await loadWorkspace({ silent: true });
    }
  }

  // =========================
  // START ACTION
  // =========================

  async function startAction(
    actionId: string
  ) {

    try {

      const response =
        await apiFetch(
          `/actions/${actionId}/start`,
          {
            method: "POST",
          }
        );

      if (!response.ok) {

        throw new Error(
          "Failed starting action"
        );
      }

      await loadWorkspace({ silent: true });

      toast.success(
        "הפעולה התחילה"
      );

    } catch (error) {

      console.error(
        "Failed starting action:",
        error
      );

      toast.error(
        "שגיאה בהתחלת הפעולה"
      );
    }
  }

  // =========================
  // BLOCK ACTION
  // =========================

  async function blockAction(
    actionId: string
  ) {

    try {

      const response =
        await apiFetch(
          `/actions/${actionId}/block`,
          {
            method: "POST",
          }
        );

      if (!response.ok) {

        throw new Error(
          "Failed blocking action"
        );
      }

      await loadWorkspace({ silent: true });

      toast.success(
        "הפעולה סומנה כחסומה"
      );

    } catch (error) {

      console.error(
        "Failed blocking action:",
        error
      );

      toast.error(
        "שגיאה בחסימת הפעולה"
      );
    }
  }

  // =========================
  // COMPLETE ACTION
  // =========================

  async function completeAction(
    actionId: string
  ) {

    try {

      const response =
        await apiFetch(
          `/actions/${actionId}/complete`,
          {
            method: "POST",
          }
        );

      if (!response.ok) {

        throw new Error(
          "Failed completing action"
        );
      }

      await loadWorkspace({ silent: true });

      toast.success(
        "הפעולה הושלמה"
      );

    } catch (error) {

      console.error(
        "Failed completing action:",
        error
      );

      toast.error(
        "שגיאה בהשלמת הפעולה"
      );
    }
  }

  // =========================
  // ESCALATE ACTION
  // =========================

  async function escalateAction(
    actionId: string
  ) {

    try {

      const response =
        await apiFetch(
          `/actions/${actionId}/escalate`,
          {
            method: "POST",
          }
        );

      if (!response.ok) {

        throw new Error(
          "Failed escalating action"
        );
      }

      await loadWorkspace({ silent: true });

      toast.success(
        "הפעולה הוסלמה"
      );

    } catch (error) {

      console.error(
        "Failed escalating action:",
        error
      );

      toast.error(
        "שגיאה בהסלמת הפעולה"
      );
    }
  }

  return {
    project,
    reviews,
    actions,
    exceptions,
    activities,
    insights,

    summary,
    health,
    operationalSummary,
    operationalSummaryLoading,

    loading,
    isValidating,

    reloadWorkspace:
      loadWorkspace,

    approveReview,

    closeAction,

    startAction,
    blockAction,
    completeAction,
    escalateAction,
  };
}