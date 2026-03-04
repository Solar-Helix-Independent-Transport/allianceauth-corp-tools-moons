import { BaseTableProps, tableInitialState } from "./Types";
import {
  getCoreRowModel,
  getFacetedMinMaxValues,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";

const NewBaseTable = ({
  isFetching = false,
  debugTable = false,
  data = [],
  columns,
  striped = false,
  hover = false,
  initialState = undefined,
  exportFileName = undefined,
}: BaseTableProps) => {
  let initState: tableInitialState = {
    pagination: {
      pageSize: 15,
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
    debugTable: debugTable,
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

// export all the base table modules

export default NewBaseTable; // Export the table
