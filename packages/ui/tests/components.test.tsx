import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import React, { useState } from "react";
import { describe, expect, it, vi } from "vitest";

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
} from "../src/index.js";

const icon = <svg viewBox="0 0 16 16" />;

describe("Button and IconButton", () => {
  it("renders the variant, defaults to type=button and fires clicks", async () => {
    const onClick = vi.fn();
    render(
      <Button variant="primary" onClick={onClick}>
        Save
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Save" });
    expect(button.getAttribute("type")).toBe("button");
    expect(button.className).toContain("nx-btn--primary");
    await userEvent.click(button);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("is disabled and aria-busy while loading", async () => {
    const onClick = vi.fn();
    render(
      <Button loading onClick={onClick}>
        Saving
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Saving" });
    expect(button.hasAttribute("disabled")).toBe(true);
    expect(button.getAttribute("aria-busy")).toBe("true");
    await userEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });

  it("activates with Enter and Space", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Go</Button>);
    screen.getByRole("button", { name: "Go" }).focus();
    await userEvent.keyboard("{Enter}");
    await userEvent.keyboard(" ");
    expect(onClick).toHaveBeenCalledTimes(2);
  });

  it("names an icon button from its label and hides the icon", () => {
    render(<IconButton label="Open settings" icon={icon} />);
    const button = screen.getByRole("button", { name: "Open settings" });
    expect(button.querySelector('[aria-hidden="true"] svg')).not.toBeNull();
  });
});

describe("form fields", () => {
  it("links label, hint and error to the input", () => {
    render(<Input label="Amount" hint="In euros" error="Enter an amount" numeric />);
    const input = screen.getByLabelText("Amount");
    expect(input.getAttribute("aria-invalid")).toBe("true");
    const describedBy = (input.getAttribute("aria-describedby") ?? "").split(" ");
    const texts = describedBy.map((id) => document.getElementById(id)?.textContent);
    expect(texts).toEqual(["In euros", "Enter an amount"]);
    expect(input.className).toContain("nx-control--numeric");
  });

  it("keeps a hidden label available to assistive technology", () => {
    render(<Input label="Search" hideLabel />);
    expect(screen.getByLabelText("Search")).toBeTruthy();
    expect(screen.getByText("Search").className).toContain("nx-visually-hidden");
  });

  it("renders a native select with a placeholder option", async () => {
    const onChange = vi.fn();
    render(
      <Select
        label="Category"
        placeholder="Choose a category"
        options={[
          { value: "rent", label: "Rent" },
          { value: "food", label: "Food" },
        ]}
        onChange={(e) => onChange(e.target.value)}
      />,
    );
    const select = screen.getByLabelText("Category");
    expect(within(select).getAllByRole("option")).toHaveLength(3);
    await userEvent.selectOptions(select, "food");
    expect(onChange).toHaveBeenCalledWith("food");
  });

  it("labels a textarea", async () => {
    render(<Textarea label="Note" />);
    await userEvent.type(screen.getByLabelText("Note"), "Paid in cash");
    expect((screen.getByLabelText("Note") as HTMLTextAreaElement).value).toBe("Paid in cash");
  });
});

describe("checkbox, switch and radio group", () => {
  it("toggles a checkbox with Space", async () => {
    render(<Checkbox label="Remember this device" />);
    const box = screen.getByRole("checkbox", { name: "Remember this device" });
    box.focus();
    await userEvent.keyboard(" ");
    expect((box as HTMLInputElement).checked).toBe(true);
  });

  it("exposes a switch role and toggles with Space", async () => {
    render(<Switch label="Hide amounts" />);
    const sw = screen.getByRole("switch", { name: "Hide amounts" });
    sw.focus();
    await userEvent.keyboard(" ");
    expect((sw as HTMLInputElement).checked).toBe(true);
  });

  it("groups radios under a legend and moves with arrow keys", async () => {
    function Controlled() {
      const [value, setValue] = useState("month");
      return (
        <RadioGroup
          label="Period"
          name="period"
          value={value}
          onChange={setValue}
          options={[
            { value: "week", label: "Week" },
            { value: "month", label: "Month" },
          ]}
        />
      );
    }
    render(<Controlled />);
    expect(screen.getByRole("group", { name: "Period" })).toBeTruthy();
    const month = screen.getByRole("radio", { name: "Month" }) as HTMLInputElement;
    expect(month.checked).toBe(true);
    await userEvent.click(screen.getByRole("radio", { name: "Week" }));
    expect((screen.getByRole("radio", { name: "Week" }) as HTMLInputElement).checked).toBe(true);
  });
});

describe("Tabs", () => {
  const items = [
    { id: "today", label: "Today", content: <p>Today panel</p> },
    { id: "money", label: "Money", content: <p>Money panel</p> },
    { id: "trading", label: "Trading", content: <p>Trading panel</p> },
  ];

  it("selects with arrow keys, Home and End, and keeps one tab in the tab order", async () => {
    render(<Tabs label="Spaces" items={items} />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs.map((t) => t.getAttribute("tabindex"))).toEqual(["0", "-1", "-1"]);
    tabs[0].focus();
    await userEvent.keyboard("{ArrowRight}");
    expect(document.activeElement).toBe(tabs[1]);
    expect(tabs[1].getAttribute("aria-selected")).toBe("true");
    expect(screen.getByRole("tabpanel").textContent).toBe("Money panel");
    await userEvent.keyboard("{End}");
    expect(tabs[2].getAttribute("aria-selected")).toBe("true");
    await userEvent.keyboard("{ArrowRight}");
    expect(tabs[0].getAttribute("aria-selected")).toBe("true");
    await userEvent.keyboard("{ArrowLeft}");
    expect(tabs[2].getAttribute("aria-selected")).toBe("true");
    await userEvent.keyboard("{Home}");
    expect(tabs[0].getAttribute("aria-selected")).toBe("true");
  });

  it("links each tab to its panel", () => {
    render(<Tabs label="Spaces" items={items} defaultValue="money" />);
    const selected = screen.getByRole("tab", { selected: true });
    const panel = screen.getByRole("tabpanel");
    expect(panel.getAttribute("aria-labelledby")).toBe(selected.id);
    expect(selected.getAttribute("aria-controls")).toBe(panel.id);
  });
});

describe("Dialog and Sheet", () => {
  function Harness({ kind }: { kind: "dialog" | "sheet" }) {
    const [open, setOpen] = useState(false);
    const Overlay = kind === "dialog" ? Dialog : Sheet;
    return (
      <>
        <Button onClick={() => setOpen(true)}>Open</Button>
        <Overlay
          open={open}
          onClose={() => setOpen(false)}
          title="Transfer details"
          description="Booked on 3 November"
          footer={<Button variant="primary">Confirm</Button>}
        >
          <Input label="Reference" />
        </Overlay>
      </>
    );
  }

  it.each(["dialog", "sheet"] as const)("%s opens labelled, focuses inside, closes on Escape and restores focus", async (kind) => {
    render(<Harness kind={kind} />);
    const trigger = screen.getByRole("button", { name: "Open" });
    await userEvent.click(trigger);
    const dialog = screen.getByRole("dialog", { name: "Transfer details" });
    expect(dialog.hasAttribute("open")).toBe(true);
    expect(dialog.getAttribute("aria-describedby")).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByLabelText("Reference"));

    // A native dialog fires "cancel" on Escape.
    act(() => {
      dialog.dispatchEvent(new Event("cancel", { cancelable: true }));
    });
    expect(dialog.hasAttribute("open")).toBe(false);
    expect(document.activeElement).toBe(trigger);
  });

  it("closes with the close button and on a backdrop click", async () => {
    render(<Harness kind="dialog" />);
    await userEvent.click(screen.getByRole("button", { name: "Open" }));
    await userEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.getByRole("dialog", { hidden: true }).hasAttribute("open")).toBe(false);

    await userEvent.click(screen.getByRole("button", { name: "Open" }));
    const dialog = screen.getByRole("dialog");
    fireEvent.click(dialog);
    expect(dialog.hasAttribute("open")).toBe(false);
  });
});

describe("Toast", () => {
  function Trigger({ tone }: { tone?: "danger" | "success" }) {
    const { toast } = useToast();
    return <Button onClick={() => toast({ title: "Payment saved", description: "Rent, 950 EUR", tone })}>Notify</Button>;
  }

  it("announces in the polite region and dismisses on its own", () => {
    vi.useFakeTimers();
    try {
      render(
        <ToastProvider>
          <Trigger tone="success" />
        </ToastProvider>,
      );
      fireEvent.click(screen.getByRole("button", { name: "Notify" }));
      const status = screen.getByRole("status");
      expect(within(status).getByText("Payment saved")).toBeTruthy();
      act(() => {
        vi.advanceTimersByTime(6100);
      });
      expect(within(status).queryByText("Payment saved")).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it("puts danger in the assertive region and keeps it until dismissed", async () => {
    render(
      <ToastProvider>
        <Trigger tone="danger" />
      </ToastProvider>,
    );
    await userEvent.click(screen.getByRole("button", { name: "Notify" }));
    const alert = screen.getByRole("alert");
    expect(within(alert).getByText("Payment saved")).toBeTruthy();
    await userEvent.click(within(alert).getByRole("button", { name: "Dismiss notification" }));
    expect(within(alert).queryByText("Payment saved")).toBeNull();
  });

  it("throws a clear error outside the provider", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    expect(() => render(<Trigger />)).toThrow(/ToastProvider/);
    spy.mockRestore();
  });
});

describe("AppShell", () => {
  it("has a skip link to main, one nav landmark and aria-current on the active space", async () => {
    const onNavigate = vi.fn();
    render(
      <AppShell
        brand="FinHub"
        title="Today"
        onNavigate={onNavigate}
        nav={[
          { id: "today", label: "Today", current: true },
          { id: "money", label: "Money" },
          { id: "trading", label: "Trading", href: "#trading" },
        ]}
      >
        <p>Content</p>
      </AppShell>,
    );
    const skip = screen.getByRole("link", { name: "Skip to content" });
    expect(skip.getAttribute("href")).toBe("#nx-main");
    expect(screen.getByRole("main").id).toBe("nx-main");
    expect(screen.getAllByRole("navigation")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Today" }).getAttribute("aria-current")).toBe("page");
    await userEvent.click(screen.getByRole("button", { name: "Money" }));
    expect(onNavigate).toHaveBeenCalledWith("money");
    expect(screen.getByRole("link", { name: "Trading" }).getAttribute("href")).toBe("#trading");
  });
});

describe("Table", () => {
  type Row = { id: string; payee: string; amount: string };
  const rows: Row[] = [
    { id: "1", payee: "Landlord", amount: "950.00" },
    { id: "2", payee: "Grocer", amount: "84.20" },
  ];
  const columns = [
    { key: "payee", header: "Payee", rowHeader: true },
    { key: "amount", header: "Amount", numeric: true },
  ];

  it("is a labelled, focusable region with a caption and right aligned numbers", () => {
    render(<Table caption="November payments" columns={columns} rows={rows} getRowKey={(r) => r.id} />);
    const region = screen.getByRole("region", { name: "November payments" });
    expect(region.getAttribute("tabindex")).toBe("0");
    const table = within(region).getByRole("table", { name: "November payments" });
    expect(within(table).getAllByRole("columnheader")[1].className).toContain("nx-table__cell--numeric");
    expect(within(table).getByRole("rowheader", { name: "Landlord" })).toBeTruthy();
    expect(within(table).getByText("84.20").className).toContain("nx-table__cell--numeric");
  });

  it("shows skeleton rows while loading and the empty state without rows", () => {
    const { rerender } = render(<Table caption="Payments" columns={columns} rows={[] as Row[]} getRowKey={(r) => r.id} loading />);
    expect(screen.getByRole("status").textContent).toContain("Loading Payments");
    rerender(<Table caption="Payments" columns={columns} rows={[] as Row[]} getRowKey={(r) => r.id} empty="No payments this month." />);
    expect(screen.getByText("No payments this month.")).toBeTruthy();
  });

  it("activates rows from the keyboard through the first cell button", async () => {
    const onRowClick = vi.fn();
    render(<Table caption="Payments" columns={columns} rows={rows} getRowKey={(r) => r.id} onRowClick={onRowClick} />);
    screen.getByRole("button", { name: "Grocer" }).focus();
    await userEvent.keyboard("{Enter}");
    expect(onRowClick).toHaveBeenCalledWith(rows[1]);
  });
});

describe("LineChart", () => {
  const data = [
    { label: "1 Nov", value: 2400 },
    { label: "15 Nov", value: 1800 },
    { label: "30 Nov", value: 1200 },
  ];

  it("is an image with a summary, a labelled floor line and a data table", () => {
    render(<LineChart title="Balance" data={data} floor={{ value: 1000, label: "Floor 1,000 EUR" }} />);
    const img = screen.getByRole("img");
    expect(img.getAttribute("aria-label")).toContain("Balance: 3 points from 1 Nov to 30 Nov");
    expect(img.getAttribute("aria-label")).toContain("floor Floor 1,000 EUR");
    expect(img.querySelector(".nx-chart__floor")).not.toBeNull();
    expect(screen.getAllByText("Floor 1,000 EUR").length).toBeGreaterThanOrEqual(2);
    const table = screen.getByRole("table", { name: "Balance" });
    expect(within(table).getAllByRole("row")).toHaveLength(4);
    expect(img.querySelector("polyline")?.getAttribute("points")?.split(" ")).toHaveLength(3);
  });

  it("handles a single point and no data", () => {
    const { rerender } = render(<LineChart title="Balance" data={[data[0]]} />);
    expect(document.querySelector(".nx-chart__dot")).not.toBeNull();
    rerender(<LineChart title="Balance" data={[]} />);
    expect(screen.getByRole("img").getAttribute("aria-label")).toBe("Balance: no data");
  });
});

describe("display components", () => {
  it("renders Card heading level, Badge tone, Stat as a description list", () => {
    render(
      <Card title="Cash" description="All accounts" headingLevel={3} accent="accent1">
        <Stat label="Available" value="2,410.55 EUR" hint="Today" status={{ tone: "success", label: "Above floor" }} />
        <Badge tone="warning">Due soon</Badge>
      </Card>,
    );
    expect(screen.getByRole("heading", { level: 3, name: "Cash" })).toBeTruthy();
    expect(screen.getByRole("term").textContent).toBe("Available");
    expect(screen.getByRole("definition").textContent).toBe("2,410.55 EUR");
    expect(screen.getByText("Due soon").className).toContain("nx-badge--warning");
  });

  it("EmptyState offers an action, ErrorState announces and retries", async () => {
    const onRetry = vi.fn();
    render(
      <>
        <EmptyState title="No payments yet" action={<Button>Add payment</Button>} />
        <ErrorState description="The server did not answer." onRetry={onRetry} />
        <SkeletonRows rows={2} />
      </>,
    );
    expect(screen.getByRole("button", { name: "Add payment" })).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("This could not be loaded");
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
