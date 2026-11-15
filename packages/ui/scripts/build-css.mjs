// Bundles src/styles/index.css (inlining its relative @imports, in order) into dist/styles.css.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const seen = new Set();

function inline(file) {
  const path = resolve(file);
  if (seen.has(path)) return "";
  seen.add(path);
  const css = readFileSync(path, "utf8");
  return css.replace(/^@import\s+"(\.[^"]+)";\s*$/gm, (_, rel) => inline(join(dirname(path), rel)));
}

const out = inline(join(root, "src", "styles", "index.css"));
if (/@import/.test(out)) throw new Error("unresolved @import left in styles.css");
mkdirSync(join(root, "dist"), { recursive: true });
writeFileSync(join(root, "dist", "styles.css"), out);
console.log(`ui: wrote dist/styles.css (${out.length} bytes)`);
