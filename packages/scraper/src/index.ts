/**
 * @nexus/scraper
 * Polite web scraping, RSS parsing contracts, and URL canonicalization.
 */

export interface ScrapedItem {
  id: string;
  url: string;
  title: string;
  summary: string;
  publishedAt: string;
  sourceDomain: string;
  contentHash: string;
  httpStatus: number;
}

export interface ScrapingPolicy {
  userAgent: string;
  timeoutMs: number;
  maxContentBytes: number;
  rateLimitPerSecond: number;
  respectRobotsTxt: boolean;
}

export const DEFAULT_NEXUS_SCRAPING_POLICY: ScrapingPolicy = {
  userAgent: "Nexus-AutonomousObservatory/1.0 (+https://nexus.framework)",
  timeoutMs: 10000,
  maxContentBytes: 524288, // 512 KB
  rateLimitPerSecond: 2,
  respectRobotsTxt: true,
};
