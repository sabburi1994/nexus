// Writes the CSS and Tailwind files from the compiled module (run after `tsc`).
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dist = join(root, "dist");
const tokens = await import(new URL("../dist/index.js", import.meta.url).href);

mkdirSync(join(dist, "themes"), { recursive: true });

writeFileSync(join(dist, "tokens.css"), tokens.tokensCss());
for (const name of tokens.THEME_NAMES) {
  writeFileSync(join(dist, "themes", `${name}.css`), tokens.singleThemeCss(name));
}
writeFileSync(join(dist, "tailwind4.css"), tokens.tailwind4Css());

const preset = JSON.stringify(tokens.tailwindPreset(), null, 2);
const banner = "// @nexus-agent-framework/tokens Tailwind 3 preset. Generated, do not edit.\n";
writeFileSync(join(dist, "tailwind-preset.js"), `${banner}export default ${preset};\n`);
writeFileSync(join(dist, "tailwind-preset.cjs"), `${banner}module.exports = ${preset};\n`);
writeFileSync(
  join(dist, "tailwind-preset.d.ts"),
  'import type { TailwindPreset } from "./tailwind.js";\ndeclare const preset: TailwindPreset;\nexport default preset;\n',
);

console.log(`tokens: wrote tokens.css, ${tokens.THEME_NAMES.length} theme files, tailwind presets`);
