"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";

import HomeNavBar from "@/components/layout/HomeNavBar";
import PublicHomePage from "@/components/landing/PublicHomePage";
import AppLoadingScreen from "@/components/ui/AppLoadingScreen";
import Badge from "@/components/ui/Badge";
import KpiCard from "@/components/ui/KpiCard";
import LoadingState from "@/components/ui/LoadingState";

import { useCallback, useEffect, useState, startTransition } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/lib/api/client";

type Project = {
  id: string;
  project_name: string;
  status: string;
};

type Organization = {
  id: string;
  organization_name: string;
  contact_email: string;
  projects: Project[];
};

function AuthenticatedHero() {
  return (
    <>
      <div
        className="
          mb-6
          inline-flex
          items-center
          gap-2
          rounded-full
          border
          border-blue-200/60
          bg-blue-50/80
          px-4
          py-2
          text-sm
          font-medium
          text-blue-700
          backdrop-blur-sm
          dark:border-blue-800/40
          dark:bg-blue-950/40
          dark:text-blue-300
        "
      >
        <Sparkles className="h-4 w-4" />
        מערכת תפעול הנדסי מבוססת AI
      </div>

      <h1 className="of-page-title">
        Supervisor AI
      </h1>

      <p className="of-page-desc max-w-3xl">
        פלטפורמת AI לניהול תפעולי,
        פיקוח הנדסי, בקרת פרויקטים,
        ניתוח חריגות ונקודות סיכון
        בפרויקטי התחדשות עירונית ובנייה.
      </p>
    </>
  );
}

export default function HomePage() {
  const { user, loading: authLoading } = useAuth();

  const [organizations, setOrganizations] =
    useState<Organization[]>([]);

  const [loading, setLoading] =
    useState(true);

  const loadOrganizations = useCallback(async () => {
    try {
      const response = await apiFetch("/organizations");

      const data =
        await response.json();

      if (!response.ok) {
        console.error("Failed loading organizations:", data);
        setOrganizations([]);
        return;
      }

      setOrganizations(
        Array.isArray(data) ? data : []
      );
    } catch (error) {
      console.error(error);
      setOrganizations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading || !user) {
      return;
    }

    startTransition(() => {
      void loadOrganizations();
    });
  }, [authLoading, user, loadOrganizations]);

  if (authLoading) {
    return <AppLoadingScreen />;
  }

  if (!user) {
    return <PublicHomePage />;
  }

  const totalProjects =
    organizations.reduce(
      (acc, org) =>
        acc + (org.projects?.length ?? 0),
      0
    );

  return (
    <div className="of-app-bg min-h-screen">
      <HomeNavBar />

      <section className="of-container relative py-12 md:py-16">
        <div className="max-w-4xl">
          <AuthenticatedHero />
        </div>
      </section>

      <section className="of-container pb-16">
        <div
          className="
            grid
            grid-cols-1
            gap-6
            md:grid-cols-2
            xl:grid-cols-4
          "
        >
          <KpiCard label="ביקורות AI" value="148" variant="accent" />
          <KpiCard label="פרויקטים פעילים" value={totalProjects} />
          <KpiCard label="מנוע AI פעיל" value="Operational AI" />
          <KpiCard
            label="סטטוס מערכת"
            value={
              <span className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
                </span>
                Online
              </span>
            }
          />
        </div>
      </section>

      <section className="of-container pb-24">
        <div className="mb-10">
          <h2 className="of-section-title">
            חברות ופרויקטים
          </h2>
          <p className="of-page-desc">
            גישה לפרויקטים הפעילים במערכת
          </p>
        </div>

        {loading ? (
          <LoadingState message="טוען נתונים..." />
        ) : null}

        <div className="space-y-10">
          {organizations.map((organization) => (
            <div
              key={organization.id}
              className="of-card of-card-p10 of-card-xl"
            >
              <div className="mb-8">
                <h3 className="text-3xl font-bold">
                  {organization.organization_name}
                </h3>
                <p className="mt-2 text-zinc-500">
                  {organization.contact_email}
                </p>
              </div>

              <div
                className="
                  grid
                  grid-cols-1
                  gap-6
                  lg:grid-cols-2
                  xl:grid-cols-3
                "
              >
                {organization.projects.map((project) => (
                  <Link
                    key={project.id}
                    href={`/projects/${project.id}`}
                    className="
                      of-card
                      of-card-interactive
                      of-card-muted
                      of-card-p8
                      block
                    "
                  >
                    <div
                      className="
                        mb-5
                        flex
                        items-start
                        justify-between
                        gap-3
                      "
                    >
                      <h4 className="text-2xl font-bold">
                        {project.project_name}
                      </h4>

                      <Badge variant="success">
                        פעיל
                      </Badge>
                    </div>

                    <p className="text-zinc-500">
                      כניסה לסביבת העבודה
                      התפעולית של הפרויקט
                    </p>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
