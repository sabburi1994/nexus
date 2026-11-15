import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import axe from "axe-core";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import React, { useState } from "react";
import { describe, expect, it } from "vitest";

import * as kit from "../src/index.js";

const {
  AppShell,
  Badge,
  Button,
  Card,
  Checkbox,
  Dialog,
  EmptyState,
  ErrorState,
  IconButton,
  Input,
  LineChart,
  RadioGroup,
  Select,
  SkeletonRows,
  Stat,
  Switch,
  Table,
  Tabs,
  Textarea,
  ToastProvider,
} = kit;

// Vitest runs with the package directory as the working directory.
const SRC = join(process.cwd(), "src");

function Everything() {
  const [open, setOpen] = useState(false);
  return (
    <ToastProvider>
      <AppShell
        brand="Nexus"
        title="Overview"
        nav={[
          { id: "today", label: "Today", current: true },
          { id: "money", label: "Money" },
        ]}
        actions={<IconButton label="Settings" icon={<svg viewBox="0 0 16 16" />} />}
      >
        <Card title="Cash" description="All accounts" accent="accent1" actions={<Button variant="quiet">Details</Button>}>
          <Stat label="Available" value="2,410.55 EUR" status={{ tone: "success", label: "Above floor" }} />
          <Badge tone="info">Synced</Badge>
          <LineChart
            title="Balance"
            data={[
              { label: "1 Nov", value: 2400 },
              { label: "30 Nov", value: 1200 },
            ]}
            floor={{ value: 1000, label: "Floor" }}
          />
        </Card>
        <Card title="Payments" flush>
          <Table
            caption="November payments"
            columns={[
              { key: "payee", header: "Payee", rowHeader: true },
              { key: "amount", header: "Amount", numeric: true },
            ]}
            rows={[{ id: "1", payee: "Landlord", amount: "950.00" }]}
            getRowKey={(r) => r.id}
          />
        </Card>
        <form aria-label="Payment form">
          <Input label="Amount" hint="In euros" error="Enter an amount" numeric />
          <Select label="Category" options={[{ value: "rent", label: "Rent" }]} />
          <Textarea label="Note" />
          <Checkbox label="Recurring" />
          <Switch label="Hide amounts" />
          <RadioGroup
            label="Period"
            name="period"
            defaultValue="month"
            options={[
              { value: "week", label: "Week" },
              { value: "month", label: "Month" },
            ]}
          />
          <Button variant="primary" type="submit">
            Save
          </Button>
          <Button variant="danger">Delete</Button>
        </form>
        <Tabs
          label="Spaces"
          items={[
            { id: "a", label: "A", content: <p>Panel A</p> },
            { id: "b", label: "B", content: <p>Panel B</p> },
          ]}
        />
        <EmptyState title="No trades yet" description="Trades appear here once placed." />
        <ErrorState description="Try again in a minute." onRetry={() => undefined} />
        <SkeletonRows rows={2} />
        <Button onClick={() => setOpen(true)}>Open dialog</Button>
        <Dialog open={open} onClose={() => setOpen(false)} title="Confirm transfer" footer={<Button variant="primary">Confirm</Button>}>
          <p>Move 200 EUR to savings?</p>
        </Dialog>
      </AppShell>
    </ToastProvider>
  );
}

async function violations(container: Element) {
  const results = await axe.run(container, {
    // jsdom has no layout or colour rendering: contrast is checked on the tokens instead
    // (packages/tokens/tests), so that rule is off here.
    rules: { "color-contrast": { enabled: false } },
  });
  return results.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.map((n) => n.target.join(" ")).join(", ")})`);
}

describe("accessibility (axe-core, offline)", () => {
  it("has no violations across the whole kit", async () => {
    const { container } = render(<Everything />);
    expect(await violations(container)).toEqual([]);
  });

  it("has no violations with a dialog open", async () => {
    const { container } = render(<Everything />);
    await userEvent.click(screen.getByRole("button", { name: "Open dialog" }));
    expect(screen.getByRole("dialog", { name: "Confirm transfer" })).toBeTruthy();
    expect(await violations(container)).toEqual([]);
  });
});

describe("policy", () => {
  it("renders no inline style attributes (works under a CSP without unsafe-inline)", () => {
    const { container } = render(<Everything />);
    expect(container.ownerDocument.querySelectorAll("[style]")).toHaveLength(0);
  });

  const files = (dir: string): string[] =>
    readdirSync(dir, { withFileTypes: true }).flatMap((d): string[] => (d.isDirectory() ? files(join(dir, d.name)) : [join(dir, d.name)]));
  const kitFiles = files(SRC).filter((f) => !f.includes(`${join("src", "showcase")}`));

  it("CSS has no gradients, blur, glows or remote resources", () => {
    for (const file of kitFiles.filter((f) => f.endsWith(".css"))) {
      const css = readFileSync(file, "utf8");
      expect(css, file).not.toMatch(/gradient|blur\(|backdrop-filter|drop-shadow|url\(|https?:\/\//i);
    }
  });

  it("kit source has no emoji or sparkle glyphs and no style props", () => {
    const emoji = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{2728}]/u;
    for (const file of kitFiles.filter((f) => /\.(ts|tsx)$/.test(f))) {
      const source = readFileSync(file, "utf8");
      expect(source, file).not.toMatch(emoji);
      expect(source, file).not.toMatch(/\bstyle=\{/);
    }
  });

  it("keeps the showcase components out of the main entry point", () => {
    for (const name of ["AiBadge", "TraceViewer", "NexusHeader", "HealingLoopPanel", "BlastRadiusCard", "RoiScorecard", "CommandBlock", "StatCard"]) {
      expect(Object.keys(kit)).not.toContain(name);
    }
  });
});
