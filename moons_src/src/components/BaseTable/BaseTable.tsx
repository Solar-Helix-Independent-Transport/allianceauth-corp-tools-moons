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

function MyTooltip(message: string) {
  return <Tooltip id="character_tooltip">{message}</Tooltip>;
}

const exportToCSV = (table: ReactTable<any>, exportFileName: string) => {
  const { rows } = table.getCoreRowModel();

  const headerRows = table.getHeaderGroups().map((headerGroup: HeaderGroup<any>) => {
    return headerGroup.headers.map((header: Header<any, any>) => {
      return header.column.columnDef.header;
    });
  });

  const csvData = rows.map((row: any) => {
    return row.getVisibleCells().map((cell: any) => {
      return cell.getValue();
    });
  });
  console.log(headerRows, csvData);
  const csv = stringify([...headerRows, ...csvData]);
  const fileType = "csv";
  const blob = new Blob([csv], {
    type: `text/${fileType};charset=utf8;`,
  });

  // spoof a download
  const link = document.createElement("a");
  link.download = exportFileName;
  link.href = URL.createObjectURL(blob);

  // Ensure the link isn't visible to the user or cause layout shifts.
  link.setAttribute("visibility", "hidden");

  // Add to document body, click and remove it.
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// function strToKey(keyString: string, ob: object) {
//   return keyString.split(".").reduce(function (p: any, prop: any) {
//     return p[prop];
//   }, ob);
// }

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
  // isLoading = false,
  isFetching = false,
  debugTable = false,
  data = [],
  // error = false,
  columns,
  // asyncExpandFunction = undefined,
  striped = false,
  hover = false,
  initialState = undefined,
  exportFileName = undefined,
}: BaseTableProps) => {
  let initState: tableInitialState = {
    pagination: {
      pageSize: 15, //custom default page size
    },
  };
  if (initialState !== undefined) {
    initState = initialState;
  }
  const table = useReactTable({
    data,
    columns,
    // Pipeline
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    getFacetedMinMaxValues: getFacetedMinMaxValues(),
    //
    debugTable: debugTable,
    // state: initialState,
    initialState: initState,
  });

  return (
    <_baseTable
      {...{
        table,
        data,
        columns,
        isFetching,
        debugTable,
        initialState,
        striped,
        hover,
        exportFileName,
      }}
    />
  );
};

function _baseTable({
  table,
  isFetching = false,
  striped = false,
  hover = false,
  debugTable = false,
  exportFileName = undefined,
}: _BaseTableProps) {
  const { rows } = table.getRowModel();
  const location = useLocation();
  const fileName =
    typeof exportFileName !== "undefined" ? exportFileName : `ExportedData_${location.pathname}`;
  return (
    <>
      <div {...{ striped, hover }}>
        <Col className="">
          {table.getHeaderGroups().map((headerGroup: HeaderGroup<any>) => (
            <>
              <Row key={`name-${headerGroup.id}`}>
                {headerGroup.headers.map((header: Header<any, any> | any) => {
                  return (
                    <Col
                      key={header.id}
                      xs={12}
                      className={`col-sm-12 col-md-12 col-lg-12 col-xl mt-4 ${header.column.columnDef.width}`}
                    >
                      {header.isPlaceholder ? null : (
                        <Row
                          {...{
                            className: header.column.getCanSort()
                              ? "d-dlex cursor-pointer select-none"
                              : "d-flex",
                          }}
                        >
                          <Row {...{ onClick: header.column.getToggleSortingHandler() }}>
                            <div className="d-flex">
                              {header.column.getCanSort() ? (
                                <div>
                                  {{
                                    asc: <i className="fas fa-sort-down fa-fw"></i>,
                                    desc: <i className="fas fa-sort-up fa-fw"></i>,
                                  }[header.column.getIsSorted() as string] ?? (
                                    <i className="fas fa-sort fa-fw"></i>
                                  )}
                                </div>
                              ) : null}
                              {flexRender(header.column.columnDef.header, header.getContext())}
                            </div>
                          </Row>
                          <Row>
                            {header.column.getCanFilter() && rows.length >= 0 ? (
                              <Filter column={header.column} table={table} />
                            ) : (
                              <></>
                            )}
                          </Row>
                        </Row>
                      )}
                    </Col>
                  );
                })}
              </Row>
              <hr />
            </>
          ))}
        </Col>
        <Col>
          {rows.map((row) => {
            return (
              <>
                <Row key={row.id} className="">
                  {row.getVisibleCells().map((cell: any) => {
                    return (
                      <Col
                        key={cell.id}
                        xs={12}
                        className={`col-sm-12 col-md-12 col-lg-12 col-xl mt-2 ${cell.column.columnDef.width}`}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </Col>
                    );
                  })}
                </Row>
                <hr />
              </>
            );
          })}
        </Col>
      </div>
      <div className="d-flex justify-content-between">
        <ButtonGroup>
          <Button active variant="info">
            {
              <>
                {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
              </>
            }
          </Button>
          {isFetching ? (
            <OverlayTrigger
              placement="bottom"
              trigger="focus"
              overlay={MyTooltip("Refreshing Data")}
            >
              <Button variant="info">
                <i className={tableStyles.refreshAnimate + " fas fa-sync"}></i>
              </Button>
            </OverlayTrigger>
          ) : (
            <OverlayTrigger
              placement="bottom"
              trigger="focus"
              overlay={MyTooltip("Data Loaded: " + new Date().toLocaleString())}
            >
              <Button variant="info">
                <i className="far fa-check-circle"></i>
              </Button>
            </OverlayTrigger>
          )}
          <Button active variant="primary" onClick={() => exportToCSV(table, fileName as string)}>
            Export Table to CSV
          </Button>{" "}
        </ButtonGroup>

        <ButtonToolbar>
          <ButtonGroup>
            <Button
              variant="success"
              onClick={() => table.setPageIndex(0)}
              disabled={!table.getCanPreviousPage()}
            >
              <i className="fas fa-angle-double-left"></i>
            </Button>{" "}
            <Button
              variant="success"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              <i className="fas fa-caret-left"></i>
            </Button>{" "}
            <Button
              variant="success"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              <i className="fas fa-caret-right"></i>
            </Button>
            <Button
              variant="success"
              onClick={() => table.setPageIndex(table.getPageCount() - 1)}
              disabled={!table.getCanNextPage()}
            >
              <i className="fas fa-angle-double-right"></i>
            </Button>
          </ButtonGroup>

          <ButtonGroup className="ms-1">
            <Button active variant="success">
              {"Page Size:"}
            </Button>{" "}
            <SplitButton
              id="pageSizeDropdown"
              variant="success"
              title={table.getState().pagination.pageSize}
            >
              {[15, 30, 60, 100, 1000000].map((_pageSize) => (
                <Dropdown.Item
                  id={`${_pageSize}`}
                  key={_pageSize}
                  eventKey={_pageSize}
                  onClick={(eventKey: any) => {
                    console.log(eventKey.target.id);
                    table.setPageSize(Number(eventKey.target.id));
                  }}
                >
                  Show {_pageSize}
                </Dropdown.Item>
              ))}
            </SplitButton>
          </ButtonGroup>
        </ButtonToolbar>
      </div>
      {debugTable && (
        <div className="col-xs-12">
          <div>{table.getRowModel().rows.length} Rows</div>
          <pre>{JSON.stringify(table.getState(), null, 2)}</pre>
        </div>
      )}
    </>
  );
}
// export all the base table modules

export default BaseTable; // Export the table
