import type { NextConfig } from "next";

import { isCapacitorStaticExportBuild } from "./lib/capacitor/build-mode";

/** Vercel מגדיר VERCEL=1 - אין להשתמש ב-standalone/export שם (גורם ל-500). */
function isVercelDeploy(env: NodeJS.ProcessEnv = process.env): boolean {
  return Boolean(env.VERCEL);
}

/** Docker UI image - standalone נדרש ל-server.js ב-Dockerfile. */
function isDockerStandaloneBuild(env: NodeJS.ProcessEnv = process.env): boolean {
  return env.DOCKER_BUILD === "1" || env.ORGFLOW_DOCKER_BUILD === "1";
}

function isExplicitCapacitorStaticExportBuild(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return (
    env.ELAYOAI_CAPACITOR_BUILD === "static"
    || env.ORGFLOW_CAPACITOR_BUILD === "static"
    || env.ELAYOAI_CAPACITOR_BUILD_MODE === "static"
    || env.ORGFLOW_CAPACITOR_BUILD_MODE === "static"
  );
}

const capacitorStaticExport =
  !isVercelDeploy() && isExplicitCapacitorStaticExportBuild();
const dockerStandalone =
  !isVercelDeploy() && isDockerStandaloneBuild();

const sharedImages: NonNullable<NextConfig["images"]> = {
  formats: ["image/avif", "image/webp"],
  deviceSizes: [640, 750, 828, 1080, 1200],
  imageSizes: [16, 32, 48, 64, 96, 128, 256],
  minimumCacheTTL: 60,
};

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  ...(capacitorStaticExport
    ? {
        output: "export",
        trailingSlash: true,
        images: {
          ...sharedImages,
          unoptimized: true,
        },
      }
    : dockerStandalone
      ? {
          output: "standalone",
          images: sharedImages,
        }
      : {
          images: sharedImages,
        }),
  experimental: {
    optimizePackageImports: ["lucide-react", "sonner"],
  },
  compiler: {
    removeConsole:
      process.env.NODE_ENV === "production"
        ? { exclude: ["error", "warn"] }
        : false,
  },
};

export default nextConfig;
