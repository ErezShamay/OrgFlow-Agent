"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { toast } from "sonner";

import { apiFetch } from "@/lib/api/client";
import { useAuth } from "@/contexts/AuthContext";

type Project = {
  id: string;
  project_name: string;
  supervisor_name: string;
  supervisor_email: string;
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
  const { profile } = useAuth();

  // =========================
  // STATE
  // =========================

  const [project, setProject] =
    useState<Project | null>(null);

  const [reviews, setReviews] =
    useState<Review[]>([]);

  const [actions, setActions] =
    useState<Action[]>([]);

  const [exceptions, setExceptions] =
    useState<Action[]>([]);

  const [activities, setActivities] =
    useState<Activity[]>([]);

  const [insights, setInsights] =
    useState<Insight[]>([]);

  const [
    operationalSummary,
    setOperationalSummary
  ] = useState<
    OperationalSummary | null
  >(null);

  const [summary, setSummary] =
    useState<Summary>({
      reviews_count: 0,
      actions_count: 0,
      escalations_count: 0,
      reports_count: 0,
    });

  const [health, setHealth] =
    useState<Health>({
      score: 100,
      status: "HEALTHY",
    });

  const [loading, setLoading] =
    useState(true);

  // =========================
  // LOAD WORKSPACE
  // =========================

  const loadWorkspace =
    useCallback(async () => {

      if (!projectId) {
        return;
      }

      try {

        setLoading(true);

        const [
          workspaceResponse,
          summaryResponse,
        ] = await Promise.all([

          apiFetch(
            `/projects/${projectId}/workspace`
          ),

          apiFetch(
            `/projects/${projectId}/operational-summary`
          ),
        ]);

        if (
          !workspaceResponse.ok
          || !summaryResponse.ok
        ) {

          throw new Error(
            "Failed loading workspace"
          );
        }

        const workspace:
          WorkspaceResponse =
            await workspaceResponse.json();

        const operationalSummaryData:
          OperationalSummary =
            await summaryResponse.json();

        setProject(
          workspace.project
        );

        setReviews(
          workspace.reviews
        );

        setActions(
          workspace.actions
        );

        setExceptions(
          workspace.exceptions
        );

        setActivities(
          workspace.activities
        );

        setInsights(
          workspace.insights
        );

        setSummary(
          workspace.summary
        );

        setHealth(
          workspace.health
        );

        setOperationalSummary(
          operationalSummaryData
        );

      } catch (error) {

        console.error(
          "Failed loading workspace:",
          error
        );

        toast.error(
          "שגיאה בטעינת סביבת העבודה"
        );

      } finally {

        setLoading(false);

      }

    }, [projectId]);

  // =========================
  // INITIAL LOAD
  // =========================

  useEffect(() => {

    loadWorkspace();

  }, [loadWorkspace]);

  // =========================
  // AUTO REFRESH
  // =========================

  useEffect(() => {

    const pollingInterval =
      Number(
        process.env
          .NEXT_PUBLIC_POLLING_INTERVAL
      ) || 30000;

    const interval =
      setInterval(() => {

        loadWorkspace();

      }, pollingInterval);

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

      await loadWorkspace();

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

      await loadWorkspace();
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

      await loadWorkspace();

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

      await loadWorkspace();
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

      await loadWorkspace();

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

      await loadWorkspace();

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

      await loadWorkspace();

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

      await loadWorkspace();

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

    loading,

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