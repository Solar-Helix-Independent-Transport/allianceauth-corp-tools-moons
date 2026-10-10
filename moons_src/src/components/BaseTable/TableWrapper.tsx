import BaseTable, { BaseTableProps } from "./BaseTable";
import { ColumnDef } from "@tanstack/react-table";

const TableWrapper = ({
  data,
  isFetching,
  columns,
  initialState,
}: {
  data: any;
  isFetching: boolean;
  columns: ColumnDef<any, any>[];
  initialState?: BaseTableProps["initialState"];
}) => {
  return <BaseTable {...{ isFetching, columns, data, initialState }} />;
};

export default TableWrapper;
