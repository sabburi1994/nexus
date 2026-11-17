# Release tarballs

The exact tarballs published to npm for `@nexus-agent-framework/tokens` and `@nexus-agent-framework/ui`.
`node scripts/release-ui.mjs` (`npm run release:ui`) builds, tests and packs them into this folder; the
owner pushes the tag `ui-v<ui version>` on the merge commit and publishes these files to npm, so the
registry serves the same bytes that are committed here.

| File | Package |
| :--- | :--- |
| `nexus-agent-framework-tokens-<version>.tgz` | `@nexus-agent-framework/tokens` (CSS variables, themes, Tailwind 3 and 4 presets) |
| `nexus-agent-framework-ui-<version>.tgz` | `@nexus-agent-framework/ui` (React kit; needs the tokens package) |

## Install (normal)

```bash
npm install @nexus-agent-framework/tokens @nexus-agent-framework/ui   # React apps
npm install @nexus-agent-framework/tokens                            # tokens only, for example the Vue app
```

## Install by URL (fallback)

To pin a tag without the registry, install the committed files over HTTPS (ui 1.0.2 with tokens 1.0.1,
tag `ui-v1.0.2`):

```bash
npm install https://raw.githubusercontent.com/sabburi1994/nexus/ui-v1.0.2/releases/nexus-agent-framework-tokens-1.0.1.tgz https://raw.githubusercontent.com/sabburi1994/nexus/ui-v1.0.2/releases/nexus-agent-framework-ui-1.0.2.tgz
```

npm records each URL with its integrity hash in `package-lock.json`. Older tags keep serving their own
tarballs, because each tag points at the commit that holds them.

## Publishing a release (owner)

After the release PR is merged and the tag pushed, from the repository root:

```bash
git archive --format=zip -o ui-release.zip ui-v<version> releases
# unzip, then, tokens first because ui depends on it:
npm publish releases/nexus-agent-framework-tokens-<version>.tgz --access public
npm publish releases/nexus-agent-framework-ui-<version>.tgz --access public
```

A version already on npm is refused, so publishing an unchanged tokens tarball again is harmless.
