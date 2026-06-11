import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(root, "..", "out");

await mkdir(outDir, { recursive: true });

const html = `<!DOCTYPE html>
<html lang="he" dir="rtl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ElayoAI</title>
  </head>
  <body>
    <p>ElayoAI - שלד Capacitor (Build A / dev). הרץ <code>npm run build:mobile</code> ל-Build B.</p>
  </body>
</html>
`;

await writeFile(path.join(outDir, "index.html"), html, "utf8");
console.log("Wrote stub web assets to out/");
