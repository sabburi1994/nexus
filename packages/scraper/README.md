# @nexus-agent-framework/scraper

> **Ethical web scraping protocols, RSS ingestion contracts, and rate-limiting policies for autonomous agents.**

- **Website & Platform Portal**: [nexus.abburi.info](https://nexus.abburi.info)
- **Documentation**: [nexus.abburi.info/#docs](https://nexus.abburi.info/#docs)

[![npm version](https://img.shields.io/npm/v/@nexus-agent-framework/scraper.svg)](https://www.npmjs.com/package/@nexus-agent-framework/scraper)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

`@nexus-agent-framework/scraper` enforces polite, resilient web scraping practices for AI data collection and radar pipelines:
- **`DEFAULT_NEXUS_SCRAPING_POLICY`**: Strict rate limits (2 req/sec), 512 KB payload caps, and automatic `robots.txt` compliance.
- **`ScrapedItem`**: Normalized data contract for web listings, news feeds, and job postings.
- **`ScrapingPolicy`**: Configurable rules for timeouts, backoffs, and user-agent declarations.

## Installation

```bash
npm install @nexus-agent-framework/scraper
```

## Quickstart

```typescript
import {
  DEFAULT_NEXUS_SCRAPING_POLICY,
  ScrapedItem,
} from "@nexus-agent-framework/scraper";

// Example polite crawler configuration
const policy = {
  ...DEFAULT_NEXUS_SCRAPING_POLICY,
  userAgent: "NexusBot/1.0 (+https://github.com/sabburi1994/nexus)",
  rateLimitPerSecond: 1, // 1 request per second
};
```

## Versions and release notes

Latest stable: **1.0.3**. 1.0.3 updates this page only; the code is the same as 1.0.2.
Every release is listed in the [changelog](https://github.com/sabburi1994/nexus/blob/main/CHANGELOG.md) and on the [GitHub releases](https://github.com/sabburi1994/nexus/releases) page.

The Nexus packages:

| Package | Latest stable |
| :--- | :--- |
| [`@nexus-agent-framework/tokens`](https://www.npmjs.com/package/@nexus-agent-framework/tokens) | 1.0.1 |
| [`@nexus-agent-framework/ui`](https://www.npmjs.com/package/@nexus-agent-framework/ui) | 1.0.2 |
| [`@nexus-agent-framework/contracts`](https://www.npmjs.com/package/@nexus-agent-framework/contracts) | 1.0.4 |
| [`@nexus-agent-framework/middleware`](https://www.npmjs.com/package/@nexus-agent-framework/middleware) | 1.0.3 |
| [`@nexus-agent-framework/scraper`](https://www.npmjs.com/package/@nexus-agent-framework/scraper) | 1.0.3 |
| [`nexus-agent-framework`](https://pypi.org/project/nexus-agent-framework/) (Python, PyPI) | 0.5.1 |

## License

Licensed under the Apache 2.0 License. Platform portal & docs at [nexus.abburi.info](https://nexus.abburi.info). Part of the [Nexus Agent Framework](https://github.com/sabburi1994/nexus).
