import { createRequire } from "node:module";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

async function main() {
  const [htmlArg, pdfArg] = process.argv.slice(2);
  if (!htmlArg || !pdfArg) {
    throw new Error("用法：node render_html_to_pdf.mjs <input.html> <output.pdf>");
  }

  const htmlPath = path.resolve(htmlArg);
  const pdfPath = path.resolve(pdfArg);

  await mkdir(path.dirname(pdfPath), { recursive: true });

  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
    await page.emulateMedia({ media: "print" });
    await page.pdf({
      path: pdfPath,
      format: "A4",
      printBackground: true,
      preferCSSPageSize: true,
      margin: {
        top: "10mm",
        right: "10mm",
        bottom: "12mm",
        left: "10mm",
      },
    });
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error?.stack || String(error));
  process.exit(1);
});
