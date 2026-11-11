# @nexus-agent-framework/middleware

> **Production security headers, zero-leak credential scrubbing, and correlation ID tracing for web applications.**

- **Website & Guardrail Sandbox**: [nexus.abburi.info/#telemetry](https://nexus.abburi.info/#telemetry)
- **Documentation**: [nexus.abburi.info/#docs](https://nexus.abburi.info/#docs)

[![npm version](https://img.shields.io/npm/v/@nexus-agent-framework/middleware.svg)](https://www.npmjs.com/package/@nexus-agent-framework/middleware)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

`@nexus-agent-framework/middleware` provides hardened security and telemetry utilities designed for Express, Fastify, Next.js, and Hono backends:
- **`NEXUS_SECURITY_HEADERS`**: Baseline OWASP-recommended HTTP security headers (CSP, HSTS, X-Frame-Options, Permissions-Policy).
- **`scrubSensitiveData`**: Zero-leak regex sanitizer that strips Bearer tokens, Gemini API keys (`AIzaSy...`), OpenAI keys (`sk-...`), and database credentials from strings before logging.
- **`generateCorrelationId`**: Lightweight, collision-resistant correlation IDs (`nx-timestamp-random`) for end-to-end request tracing.

## Installation

```bash
npm install @nexus-agent-framework/middleware
```

## Quickstart

### Express Middleware Example

```typescript
import express from "express";
import {
  NEXUS_SECURITY_HEADERS,
  scrubSensitiveData,
  generateCorrelationId,
} from "@nexus-agent-framework/middleware";

const app = express();

// Apply security headers
app.use((req, res, next) => {
  res.set(NEXUS_SECURITY_HEADERS);
  req.headers["x-correlation-id"] = generateCorrelationId();
  next();
});

// Scrub logs before sending to datadog / cloud logging
app.use((err, req, res, next) => {
  const safeMessage = scrubSensitiveData(err.stack || err.message);
  console.error(`[CRITICAL] Correlation: ${req.headers["x-correlation-id"]} - ${safeMessage}`);
  res.status(500).json({ error: "Internal Server Error" });
});
```

## License

Licensed under the Apache 2.0 License. Live platform & docs at [nexus.abburi.info](https://nexus.abburi.info). Part of the [Nexus Agent Framework](https://github.com/sabburi1994/nexus).
