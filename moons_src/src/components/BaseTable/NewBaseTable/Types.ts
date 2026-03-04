import {
  ColumnDef,
  PaginationInitialTableState,
  Table as ReactTable,
  SortingTableState,
  VisibilityTableState,
} from "@tanstack/react-table";

export type tableInitialState =
  | SortingTableState
  | VisibilityTableState
  | PaginationInitialTableState;

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

export interface _BaseTableProps extends BaseTableProps {
  table: ReactTable<any>;
}
