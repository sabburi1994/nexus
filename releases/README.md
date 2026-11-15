# Release tarballs

Built packages for the platform apps, installed straight from a git tag over HTTPS instead of the npm
registry. `node scripts/release-ui.mjs` builds, tests and packs them into this folder; the owner then
pushes the tag `ui-v<ui version>` on the merge commit.

| File | Package |
| :--- | :--- |
| `nexus-agent-framework-tokens-<version>.tgz` | `@nexus-agent-framework/tokens` (CSS variables, themes, Tailwind 3 and 4 presets) |
| `nexus-agent-framework-ui-<version>.tgz` | `@nexus-agent-framework/ui` (React kit; needs the tokens package) |

React apps (version 1.0.0, tag `ui-v1.0.0`):

```bash
npm install https://raw.githubusercontent.com/sabburi1994/nexus/ui-v1.0.0/releases/nexus-agent-framework-tokens-1.0.0.tgz https://raw.githubusercontent.com/sabburi1994/nexus/ui-v1.0.0/releases/nexus-agent-framework-ui-1.0.0.tgz
```

Tokens only (for example the Vue app):

```bash
npm install https://raw.githubusercontent.com/sabburi1994/nexus/ui-v1.0.0/releases/nexus-agent-framework-tokens-1.0.0.tgz
```

npm records each URL with its integrity hash in `package-lock.json`, so installs are reproducible and
need no git inside Docker builds. To upgrade, install the URLs of a newer tag. Older tags keep serving
their own tarballs, because each tag points at the commit that holds them.
