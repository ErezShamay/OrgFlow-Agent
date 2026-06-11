#!/usr/bin/env node
/**
 * יוצר אייקוני launcher ומסכי splash ל-Android מלוגו המערכת (public/icons/icon-512.svg).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import sharp from "sharp";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const uiRoot = path.join(scriptDir, "..");
const androidRes = path.join(uiRoot, "android/app/src/main/res");
const brandSvg = path.join(uiRoot, "public/icons/icon-512.svg");

/** רקע מותג (Kobioron teal) */
const BRAND_BG = { r: 7, g: 116, b: 141 };

/** גודל ic_launcher (px) לפי תיקיית mipmap. */
const LAUNCHER_PX = {
  "mipmap-mdpi": 48,
  "mipmap-hdpi": 72,
  "mipmap-xhdpi": 96,
  "mipmap-xxhdpi": 144,
  "mipmap-xxxhdpi": 192,
};

/** גודל ic_launcher_foreground (adaptive icon). */
const FOREGROUND_PX = {
  "mipmap-mdpi": 108,
  "mipmap-hdpi": 162,
  "mipmap-xhdpi": 216,
  "mipmap-xxhdpi": 324,
  "mipmap-xxxhdpi": 432,
};

/** מסכי splash - [width, height] לכל תיקייה. */
const SPLASH_SIZES = {
  "drawable/splash.png": [480, 320],
  "drawable-port-mdpi/splash.png": [320, 480],
  "drawable-port-hdpi/splash.png": [480, 800],
  "drawable-port-xhdpi/splash.png": [720, 1280],
  "drawable-port-xxhdpi/splash.png": [1080, 1920],
  "drawable-port-xxxhdpi/splash.png": [1440, 2560],
  "drawable-land-mdpi/splash.png": [480, 320],
  "drawable-land-hdpi/splash.png": [800, 480],
  "drawable-land-xhdpi/splash.png": [1280, 720],
  "drawable-land-xxhdpi/splash.png": [1920, 1080],
  "drawable-land-xxxhdpi/splash.png": [2560, 1440],
};

async function writePng(svgPath, outPath, size) {
  await sharp(svgPath, { density: 300 })
    .resize(size, size, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png()
    .toFile(outPath);
}

async function writeSplash(svgPath, outPath, width, height) {
  const logoSize = Math.round(Math.min(width, height) * 0.38);
  const logoBuffer = await sharp(svgPath, { density: 300 })
    .resize(logoSize, logoSize, {
      fit: "contain",
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    })
    .png()
    .toBuffer();

  await sharp({
    create: {
      width,
      height,
      channels: 3,
      background: BRAND_BG,
    },
  })
    .composite([{ input: logoBuffer, gravity: "center" }])
    .png()
    .toFile(outPath);
}

async function main() {
  if (!fs.existsSync(brandSvg)) {
    console.error(`Brand icon not found: ${brandSvg}`);
    process.exit(1);
  }

  for (const [folder, size] of Object.entries(LAUNCHER_PX)) {
    const dir = path.join(androidRes, folder);
    fs.mkdirSync(dir, { recursive: true });

    const launcher = path.join(dir, "ic_launcher.png");
    await writePng(brandSvg, launcher, size);
    await writePng(brandSvg, path.join(dir, "ic_launcher_round.png"), size);
    console.log(`Wrote ${launcher} (${size}px)`);
  }

  for (const [folder, size] of Object.entries(FOREGROUND_PX)) {
    const out = path.join(androidRes, folder, "ic_launcher_foreground.png");
    await writePng(brandSvg, out, size);
    console.log(`Wrote ${out} (${size}px)`);
  }

  for (const [relativePath, [width, height]] of Object.entries(SPLASH_SIZES)) {
    const out = path.join(androidRes, relativePath);
    fs.mkdirSync(path.dirname(out), { recursive: true });
    await writeSplash(brandSvg, out, width, height);
    console.log(`Wrote ${out} (${width}x${height})`);
  }

  console.log("Android launcher icons and splash screens updated from public/icons/icon-512.svg");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
