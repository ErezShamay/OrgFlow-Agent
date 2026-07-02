import fs from "node:fs";
import os from "node:os";
import path from "node:path";

/** Gradle / Capacitor Android דורשים JDK 21 (ראה שגיאת toolchain). */
const JAVA_HOME_CANDIDATES = [
  () => process.env.JAVA_HOME,
  "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home",
  "/usr/local/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home",
  "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home",
  "/usr/local/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home",
  "/Applications/Android Studio.app/Contents/jbr/Contents/Home",
  "C:\\Program Files\\Android\\Android Studio\\jbr",
  "C:\\Program Files\\Java\\jdk-21",
  "C:\\Program Files\\Eclipse Adoptium\\jdk-21.0.7.6-hotspot",
  "C:\\Program Files\\Microsoft\\jdk-21.0.7.6-hotspot",
];

function javaExecutable(javaHome) {
  const name = process.platform === "win32" ? "java.exe" : "java";
  return path.join(javaHome, "bin", name);
}

export function resolveJavaHome() {
  for (const candidate of JAVA_HOME_CANDIDATES) {
    const home =
      typeof candidate === "function" ? candidate() : candidate;
    if (!home) {
      continue;
    }

    if (fs.existsSync(javaExecutable(home))) {
      return home;
    }
  }

  return null;
}

export function resolveAndroidHome() {
  const fromEnv = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT;
  if (fromEnv && fs.existsSync(fromEnv)) {
    return fromEnv;
  }

  if (process.platform === "darwin") {
    const defaultSdk = path.join(
      os.homedir(),
      "Library",
      "Android",
      "sdk"
    );
    if (fs.existsSync(defaultSdk)) {
      return defaultSdk;
    }
  }

  if (process.platform === "win32" && process.env.LOCALAPPDATA) {
    const defaultSdk = path.join(
      process.env.LOCALAPPDATA,
      "Android",
      "Sdk"
    );
    if (fs.existsSync(defaultSdk)) {
      return defaultSdk;
    }
  }

  return fromEnv || null;
}

/**
 * משתני סביבה לבניית APK - JAVA_HOME 21, ANDROID_HOME, PATH.
 */
export function resolveAndroidBuildEnv(baseEnv = process.env) {
  const env = { ...baseEnv };
  const notes = [];

  const javaHome = resolveJavaHome();
  if (javaHome) {
    env.JAVA_HOME = javaHome;
    const javaBin = path.join(javaHome, "bin");
    env.PATH = env.PATH ? `${javaBin}${path.delimiter}${env.PATH}` : javaBin;
    notes.push(`JAVA_HOME=${javaHome}`);
  } else {
    notes.push(
      "JAVA_HOME: not found - install JDK 21 (Android Studio JBR) or set JAVA_HOME"
    );
  }

  const androidHome = resolveAndroidHome();
  if (androidHome) {
    env.ANDROID_HOME = androidHome;
    env.ANDROID_SDK_ROOT = androidHome;
    const platformTools = path.join(androidHome, "platform-tools");
    if (fs.existsSync(platformTools)) {
      env.PATH = env.PATH
        ? `${platformTools}${path.delimiter}${env.PATH}`
        : platformTools;
    }
    notes.push(`ANDROID_HOME=${androidHome}`);
  } else {
    notes.push(
      "ANDROID_HOME: not found - install Android Studio / SDK or set ANDROID_HOME"
    );
  }

  return { env, notes, javaHome, androidHome };
}
