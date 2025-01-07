export const seachOre = (row: any, columnId: string, filterValue: string): boolean => {
  if (!filterValue) {
    return true;
  } else {
    console.log(row, columnId, filterValue);
    let rowValue = row.getValue(columnId).reduce((p: any, c: any) => {
      return p + "  " + c.type.cat + " " + c.type.name;
    }, "");
    return rowValue ? rowValue.toLowerCase().includes(filterValue.toLowerCase()) : false;
  }
};
