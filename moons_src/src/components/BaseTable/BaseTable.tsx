import tableStyles from "./BaseTable.module.css";
import Filter from "./BaseTableFilter";
import {
  ColumnDef,
  Header,
  HeaderGroup,
  PaginationInitialTableState,
  Table as ReactTable,
  SortingTableState,
  VisibilityTableState,
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
import {
  Button,
  ButtonGroup,
  ButtonToolbar,
  Col,
  Dropdown,
  OverlayTrigger,
  Row,
  SplitButton,
  Tooltip,
} from "react-bootstrap";
import { useLocation } from "react-router-dom";

function TableTooltip(message: string) {
  return <Tooltip id="table_tooltip">{message}</Tooltip>;
}

const exportToCSV = (table: ReactTable<any>, exportFileName: string) => {
  const { rows } = table.getCoreRowModel();

  const headerRows = table
    .getHeaderGroups()
    .map((headerGroup: HeaderGroup<any>) =>
      headerGroup.headers.map((header: Header<any, any>) => header.column.columnDef.header)
    );
  const csvData = rows.map((row: any) => row.getVisibleCells().map((cell: any) => cell.getValue()));

  const csv = stringify([...headerRows, ...csvData]);
  const blob = new Blob([csv], { type: "text/csv;charset=utf8;" });
  const link = document.createElement("a");
  link.download = exportFileName;
  link.href = URL.createObjectURL(blob);
  link.setAttribute("visibility", "hidden");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

type tableInitialState = SortingTableState | VisibilityTableState | PaginationInitialTableState;

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
  initialState?: tableInitialState;
  exportFileName?: string;
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
}: BaseTableProps) => {
  const initState: tableInitialState = initialState ?? { pagination: { pageSize: 15 } };

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
    initialState: initState,
  });

  return (
    <_baseTable
      {...{ table, data, columns, isFetching, debugTable, initialState, exportFileName }}
    />
  );
};

function _baseTable({
  table,
  isFetching = false,
  debugTable = false,
  exportFileName = undefined,
}: _BaseTableProps) {
  const { rows } = table.getRowModel();
  const location = useLocation();
  const fileName = exportFileName ?? `ExportedData_${location.pathname}`;
  const pageSize = table.getState().pagination.pageSize;

  return (
    <>
      {/* Header */}
      {table.getHeaderGroups().map((headerGroup: HeaderGroup<any>) => (
        <Row key={headerGroup.id} className="pb-2 mb-1 border-bottom fw-semibold align-items-end">
          {headerGroup.headers.map((header: Header<any, any> | any) => (
            <Col key={header.id} className={`col-12 ${header.column.columnDef.width ?? "col-xl"}`}>
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
                  {header.column.getCanFilter() && <Filter column={header.column} table={table} />}
                </>
              )}
            </Col>
          ))}
        </Row>
      ))}

      {/* Data rows */}
      {rows.map((row) => (
        <Row key={row.id} className={`py-2 border-top align-items-center ${tableStyles.tableRow}`}>
          {row.getVisibleCells().map((cell: any) => (
            <Col key={cell.id} className={`col-12 ${cell.column.columnDef.width ?? "col-xl"}`}>
              {flexRender(cell.column.columnDef.cell, cell.getContext())}
            </Col>
          ))}
        </Row>
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

          <ButtonGroup size="sm" className="ms-2">
            <SplitButton
              id="pageSizeDropdown"
              variant="outline-success"
              title={pageSize === 1_000_000 ? "All rows" : `${pageSize} rows`}
            >
              {[15, 30, 60, 100, 1_000_000].map((_pageSize) => (
                <Dropdown.Item key={_pageSize} onClick={() => table.setPageSize(_pageSize)}>
                  {_pageSize === 1_000_000 ? "Show all" : `Show ${_pageSize}`}
                </Dropdown.Item>
              ))}
            </SplitButton>
          </ButtonGroup>
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
