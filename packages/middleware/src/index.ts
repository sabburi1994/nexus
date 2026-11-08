/**
 * @nexus/middleware
 * Shared middleware rules and helpers for web servers (Express, Fastify, Next.js, FastAPI).
 */

export const NEXUS_SECURITY_HEADERS = {
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
  "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none';",
};

export const SENSITIVE_KEY_PATTERNS = [
  /api[_-]?key/i,
  /secret/i,
  /password/i,
  /token/i,
  /authorization/i,
  /bearer\s+[A-Za-z0-9._~+/-]+=*/i,
  /AIzaSy[A-Za-z0-9_-]{33}/,
  /sk-[A-Za-z0-9]{48}/,
];

/**
 * Scrubs credentials and secrets from logs and error messages before output.
 */
export function scrubSensitiveData(text: string): string {
  let cleaned = text;
  // Redact Bearer tokens
  cleaned = cleaned.replace(/Bearer\s+[A-Za-z0-9._~+/-]+=*/gi, "Bearer [REDACTED_TOKEN]");
  // Redact Google AI / Gemini API keys
  cleaned = cleaned.replace(/AIzaSy[A-Za-z0-9_-]{33}/g, "AIzaSy[REDACTED_GEMINI_KEY]");
  // Redact OpenAI / Anthropic format keys
  cleaned = cleaned.replace(/sk-[A-Za-z0-9_-]{20,}/g, "sk-[REDACTED_API_KEY]");
  // Redact basic auth passwords
  cleaned = cleaned.replace(/:\/\/[^:]+:([^@]+)@/g, "://[USER]:[REDACTED_PW]@");
  return cleaned;
}

/**
 * Creates correlation request ID header for end-to-end tracing across services.
 */
export function generateCorrelationId(): string {
  return `nx-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
