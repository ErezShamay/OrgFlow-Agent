import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HELPERS_DIR = path.dirname(fileURLToPath(import.meta.url));
const UI_ROOT = path.resolve(HELPERS_DIR, "../..");
const REPO_ROOT = path.resolve(UI_ROOT, "..");

/** Python executable path for gate tests (venv on Windows, python3 elsewhere). */
export function resolvePythonCommand(): string {
  const winVenv = path.join(REPO_ROOT, ".venv", "Scripts", "python.exe");
  if (process.platform === "win32" && existsSync(winVenv)) {
    return winVenv;
  }

  const unixVenv = path.join(REPO_ROOT, ".venv", "bin", "python3");
  if (existsSync(unixVenv)) {
    return unixVenv;
  }

  return process.platform === "win32" ? "python" : "python3";
}

export function execPythonScript(
  script: string,
  options: { cwd?: string; encoding?: BufferEncoding; maxBuffer?: number } = {}
): string {
  const python = resolvePythonCommand();
  const cwd = options.cwd ?? REPO_ROOT;

  return execFileSync(python, ["-c", script], {
    cwd,
    encoding: options.encoding ?? "utf8",
    maxBuffer: options.maxBuffer,
  }) as string;
}

export function execPythonArgs(
  args: string[],
  options: { cwd?: string; encoding?: BufferEncoding; maxBuffer?: number } = {}
): string {
  const python = resolvePythonCommand();
  const cwd = options.cwd ?? REPO_ROOT;

  return execFileSync(python, args, {
    cwd,
    encoding: options.encoding ?? "utf8",
    maxBuffer: options.maxBuffer,
  }) as string;
}

export { REPO_ROOT };
