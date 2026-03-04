import BaseTable from "./BaseTable";
import { ColumnDef } from "@tanstack/react-table";

const TableWrapper = ({
  data,
  isFetching,
  columns,
}: {
  data: any;
  isFetching: boolean;
  columns: ColumnDef<any, any>[];
}) => {
  return <BaseTable {...{ isFetching, columns, data }} />;
};

export default TableWrapper;
