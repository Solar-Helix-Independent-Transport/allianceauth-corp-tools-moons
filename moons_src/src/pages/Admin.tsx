import BaseTable from "../components/BaseTable/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import { ExplainPre } from "../components/ExplainTax";
import { OutstandingTax } from "../components/OutstandingTax";
import { getAdminList } from "../helpers/Api";
import { corps } from "../types";
import { createColumnHelper } from "@tanstack/react-table";
import { Card } from "react-bootstrap";
import { useQuery } from "react-query";

const AdminList = () => {
  const { isLoading, isFetching, data } = useQuery(["admin-corps"], () => getAdminList(), {
    initialData: [],
    refetchOnWindowFocus: false,
  });
  const columnHelper = createColumnHelper<corps>();

  const columns = [
    columnHelper.accessor("name", {
      header: "Corporation",
    }),
    columnHelper.accessor("char_tokens", {
      header: "Character Level Tokens",
    }),
    columnHelper.accessor("corp_tokens", {
      header: "Corp Level Tokens",
    }),
    columnHelper.accessor("obs", {
      header: "Last Observation Update",
    }),
    columnHelper.accessor("frack", {
      header: "Last Frack Update",
    }),
  ];

  return (
    <ErrorBoundary>
      <BaseTable {...{ isLoading, isFetching, data, columns }} />
      <br />
      <Card>
        <Card.Body>
          <ErrorBoundary>
            <OutstandingTax />
          </ErrorBoundary>
        </Card.Body>
      </Card>
      <br />
      <Card>
        <Card.Body>
          <ErrorBoundary>
            <ExplainPre />
          </ErrorBoundary>
        </Card.Body>
      </Card>
    </ErrorBoundary>
  );
};

export default AdminList;
