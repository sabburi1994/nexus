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

## License

Licensed under the Apache 2.0 License. Platform portal & docs at [nexus.abburi.info](https://nexus.abburi.info). Part of the [Nexus Agent Framework](https://github.com/sabburi1994/nexus).
