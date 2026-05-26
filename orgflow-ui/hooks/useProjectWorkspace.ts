"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { toast } from "sonner";

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
  assigned_to: string | null;
};

type Summary = {
  reviews_count: number;
  actions_count: number;
  escalations_count: number;
  reports_count: number;
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

type WorkspaceResponse = {
  project: Project;
  reviews: Review[];
  actions: Action[];
  exceptions: Action[];
  activities: Activity[];
  insights: Insight[];
  summary: Summary;
};

export function useProjectWorkspace(
  projectId: string
) {

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

  const [summary, setSummary] =
    useState<Summary>({
      reviews_count: 0,
      actions_count: 0,
      escalations_count: 0,
      reports_count: 0,
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

        const response =
          await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/workspace`
          );

        if (!response.ok) {

          throw new Error(
            "Failed loading workspace"
          );
        }

        const workspace:
          WorkspaceResponse =
            await response.json();

        // =========================
        // UPDATE STATE
        // =========================

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

      } catch (error) {

        console.error(
          "Failed loading workspace:",
          error
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

    // =========================
    // OPTIMISTIC UPDATE
    // =========================

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
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/reviews/${reviewId}/approve`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              reviewed_by:
                "ארז שמאי",

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

    // =========================
    // OPTIMISTIC UPDATE
    // =========================

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
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/actions/${actionId}/close`,
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

  return {
    project,
    reviews,
    actions,
    exceptions,
    activities,
    insights,
    summary,
    loading,

    reloadWorkspace:
      loadWorkspace,

    approveReview,
    closeAction,
  };
}