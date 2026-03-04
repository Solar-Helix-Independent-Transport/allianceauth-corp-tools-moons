import { Header, HeaderGroup, Table as ReactTable } from "@tanstack/react-table";
import { stringify } from "csv-stringify/browser/esm/sync";

export const exportToCSV = (table: ReactTable<any>, exportFileName: string) => {
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

function strToKey(keyString: string, ob: object) {
  return keyString.split(".").reduce(function (p: any, prop: any) {
    return p[prop];
  }, ob);
}
