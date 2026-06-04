import {
  createClient,
  type SupabaseClient,
} from "@supabase/supabase-js";

import { getSupabasePublicConfig } from "@/lib/env/public-env";

const PLACEHOLDER_URL = "https://placeholder.supabase.co";
const PLACEHOLDER_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1wbGFjZWhvbGRlciJ9.placeholder";

function isProductionBuildPhase(): boolean {
  return (
    process.env.NEXT_PHASE === "phase-production-build"
    || process.env.npm_lifecycle_event === "build"
  );
}

function resolveCredentials(): { url: string; anonKey: string } {
  const { url, anonKey } = getSupabasePublicConfig();

  if (url && anonKey) {
    return { url, anonKey };
  }

  if (typeof window === "undefined" && isProductionBuildPhase()) {
    return {
      url: url || PLACEHOLDER_URL,
      anonKey: anonKey || PLACEHOLDER_ANON_KEY,
    };
  }

  if (!url || !anonKey) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY"
    );
  }

  return { url, anonKey };
}

let singleton: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (!singleton) {
    const { url, anonKey } = resolveCredentials();
    singleton = createClient(url, anonKey);
  }

  return singleton;
}

export const supabase = new Proxy({} as SupabaseClient, {
  get(_target, prop) {
    const client = getSupabaseClient();
    const value = Reflect.get(client, prop, client);

    return typeof value === "function"
      ? (value as (...args: unknown[]) => unknown).bind(client)
      : value;
  },
});
