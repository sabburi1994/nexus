// Builds, tests and packs @nexus-agent-framework/tokens and @nexus-agent-framework/ui into
// releases/, then prints the tag and npm publish commands for the owner and the install lines.
//
//   node scripts/release-ui.mjs        (or: npm run release:ui)
//
// The committed tarballs are what the owner publishes to npm, so the registry serves the same
// bytes as the repository. They can also be installed by URL from the tag (fallback). The tag is
// ui-v<ui version>.
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, rmSync } from "node:fs";
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

// A released version is immutable: when the tarball for a package's current version already
// exists it is kept as is (repacking on another machine changes bytes, for example line endings,
// and with them the integrity hash apps recorded). Bump the version to ship a change.
for (const name of packages) {
  const prefix = `nexus-agent-framework-${name}-`;
  const current = `${prefix}${pkg(name).version}.tgz`;
  if (existsSync(join(releases, current))) {
    console.log(`kept ${current} (version unchanged)`);
    continue;
  }
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
const tokensFile = `releases/nexus-agent-framework-tokens-${pkg("tokens").version}.tgz`;
const uiFile = `releases/nexus-agent-framework-ui-${pkg("ui").version}.tgz`;
console.log(`
Packed into releases/. Commit them and merge; then the owner tags the merge commit and publishes
(tokens first; a version already on npm is refused, which is harmless):

  git tag -a ${tag} <merge commit> -m "${tag}" && git push origin ${tag}
  npm publish ${tokensFile} --access public
  npm publish ${uiFile} --access public

Install:          npm install @nexus-agent-framework/tokens @nexus-agent-framework/ui
By URL (pinned):  npm install ${tokensUrl} ${uiUrl}
`);
