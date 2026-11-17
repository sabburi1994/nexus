import React, { useEffect, useState } from "react";
import "@nexus-agent-framework/tokens/tokens.css";
import "@nexus-agent-framework/ui/styles.css";
import "./gallery.css";
import { THEMES, THEME_NAMES, type Mode, type ThemeName } from "@nexus-agent-framework/tokens";
import {
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
  Sheet,
  SkeletonRows,
  Stat,
  Switch,
  Table,
  Tabs,
  Textarea,
  ToastProvider,
  useToast,
  type TableColumn,
  type Tone,
} from "@nexus-agent-framework/ui";

/** Route: #gallery, #gallery/<theme>, #gallery/<theme>/<mode>. */
export function parseGalleryHash(hash: string): { theme: ThemeName; mode: Mode } {
  const [, theme, mode] = hash.replace(/^#\/?/, "").toLowerCase().split("/");
  return {
    theme: (THEME_NAMES as readonly string[]).includes(theme) ? (theme as ThemeName) : "finhub",
    mode: mode === "dark" ? "dark" : "light",
  };
}

const ROLE_GROUPS: Array<{ title: string; roles: Array<keyof (typeof THEMES)["base"]["light"]> }> = [
  { title: "Surfaces", roles: ["bg", "surface", "surfaceSunken", "border", "borderStrong", "control"] },
  { title: "Text and action", roles: ["text", "textMuted", "primary", "primaryHover", "primarySubtle", "focus"] },
  { title: "Status", roles: ["successText", "warningText", "danger", "infoText", "dangerSubtle", "successSubtle"] },
  { title: "Topic accents", roles: ["accent1", "accent2", "accent3", "accent4", "chartLine", "chartFloor"] },
  { title: "Navigation", roles: ["nav", "navText", "navActive", "navActiveText", "navTextMuted", "skeleton"] },
];

function kebab(role: string): string {
  return role.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
}

const Icon = {
  today: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3.5" y="5" width="17" height="15" rx="2" />
      <path d="M3.5 9.5h17M8 3v4M16 3v4" />
    </svg>
  ),
  money: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <circle cx="12" cy="12" r="2.5" />
    </svg>
  ),
  chart: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19h16M5 15l4-4 3 3 6-7" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4" />
    </svg>
  ),
  plus: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <path d="M12 5v14M5 12h14" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <circle cx="11" cy="11" r="6" />
      <path d="m20 20-4.5-4.5" />
    </svg>
  ),
  empty: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 13h4l2 3h4l2-3h4M4 13l2.5-7h11L20 13v5H4z" />
    </svg>
  ),
};

interface Payment {
  id: string;
  date: string;
  payee: string;
  category: string;
  amount: string;
  status: { tone: Tone; label: string };
}

const PAYMENTS: Payment[] = [
  { id: "p1", date: "3 Nov", payee: "Landlord", category: "Housing", amount: "950.00", status: { tone: "success", label: "Paid" } },
  { id: "p2", date: "5 Nov", payee: "Electricity", category: "Utilities", amount: "84.20", status: { tone: "success", label: "Paid" } },
  { id: "p3", date: "12 Nov", payee: "Credit card", category: "Card", amount: "412.75", status: { tone: "warning", label: "Due 15 Nov" } },
  { id: "p4", date: "20 Nov", payee: "Insurance", category: "Insurance", amount: "61.90", status: { tone: "neutral", label: "Scheduled" } },
];

const BALANCE = [
  { label: "1 Nov", value: 3120 },
  { label: "5 Nov", value: 2086 },
  { label: "10 Nov", value: 1990 },
  { label: "15 Nov", value: 1577 },
  { label: "20 Nov", value: 1515 },
  { label: "25 Nov", value: 3420 },
  { label: "30 Nov", value: 3288 },
];
const LAST_MONTH = BALANCE.map((p, i) => ({ label: p.label, value: [2950, 2200, 2010, 1720, 1650, 3300, 3180][i] }));

const eur = (v: number) => `${v.toLocaleString("en-GB", { maximumFractionDigits: 0 })} EUR`;

function Section({ id, title, description, children }: { id: string; title: string; description?: string; children: React.ReactNode }) {
  return (
    <section className="gx-section" aria-labelledby={`gx-${id}`}>
      <div className="gx-section__head">
        <h3 id={`gx-${id}`} className="gx-section__title">
          {title}
        </h3>
        {description ? <p className="gx-section__description">{description}</p> : null}
      </div>
      {children}
    </section>
  );
}

function ToastButtons() {
  const { toast } = useToast();
  return (
    <>
      <Button onClick={() => toast({ title: "Payment saved", description: "Electricity, 84.20 EUR", tone: "success" })}>Show success toast</Button>
      <Button onClick={() => toast({ title: "Sync failed", description: "The bank did not answer. Nothing was changed.", tone: "danger" })}>
        Show danger toast
      </Button>
    </>
  );
}

function ComponentPreview({ theme }: { theme: ThemeName }) {
  const accents = THEMES[theme].accentNames;
  const [dialogOpen, setDialogOpen] = useState(false);
  const [sheetRow, setSheetRow] = useState<Payment | null>(null);
  const [tableState, setTableState] = useState<"rows" | "loading" | "empty">("rows");
  const [period, setPeriod] = useState("month");

  const columns: TableColumn<Payment>[] = [
    { key: "payee", header: "Payee", rowHeader: true },
    { key: "date", header: "Date" },
    { key: "category", header: "Category", hideOnMobile: true },
    { key: "status", header: "Status", hideOnMobile: true, render: (p) => <Badge tone={p.status.tone}>{p.status.label}</Badge> },
    { key: "amount", header: "Amount (EUR)", numeric: true },
  ];

  return (
    <div className="gx-preview">
      <Section id="buttons" title="Buttons" description="40 px high. One primary action per area; quiet for low emphasis; danger only for destructive actions.">
        <div className="gx-row">
          <Button variant="primary">Save payment</Button>
          <Button variant="secondary">Export</Button>
          <Button variant="quiet">View details</Button>
          <Button variant="danger">Delete</Button>
        </div>
        <div className="gx-row">
          <Button variant="primary" iconStart={Icon.plus}>
            Add payment
          </Button>
          <Button variant="secondary" size="sm">
            Small
          </Button>
          <Button variant="primary" loading>
            Saving
          </Button>
          <Button variant="secondary" disabled>
            Disabled
          </Button>
          <IconButton label="Search" icon={Icon.search} variant="secondary" />
          <IconButton label="Settings" icon={Icon.settings} />
        </div>
      </Section>

      <Section id="forms" title="Form controls" description="Visible labels, hints and errors linked to the control; numbers right aligned.">
        <div className="gx-grid gx-grid--2">
          <Input label="Amount" hint="In euros, two decimals" numeric defaultValue="84.20" />
          <Input label="IBAN" error="This IBAN has 21 characters; Dutch IBANs have 18." defaultValue="NL91ABNA04171643000" />
          <Select
            label="Category"
            placeholder="Choose a category"
            options={[
              { value: "housing", label: "Housing" },
              { value: "utilities", label: "Utilities" },
              { value: "insurance", label: "Insurance" },
            ]}
          />
          <Textarea label="Note" hint="Shown on the statement" rows={3} />
          <RadioGroup
            label="Period"
            name={`period-${theme}`}
            inline
            value={period}
            onChange={setPeriod}
            options={[
              { value: "week", label: "Week" },
              { value: "month", label: "Month" },
              { value: "year", label: "Year" },
            ]}
          />
          <div className="gx-stack">
            <Checkbox label="Recurring payment" hint="Repeats on the same day every month" defaultChecked />
            <Switch label="Hide amounts" />
          </div>
        </div>
      </Section>

      <Section id="cards" title="Cards, numbers and badges" description="White surface, hairline border, faint shadow. One number per card.">
        <div className="gx-grid gx-grid--3">
          <Card title={accents[0]} description="All current accounts" accent="accent1" headingLevel={4}>
            <Stat label="Available today" value="3,288.40 EUR" hint="Updated 08:10" status={{ tone: "success", label: "Above floor" }} />
          </Card>
          <Card title={accents[1]} description="Next 14 days" accent="accent2" headingLevel={4}>
            <Stat label="Scheduled" value="474.65 EUR" hint="2 payments" status={{ tone: "warning", label: "1 due soon" }} />
          </Card>
          <Card title={accents[2]} description="Open positions" accent="accent3" headingLevel={4} actions={<Button variant="quiet" size="sm">Open</Button>}>
            <Stat label="Market value" value="1,920.00 EUR" hint="Since 1 Nov: plus 2.4 percent" />
          </Card>
        </div>
        <div className="gx-row">
          {(["neutral", "primary", "success", "warning", "danger", "info"] as Tone[]).map((tone) => (
            <Badge key={tone} tone={tone}>
              {tone.charAt(0).toUpperCase() + tone.slice(1)}
            </Badge>
          ))}
          {(["accent1", "accent2", "accent3", "accent4"] as Tone[]).map((tone, i) => (
            <Badge key={tone} tone={tone}>
              {accents[i]}
            </Badge>
          ))}
        </div>
      </Section>

      <Section id="table" title="Table" description="Right aligned tabular numbers, sticky header, scrolls inside its own region. Click a payee to open the side sheet.">
        <div className="gx-row">
          <RadioGroup
            label="Table state"
            name={`table-state-${theme}`}
            inline
            value={tableState}
            onChange={(v) => setTableState(v as typeof tableState)}
            options={[
              { value: "rows", label: "Rows" },
              { value: "loading", label: "Loading" },
              { value: "empty", label: "Empty" },
            ]}
          />
        </div>
        <Card title="November payments" flush headingLevel={4}>
          <Table
            caption="November payments"
            hideCaption
            columns={columns}
            rows={tableState === "rows" ? PAYMENTS : []}
            loading={tableState === "loading"}
            empty={<EmptyState title="No payments this month" description="Payments appear here once booked." />}
            getRowKey={(p) => p.id}
            onRowClick={setSheetRow}
            footer={{ payee: "Total", amount: "1,508.85" }}
          />
        </Card>
      </Section>

      <Section id="chart" title="Line chart" description="A thin line, last month for comparison, and a labelled floor line.">
        <Card title="Balance, November" headingLevel={4}>
          <LineChart
            title="Balance, November"
            data={BALANCE}
            seriesName="November"
            compare={{ name: "October", data: LAST_MONTH }}
            floor={{ value: 1000, label: "Floor 1,000 EUR" }}
            formatValue={eur}
          />
        </Card>
      </Section>

      <Section id="tabs" title="Tabs" description="Arrow keys move between tabs; Home and End jump.">
        <Tabs
          label="Spaces"
          items={[
            { id: "today", label: "Today", content: <p className="gx-copy">Three payments are due this week, all covered by the current balance.</p> },
            { id: "money", label: "Money", content: <p className="gx-copy">Money shows accounts, payments and the floor.</p> },
            { id: "trading", label: "Trading", content: <p className="gx-copy">Trading shows open positions and their budgets.</p> },
          ]}
        />
      </Section>

      <Section id="overlays" title="Dialog, sheet and toast" description="Escape closes; focus returns to the button that opened them.">
        <div className="gx-row">
          <Button variant="primary" onClick={() => setDialogOpen(true)}>
            Open dialog
          </Button>
          <Button onClick={() => setSheetRow(PAYMENTS[2])}>Open sheet</Button>
          <ToastButtons />
        </div>
        <Dialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          title="Delete this payment?"
          description="Credit card, 412.75 EUR, due 15 Nov. This cannot be undone."
          footer={
            <>
              <Button onClick={() => setDialogOpen(false)}>Keep</Button>
              <Button variant="danger" onClick={() => setDialogOpen(false)}>
                Delete payment
              </Button>
            </>
          }
        >
          <Checkbox label="Also remove the reminder" />
        </Dialog>
        <Sheet
          open={sheetRow !== null}
          onClose={() => setSheetRow(null)}
          title={sheetRow ? sheetRow.payee : "Payment"}
          description={sheetRow ? `${sheetRow.date}, ${sheetRow.category}` : undefined}
          footer={
            <>
              <Button onClick={() => setSheetRow(null)}>Close</Button>
              <Button variant="primary" onClick={() => setSheetRow(null)}>
                Mark as paid
              </Button>
            </>
          }
        >
          {sheetRow ? (
            <div className="gx-stack">
              <Stat label="Amount" value={`${sheetRow.amount} EUR`} status={sheetRow.status} />
              <Input label="Reference" defaultValue={`NOV-${sheetRow.id.toUpperCase()}`} />
              <Textarea label="Note" rows={3} />
            </div>
          ) : null}
        </Sheet>
      </Section>

      <Section id="states" title="Loading, empty and error" description="Skeleton rows instead of spinners; every empty or failed state says what to do next.">
        <div className="gx-grid gx-grid--3">
          <Card title="Loading" headingLevel={4}>
            <SkeletonRows rows={3} columns={3} label="Loading payments" />
          </Card>
          <Card title="Empty" headingLevel={4}>
            <EmptyState icon={Icon.empty} title="No trades yet" description="Trades appear here once an order is filled." action={<Button size="sm">Open trading</Button>} />
          </Card>
          <Card title="Error" headingLevel={4}>
            <ErrorState description="The bank connection timed out. Nothing was changed." onRetry={() => undefined} />
          </Card>
        </div>
      </Section>

      <Section id="shell" title="Navigation shell" description="Side rail from 768 px, a bottom bar of spaces on phones, and a skip link (press Tab inside the frame).">
        <div className="gx-shell-frame">
          <AppShell
            brand={THEMES[theme].label}
            title="Today"
            mainId={`gx-main-${theme}`}
            navLabel={`${THEMES[theme].label} demo navigation`}
            nav={[
              { id: "today", label: "Today", icon: Icon.today, current: true },
              { id: "money", label: "Money", icon: Icon.money },
              { id: "trading", label: "Trading", icon: Icon.chart },
              { id: "settings", label: "Settings", icon: Icon.settings },
            ]}
            actions={<IconButton label="Search" icon={Icon.search} />}
          >
            <div className="gx-grid gx-grid--2">
              <Card title={accents[0]} accent="accent1" headingLevel={4}>
                <Stat label="Available" value="3,288.40 EUR" />
              </Card>
              <Card title={accents[1]} accent="accent2" headingLevel={4}>
                <Stat label="Due this week" value="412.75 EUR" />
              </Card>
            </div>
          </AppShell>
        </div>
      </Section>
    </div>
  );
}

function ThemeSwatches() {
  return (
    <div className="gx-swatches">
      {ROLE_GROUPS.map((group) => (
        <div key={group.title} className="gx-swatch-group">
          <p className="gx-swatch-group__title">{group.title}</p>
          <ul className="gx-swatch-list">
            {group.roles.map((role) => (
              <li key={role} className="gx-swatch">
                <span className={`gx-swatch__chip gx-chip--${kebab(role)}`} aria-hidden="true" />
                <code className="gx-swatch__name">--nx-color-{kebab(role)}</code>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function AllThemes() {
  return (
    <div className="gx-all">
      {THEME_NAMES.map((name) =>
        (["light", "dark"] as const).map((mode) => (
          <div key={`${name}-${mode}`} data-nx-theme={name} data-nx-mode={mode} className="gx-mini">
            <p className="gx-mini__title">
              {THEMES[name].label} <span className="gx-mini__mode">{mode}</span>
            </p>
            <Stat label="Available" value="3,288.40 EUR" />
            <div className="gx-row gx-row--tight">
              {(["accent1", "accent2", "accent3", "accent4"] as Tone[]).map((tone, i) => (
                <Badge key={tone} tone={tone}>
                  {THEMES[name].accentNames[i]}
                </Badge>
              ))}
            </div>
            <div className="gx-row gx-row--tight">
              <Button variant="primary" size="sm">
                Primary
              </Button>
              <Button size="sm">Secondary</Button>
              <Button variant="quiet" size="sm">
                Quiet
              </Button>
            </div>
          </div>
        )),
      )}
    </div>
  );
}

/** Design system gallery: every kit component in every app theme, light and dark. */
export default function GallerySection() {
  const [{ theme, mode }, setRoute] = useState(() => parseGalleryHash(window.location.hash));

  useEffect(() => {
    const onHash = () => setRoute(parseGalleryHash(window.location.hash));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const update = (next: { theme?: ThemeName; mode?: Mode }) => {
    const t = next.theme ?? theme;
    const m = next.mode ?? mode;
    window.location.hash = `#gallery/${t}/${m}`;
  };

  return (
    <div className="gx-page">
      <header className="gx-intro">
        <p className="gx-eyebrow">Design system</p>
        <h2 className="gx-title">Platform UI kit</h2>
        <p className="gx-lede">
          <code>@nexus-agent-framework/tokens</code> 1.0.1 and <code>@nexus-agent-framework/ui</code> 1.0.2: one set of tokens
          and React components for FinHub, TandemPath, PredictiveEconomics, CommandCenter and klassesall. Pick an app theme and
          a mode; every component below re-themes from CSS variables alone.
        </p>
        <p className="gx-lede gx-install">
          <code>npm install @nexus-agent-framework/tokens @nexus-agent-framework/ui</code>
        </p>
      </header>

      <div data-nx-theme={theme} data-nx-mode={mode} className="gx-canvas">
        <ToastProvider>
          <div className="gx-controls">
            <Select
              label="App theme"
              value={theme}
              onChange={(e) => update({ theme: e.target.value as ThemeName })}
              options={THEME_NAMES.map((n) => ({ value: n, label: THEMES[n].label }))}
              fieldClassName="gx-controls__theme"
            />
            <RadioGroup
              label="Mode"
              name="gx-mode"
              inline
              value={mode}
              onChange={(v) => update({ mode: v as Mode })}
              options={[
                { value: "light", label: "Light" },
                { value: "dark", label: "Dark" },
              ]}
            />
          </div>
          <Section id="tokens" title="Colour roles" description={`${THEMES[theme].label}, ${mode}. Every text and state pair passes WCAG AA (tested).`}>
            <ThemeSwatches />
          </Section>
          <ComponentPreview key={`${theme}-${mode}`} theme={theme} />
        </ToastProvider>
      </div>

      <section className="gx-all-section" aria-labelledby="gx-all-title">
        <h3 id="gx-all-title" className="gx-all-section__title">
          All themes at a glance
        </h3>
        <AllThemes />
      </section>
    </div>
  );
}
