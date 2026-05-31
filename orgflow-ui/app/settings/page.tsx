"use client";

import HomeNavBar from "@/components/layout/HomeNavBar";
import PublicNavBar from "@/components/landing/PublicNavBar";
import ThemeSettings from "@/components/settings/ThemeSettings";
import AppLoadingScreen from "@/components/ui/AppLoadingScreen";
import Card from "@/components/ui/Card";
import PageHeader from "@/components/ui/PageHeader";
import { useAuth } from "@/contexts/AuthContext";

export default function SettingsPage() {
  const { user, loading } = useAuth();

  if (loading) {
    return <AppLoadingScreen />;
  }

  return (
    <div className="of-app-bg min-h-screen">
      {user ? <HomeNavBar /> : <PublicNavBar />}

      <main className="of-dashboard-page of-container mx-auto max-w-3xl">
        <PageHeader
          title="הגדרות"
          description="התאימו את חוויית השימוש במערכת לפי העדפותיכם"
          eyebrow="Supervisor AI"
        />

        <Card padding="lg">
          <ThemeSettings />
        </Card>
      </main>
    </div>
  );
}
