import tableStyles from "./BaseTable.module.css";
import Filter from "./BaseTableFilter";
import {
  ColumnDef,
  Header,
  HeaderGroup,
  InitialTableState,
  Table as ReactTable,
  RowSelectionState,
  flexRender,
  getCoreRowModel,
  getFacetedMinMaxValues,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { stringify } from "csv-stringify/browser/esm/sync";
import { ReactNode, useEffect, useRef } from "react";
import {
  Button,
  ButtonGroup,
  ButtonToolbar,
  Col,
  Form,
  OverlayTrigger,
  Row,
  Tooltip,
} from "react-bootstrap";
import { useLocation } from "react-router-dom";

function TableTooltip(message: string) {
  return <Tooltip id="table_tooltip">{message}</Tooltip>;
}

// exports what the user is looking at: every page, but only rows that pass the current filters
const exportToCSV = (table: ReactTable<any>, exportFileName: string) => {
  const { rows } = table.getFilteredRowModel();

  const headerRows = table.getHeaderGroups().map((headerGroup: HeaderGroup<any>) =>
    headerGroup.headers.map((header: Header<any, any>) => {
      // a rendered header can't go in a csv, fall back to the column's key
      if (typeof header.column.columnDef.header === "function") {
        return (header.column.columnDef as { accessorKey?: string }).accessorKey;
      }
      return header.column.columnDef.header;
    })
  );
  const csvData = rows.map((row) => row.getVisibleCells().map((cell) => cell.getValue()));

  const csv = stringify([...headerRows, ...csvData]);
  const blob = new Blob([csv], { type: "text/csv;charset=utf8;" });
  const link = document.createElement("a");
  link.download = exportFileName;
  link.href = URL.createObjectURL(blob);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// opt in to tick boxes on rows; the page owns the selection so it can act on it and clear it
export interface TableSelection {
  getRowId: (row: any) => string;
  selected: RowSelectionState;
  onChange: (selected: RowSelectionState) => void;
  canSelect?: (row: any) => boolean;
  // bulk action buttons, shown while something is selected
  actions?: (rows: Array<any>) => ReactNode;
}

const TickBox = ({
  checked,
  indeterminate = false,
  disabled = false,
  onChange,
  label,
}: {
  checked: boolean;
  indeterminate?: boolean;
  disabled?: boolean;
  onChange: (e: any) => void;
  label: string;
}) => {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = indeterminate && !checked;
  }, [indeterminate, checked]);
  return (
    <Form.Check
      ref={ref}
      aria-label={label}
      checked={checked}
      disabled={disabled}
      onChange={onChange}
    />
  );
};

// the tick box sits right of the grid row so pages keep their 12 column layouts
const SELECT_WIDTH = "2rem";

export interface BaseTableProps extends Partial<HTMLElement> {
  isLoading?: boolean;
  isFetching?: boolean;
  debugTable?: boolean;
  striped?: boolean;
  data?: any;
  error?: boolean;
  hover?: boolean;
  columns: ColumnDef<any, any>[];
  asyncExpandFunction?: any;
  initialState?: InitialTableState;
  exportFileName?: string;
  selection?: TableSelection;
}

interface _BaseTableProps extends BaseTableProps {
  table: ReactTable<any>;
}

const BaseTable = ({
  isFetching = false,
  debugTable = false,
  data = [],
  columns,
  initialState = undefined,
  exportFileName = undefined,
  selection = undefined,
}: BaseTableProps) => {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
    debugTable,
    // merge so a page that only sets sorting still gets the default page size
    initialState: {
      ...initialState,
      pagination: { pageSize: 15, ...initialState?.pagination },
    },
    ...(selection && {
      getRowId: selection.getRowId,
      enableRowSelection: (row: any) =>
        selection.canSelect ? selection.canSelect(row.original) : true,
      state: { rowSelection: selection.selected },
      onRowSelectionChange: (updater: any) =>
        selection.onChange(typeof updater === "function" ? updater(selection.selected) : updater),
    }),
  });

  return (
    <_baseTable
      {...{ table, data, columns, isFetching, debugTable, initialState, exportFileName, selection }}
    />
  );
};

function _baseTable({
  table,
  isFetching = false,
  debugTable = false,
  exportFileName = undefined,
  data = [],
  selection = undefined,
}: _BaseTableProps) {
  const { rows } = table.getRowModel();
  // ids left over from rows that have since gone (e.g. after a refresh) don't count
  const selectedRows: Array<any> = selection
    ? data.filter((row: any) => selection.selected[selection.getRowId(row)])
    : [];
  const location = useLocation();
  const fileName = exportFileName ?? `ExportedData_${location.pathname}`;
  const pageSize = table.getState().pagination.pageSize;

  return (
    <>
      {/* Header */}
      {selection && selectedRows.length > 0 && (
        <div className="d-flex flex-wrap align-items-center gap-2 mb-2 p-2 border rounded bg-body-tertiary">
          <strong>{selectedRows.length} selected</strong>
          <Button size="sm" variant="link" className="p-0" onClick={() => selection.onChange({})}>
            Clear
          </Button>
          <div className="ms-auto d-flex gap-2">{selection.actions?.(selectedRows)}</div>
        </div>
      )}
      {table.getHeaderGroups().map((headerGroup: HeaderGroup<any>) => (
        <div key={headerGroup.id} className="d-flex align-items-end border-bottom pb-2 mb-1">
          <Row className={`flex-grow-1 fw-semibold align-items-end ${selection ? "me-0" : ""}`}>
            {headerGroup.headers.map((header: Header<any, any> | any) => (
              <Col
                key={header.id}
                className={`col-12 ${header.column.columnDef.width ?? "col-xl"}`}
              >
                {header.isPlaceholder ? null : (
                  <>
                    <div
                      className={`d-flex align-items-center gap-1 ${
                        header.column.getCanSort() ? `${tableStyles.sortable} user-select-none` : ""
                      }`}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      {header.column.getCanSort() && (
                        <i
                          className={`fas fa-fw ${
                            header.column.getIsSorted() === "asc"
                              ? "fa-sort-down"
                              : header.column.getIsSorted() === "desc"
                              ? "fa-sort-up"
                              : "fa-sort text-muted"
                          }`}
                        />
                      )}
                      {flexRender(header.column.columnDef.header, header.getContext())}
                    </div>
                    {header.column.getCanFilter() && (
                      <Filter column={header.column} table={table} />
                    )}
                  </>
                )}
              </Col>
            ))}
          </Row>
          {selection && (
            <div style={{ width: SELECT_WIDTH, flexShrink: 0 }}>
              <TickBox
                label="Select all matching rows"
                checked={table.getIsAllRowsSelected()}
                indeterminate={table.getIsSomeRowsSelected()}
                onChange={table.getToggleAllRowsSelectedHandler()}
              />
            </div>
          )}
        </div>
      ))}

      {/* Data rows */}
      {rows.map((row) => (
        <div
          key={row.id}
          className={`d-flex align-items-center border-top ${tableStyles.tableRow}`}
        >
          <Row className={`flex-grow-1 py-2 align-items-center ${selection ? "me-0" : ""}`}>
            {row.getVisibleCells().map((cell: any) => (
              <Col key={cell.id} className={`col-12 ${cell.column.columnDef.width ?? "col-xl"}`}>
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </Col>
            ))}
          </Row>
          {selection && (
            <div style={{ width: SELECT_WIDTH, flexShrink: 0 }}>
              {row.getCanSelect() && (
                <TickBox
                  label="Select row"
                  checked={row.getIsSelected()}
                  onChange={row.getToggleSelectedHandler()}
                />
              )}
            </div>
          )}
        </div>
      ))}

      {/* Empty state */}
      {rows.length === 0 && !isFetching && (
        <div className="text-center py-5 text-muted">
          <i className="fas fa-inbox fa-2x d-block mb-2" />
          No data available.
        </div>
      )}

      {/* Footer */}
      <div className="d-flex justify-content-between align-items-center mt-3 pt-2 border-top flex-wrap gap-2">
        <ButtonGroup size="sm">
          <Button variant="outline-secondary" disabled>
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount() || 1}
          </Button>
          <OverlayTrigger
            placement="top"
            trigger={["hover", "focus"]}
            overlay={TableTooltip(isFetching ? "Refreshing data…" : "Data up to date")}
          >
            <Button variant="outline-secondary">
              <i
                className={
                  isFetching ? `${tableStyles.refreshAnimate} fas fa-sync` : "far fa-check-circle"
                }
              />
            </Button>
          </OverlayTrigger>
          <Button variant="outline-primary" onClick={() => exportToCSV(table, fileName)}>
            <i className="fas fa-download me-1" />
            Export CSV
          </Button>
        </ButtonGroup>

        <ButtonToolbar>
          <ButtonGroup size="sm">
            <Button
              variant="outline-success"
              onClick={() => table.setPageIndex(0)}
              disabled={!table.getCanPreviousPage()}
            >
              <i className="fas fa-angle-double-left" />
            </Button>
            <Button
              variant="outline-success"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              <i className="fas fa-caret-left" />
            </Button>
            <Button
              variant="outline-success"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              <i className="fas fa-caret-right" />
            </Button>
            <Button
              variant="outline-success"
              onClick={() => table.setPageIndex(table.getPageCount() - 1)}
              disabled={!table.getCanNextPage()}
            >
              <i className="fas fa-angle-double-right" />
            </Button>
          </ButtonGroup>

          <Form.Select
            size="sm"
            className="ms-2"
            style={{ width: "auto" }}
            aria-label="Page size"
            value={pageSize}
            onChange={(e) => table.setPageSize(Number(e.target.value))}
          >
            {[15, 30, 60, 100, 1_000_000].map((_pageSize) => (
              <option key={_pageSize} value={_pageSize}>
                {_pageSize === 1_000_000 ? "Show all" : `Show ${_pageSize}`}
              </option>
            ))}
          </Form.Select>
        </ButtonToolbar>
      </div>

      {debugTable && (
        <div className="mt-2">
          <div>{table.getRowModel().rows.length} Rows</div>
          <pre>{JSON.stringify(table.getState(), null, 2)}</pre>
        </div>
      )}
    </>
  );
}

export default BaseTable;
