// Builds, tests and packs @nexus-agent-framework/tokens and @nexus-agent-framework/ui into
// releases/, then prints the install lines and the tag the owner pushes.
//
//   node scripts/release-ui.mjs
//
// Apps install the tarballs straight from the tagged commit over HTTPS, so nothing is published
// to npm and no git is needed inside Docker builds. The tag is ui-v<ui version>.
import { execFileSync } from "node:child_process";
import { readdirSync, readFileSync, rmSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const releases = join(root, "releases");
const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const run = (args, env = {}) =>
  execFileSync(npm, args, { cwd: root, stdio: "inherit", shell: process.platform === "win32", env: { ...process.env, ...env } });
const pkg = (name) => JSON.parse(readFileSync(join(root, "packages", name, "package.json"), "utf8"));

const packages = ["tokens", "ui"];
for (const name of packages) {
  run(["run", "build", "-w", `@nexus-agent-framework/${name}`]);
  run(["run", "test", "-w", `@nexus-agent-framework/${name}`], { NEXUS_RELEASE_PACKING: "1" });
}

for (const name of packages) {
  const prefix = `nexus-agent-framework-${name}-`;
  for (const old of readdirSync(releases).filter((f) => f.startsWith(prefix) && f.endsWith(".tgz"))) {
    rmSync(join(releases, old));
  }
  run(["pack", "-w", `@nexus-agent-framework/${name}`, "--pack-destination", releases]);
}

// Verify the fresh tarballs (versions and contents).
run(["run", "test", "-w", "@nexus-agent-framework/ui", "--", "tests/release.test.ts"]);

const tag = `ui-v${pkg("ui").version}`;
const base = `https://raw.githubusercontent.com/sabburi1994/nexus/${tag}/releases`;
const tokensUrl = `${base}/nexus-agent-framework-tokens-${pkg("tokens").version}.tgz`;
const uiUrl = `${base}/nexus-agent-framework-ui-${pkg("ui").version}.tgz`;
console.log(`
Packed into releases/. Commit them, merge, then the owner tags the merge commit:

  git tag ${tag} <merge commit> && git push origin ${tag}

React apps:   npm install ${tokensUrl} ${uiUrl}
Tokens only:  npm install ${tokensUrl}
`);
