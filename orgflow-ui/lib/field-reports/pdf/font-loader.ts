const FONT_CACHE_KEY = "orgflow-field-report-pdf-font";
const FONT_PATH = "/fonts/NotoSansHebrew-Regular.ttf";
const FONT_FILE = "NotoSansHebrew-Regular.ttf";

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }
  return btoa(binary);
}

async function readCachedFont(): Promise<string | null> {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return localStorage.getItem(FONT_CACHE_KEY);
  } catch {
    return null;
  }
}

async function cacheFont(base64: string): Promise<void> {
  try {
    localStorage.setItem(FONT_CACHE_KEY, base64);
  } catch {
    // Ignore quota errors — PDF can still work this session.
  }
}

async function fetchFontBase64(): Promise<string> {
  const cached = await readCachedFont();
  if (cached) {
    return cached;
  }

  const response = await fetch(FONT_PATH);
  if (!response.ok) {
    throw new Error("טעינת גופן עברית ל-PDF נכשלה");
  }

  const base64 = arrayBufferToBase64(await response.arrayBuffer());
  await cacheFont(base64);
  return base64;
}

export async function createPdfPrinter() {
  const pdfMakeModule = await import("pdfmake/build/pdfmake");
  const pdfFontsModule = await import("pdfmake/build/vfs_fonts");
  const pdfMake = pdfMakeModule.default;
  const baseVfs =
    pdfFontsModule.default?.pdfMake?.vfs
    || pdfFontsModule.default
    || {};

  const hebrewFont = await fetchFontBase64();

  const mergedVfs = {
    ...baseVfs,
    [FONT_FILE]: hebrewFont,
  };

  // pdfmake 0.3.x no longer supports direct assignment to `vfs`.
  // Use the public API so the font exists in the virtual file system.
  if (typeof pdfMake.addVirtualFileSystem === "function") {
    pdfMake.addVirtualFileSystem(mergedVfs);
  } else {
    (pdfMake as { vfs?: Record<string, string> }).vfs = mergedVfs;
  }

  const mergedFonts = {
    ...(pdfMake.fonts || {}),
    NotoSansHebrew: {
      normal: FONT_FILE,
      bold: FONT_FILE,
      italics: FONT_FILE,
      bolditalics: FONT_FILE,
    },
  };

  if (typeof pdfMake.addFonts === "function") {
    pdfMake.addFonts(mergedFonts);
  } else {
    pdfMake.fonts = mergedFonts;
  }

  return pdfMake;
}
