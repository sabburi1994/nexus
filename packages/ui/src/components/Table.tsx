import React from "react";

import { cx } from "../utils.js";
import { SkeletonRows } from "./Display.js";

export interface TableColumn<Row> {
  /** Stable key; also the default cell value (row[key]). */
  key: string;
  header: React.ReactNode;
  /** Numbers: right aligned with tabular figures. */
  numeric?: boolean;
  /** Custom cell content. */
  render?: (row: Row) => React.ReactNode;
  /** Hide this column below the md breakpoint (keep the essential ones visible on phones). */
  hideOnMobile?: boolean;
  /** Header cell scope is "col"; set true for the column that names each row (rendered as th scope="row"). */
  rowHeader?: boolean;
}

export interface TableProps<Row> {
  columns: TableColumn<Row>[];
  rows: Row[];
  getRowKey: (row: Row, index: number) => string;
  /** Describes the table; required for screen readers. Set hideCaption to keep it off screen. */
  caption: string;
  hideCaption?: boolean;
  /** Header stays visible while the table scrolls inside its region (default true). */
  stickyHeader?: boolean;
  dense?: boolean;
  loading?: boolean;
  /** Shown in a single full width row when there are no rows. */
  empty?: React.ReactNode;
  onRowClick?: (row: Row) => void;
  className?: string;
  /** Totals or summary row content keyed by column key. */
  footer?: Partial<Record<string, React.ReactNode>>;
}

function cellValue<Row>(row: Row, column: TableColumn<Row>): React.ReactNode {
  if (column.render) return column.render(row);
  const value = (row as Record<string, unknown>)[column.key];
  return value === null || value === undefined ? "" : String(value);
}

/**
 * Data table: a focusable, horizontally scrollable region on small screens, sticky header,
 * right aligned tabular numbers. Rows with onRowClick are activated by click or by Enter on
 * the row's first cell button.
 */
export function Table<Row>({
  columns,
  rows,
  getRowKey,
  caption,
  hideCaption = false,
  stickyHeader = true,
  dense = false,
  loading = false,
  empty,
  onRowClick,
  className,
  footer,
}: TableProps<Row>) {
  const colClass = (c: TableColumn<Row>) => cx(c.numeric && "nx-table__cell--numeric", c.hideOnMobile && "nx-table__cell--wide-only");
  return (
    <div
      className={cx("nx-table-region", className)}
      role="region"
      aria-label={caption}
      // Focusable so keyboard users can scroll a wide table.
      tabIndex={0}
    >
      <table className={cx("nx-table", stickyHeader && "nx-table--sticky", dense && "nx-table--dense")}>
        <caption className={cx("nx-table__caption", hideCaption && "nx-visually-hidden")}>{caption}</caption>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} scope="col" className={colClass(c)}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody aria-busy={loading || undefined}>
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="nx-table__loading">
                <SkeletonRows rows={3} columns={Math.min(columns.length, 4)} label={`Loading ${caption}`} />
              </td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="nx-table__empty">
                {empty ?? "No rows to show."}
              </td>
            </tr>
          ) : (
            rows.map((row, index) => (
              <tr
                key={getRowKey(row, index)}
                className={cx(onRowClick && "nx-table__row--interactive")}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((c, ci) => {
                  const content = cellValue(row, c);
                  const inner =
                    onRowClick && ci === 0 ? (
                      <button
                        type="button"
                        className="nx-table__row-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onRowClick(row);
                        }}
                      >
                        {content}
                      </button>
                    ) : (
                      content
                    );
                  return c.rowHeader ? (
                    <th key={c.key} scope="row" className={colClass(c)}>
                      {inner}
                    </th>
                  ) : (
                    <td key={c.key} className={colClass(c)}>
                      {inner}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
        {footer && !loading && rows.length > 0 ? (
          <tfoot>
            <tr>
              {columns.map((c) => (
                <td key={c.key} className={colClass(c)}>
                  {footer[c.key] ?? ""}
                </td>
              ))}
            </tr>
          </tfoot>
        ) : null}
      </table>
    </div>
  );
}
