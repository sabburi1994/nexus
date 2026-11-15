import React, { useEffect, useId, useRef, useState } from "react";

import { cx } from "../utils.js";

export interface ChartPoint {
  /** X axis label (for example a date). */
  label: string;
  value: number;
}

export interface LineChartProps {
  /** Short name of what is plotted; becomes the accessible name. */
  title: string;
  data: ChartPoint[];
  /** Optional second series on the same x labels (same length as data). */
  compare?: { name: string; data: ChartPoint[] };
  seriesName?: string;
  /** Labelled horizontal floor line, for example a minimum balance. */
  floor?: { value: number; label: string };
  /** Formats y values for axis labels and the data table. */
  formatValue?: (value: number) => string;
  /** Height in px (default 200). Width follows the container. */
  height?: number;
  /** Visually hidden data table for screen readers (default true). */
  dataTable?: boolean;
  className?: string;
}

const PAD = { top: 16, right: 12, bottom: 28, left: 56 };

/** Round step (1, 2, 2.5 or 5 times a power of ten) at least ``raw``. */
function niceStep(raw: number): number {
  if (!(raw > 0) || !Number.isFinite(raw)) return 1;
  const power = 10 ** Math.floor(Math.log10(raw));
  const fraction = raw / power;
  const nice = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 2.5 ? 2.5 : fraction <= 5 ? 5 : 10;
  return nice * power;
}

/** Axis range on round values with the data inside: two equal steps, so min, middle and max are round. */
export function niceRange(values: number[]): [number, number] {
  if (values.length === 0) return [0, 1];
  let lo = Math.min(...values);
  let hi = Math.max(...values);
  if (lo === hi) {
    lo -= Math.abs(lo) * 0.1 || 1;
    hi += Math.abs(hi) * 0.1 || 1;
  }
  let step = niceStep((hi - lo) / 2);
  for (let i = 0; i < 6; i++) {
    const start = Math.floor(lo / step) * step;
    if (start + 2 * step >= hi) return [start, start + 2 * step];
    step = niceStep(step * 1.01);
  }
  const start = Math.floor(lo / step) * step;
  return [start, start + 2 * step];
}

function useContainerWidth(fallback: number) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver((entries) => {
      const w = Math.round(entries[0]?.contentRect.width ?? 0);
      if (w > 0) setWidth(w);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

/**
 * Thin line chart: one or two series, an optional labelled floor line, min, middle and max y
 * labels, first and last x labels. Pure SVG styled through classes (no inline styles), scaled
 * to the container width so text stays readable on phones.
 */
export function LineChart({
  title,
  data,
  compare,
  seriesName = "Value",
  floor,
  formatValue = (v) => v.toLocaleString(),
  height = 200,
  dataTable = true,
  className,
}: LineChartProps) {
  const [ref, width] = useContainerWidth(600);
  const descId = `nx-chart-${useId().replace(/:/g, "")}`;

  const values = [...data.map((d) => d.value), ...(compare?.data.map((d) => d.value) ?? [])];
  if (floor) values.push(floor.value);
  const [min, max] = niceRange(values);

  const innerW = Math.max(width - PAD.left - PAD.right, 10);
  const innerH = Math.max(height - PAD.top - PAD.bottom, 10);
  const x = (i: number, n: number) => PAD.left + (n <= 1 ? innerW / 2 : (i / (n - 1)) * innerW);
  const y = (v: number) => PAD.top + (1 - (v - min) / (max - min)) * innerH;
  const points = (series: ChartPoint[]) => series.map((d, i) => `${x(i, series.length).toFixed(1)},${y(d.value).toFixed(1)}`).join(" ");

  const ticks = [max, (max + min) / 2, min];
  const last = data[data.length - 1];
  const summary =
    data.length > 0
      ? `${title}: ${data.length} points from ${data[0].label} to ${last.label}, latest ${formatValue(last.value)}` +
        (floor ? `, floor ${floor.label} at ${formatValue(floor.value)}` : "")
      : `${title}: no data`;

  return (
    <figure className={cx("nx-chart", className)}>
      <div ref={ref} className="nx-chart__frame">
        <svg
          role="img"
          aria-label={summary}
          aria-describedby={dataTable ? descId : undefined}
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          className="nx-chart__svg"
          focusable="false"
        >
          {ticks.map((t, i) => (
            <g key={i}>
              <line className="nx-chart__grid" x1={PAD.left} x2={width - PAD.right} y1={y(t)} y2={y(t)} />
              <text className="nx-chart__axis-label" x={PAD.left - 8} y={y(t)} textAnchor="end" dominantBaseline="middle">
                {formatValue(t)}
              </text>
            </g>
          ))}
          {data.length > 0 ? (
            <>
              <text className="nx-chart__axis-label" x={x(0, data.length)} y={height - 8} textAnchor="start">
                {data[0].label}
              </text>
              {data.length > 1 ? (
                <text className="nx-chart__axis-label" x={x(data.length - 1, data.length)} y={height - 8} textAnchor="end">
                  {last.label}
                </text>
              ) : null}
            </>
          ) : null}
          {floor ? (
            <g className="nx-chart__floor-group">
              <line className="nx-chart__floor" x1={PAD.left} x2={width - PAD.right} y1={y(floor.value)} y2={y(floor.value)} />
              <text className="nx-chart__floor-label" x={width - PAD.right} y={y(floor.value) - 6} textAnchor="end">
                {floor.label}
              </text>
            </g>
          ) : null}
          {compare && compare.data.length > 1 ? (
            <polyline className="nx-chart__line nx-chart__line--alt" points={points(compare.data)} vectorEffect="non-scaling-stroke" />
          ) : null}
          {data.length > 1 ? <polyline className="nx-chart__line" points={points(data)} vectorEffect="non-scaling-stroke" /> : null}
          {data.length === 1 ? <circle className="nx-chart__dot" cx={x(0, 1)} cy={y(data[0].value)} r={3} /> : null}
        </svg>
      </div>
      <figcaption className="nx-chart__caption">
        <span className="nx-chart__legend">
          <span className="nx-chart__swatch" aria-hidden="true" />
          {seriesName}
        </span>
        {compare ? (
          <span className="nx-chart__legend">
            <span className="nx-chart__swatch nx-chart__swatch--alt" aria-hidden="true" />
            {compare.name}
          </span>
        ) : null}
        {floor ? (
          <span className="nx-chart__legend">
            <span className="nx-chart__swatch nx-chart__swatch--floor" aria-hidden="true" />
            {floor.label}
          </span>
        ) : null}
      </figcaption>
      {dataTable ? (
        // The clip goes on a wrapping div: a <table> cannot shrink to 1 px, so a visually hidden
        // table still widens the page (428 px at a 390 px viewport before 1.0.1).
        <div className="nx-visually-hidden nx-chart__data">
          <table id={descId}>
            <caption>{title}</caption>
          <thead>
            <tr>
              <th scope="col">Label</th>
              <th scope="col">{seriesName}</th>
              {compare ? <th scope="col">{compare.name}</th> : null}
            </tr>
          </thead>
          <tbody>
            {data.map((d, i) => (
              <tr key={`${d.label}-${i}`}>
                <th scope="row">{d.label}</th>
                <td>{formatValue(d.value)}</td>
                {compare ? <td>{compare.data[i] ? formatValue(compare.data[i].value) : ""}</td> : null}
              </tr>
            ))}
          </tbody>
          </table>
        </div>
      ) : null}
    </figure>
  );
}
