// @vitest-environment node
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { gunzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";

// The committed tarballs in releases/ must be the current source versions and contain the built files,
// because apps install them by URL from the tagged commit.
const repo = join(process.cwd(), "..", "..");

function readTar(file: string): Map<string, Buffer> {
  const data = gunzipSync(readFileSync(file));
  const entries = new Map<string, Buffer>();
  let offset = 0;
  while (offset + 512 <= data.length) {
    const header = data.subarray(offset, offset + 512);
    if (header.every((b) => b === 0)) break;
    const field = (start: number, length: number) => header.subarray(start, start + length).toString("utf8").replace(/\0.*$/s, "");
    const prefix = field(345, 155);
    const name = (prefix ? `${prefix}/` : "") + field(0, 100);
    const size = parseInt(field(124, 12).trim() || "0", 8);
    entries.set(name, data.subarray(offset + 512, offset + 512 + size));
    offset += 512 + Math.ceil(size / 512) * 512;
  }
  return entries;
}

// Skipped while scripts/release-ui.mjs is packing (the tarballs are being rebuilt); it runs again after.
describe.skipIf(process.env.NEXUS_RELEASE_PACKING === "1").each([
  ["tokens", ["package/dist/index.js", "package/dist/tokens.css", "package/dist/tailwind4.css", "package/dist/tailwind-preset.cjs", "package/dist/themes/finhub.css"]],
  ["ui", ["package/dist/index.js", "package/dist/index.d.ts", "package/dist/styles.css", "package/dist/showcase/index.js"]],
])("release tarball for %s", (name, required) => {
  const source = JSON.parse(readFileSync(join(repo, "packages", name, "package.json"), "utf8")) as { version: string };
  const file = join(repo, "releases", `nexus-agent-framework-${name}-${source.version}.tgz`);

  it("exists for the current source version", () => {
    expect(existsSync(file), `${file} missing: run node scripts/release-ui.mjs`).toBe(true);
  });

  it("carries the same version and the built files", () => {
    const entries = readTar(file);
    const manifest = JSON.parse(entries.get("package/package.json")?.toString("utf8") ?? "{}") as { version?: string };
    expect(manifest.version).toBe(source.version);
    for (const path of required) expect([...entries.keys()], path).toContain(path);
    expect([...entries.keys()].some((p) => p.includes("/tests/") || p.includes("/src/"))).toBe(false);
  });
});
