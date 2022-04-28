import React from "react";
import { Panel } from "react-bootstrap";
import { useQuery } from "react-query";
import { getAdminList } from "../helpers/Api";
import { BaseTable } from "../components/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";

const dateFormat = Intl.DateTimeFormat("default", {
  year: "numeric",
  month: "long",
  day: "numeric",
});
const timeFormat = Intl.DateTimeFormat("default", {
  hour: "numeric",
  minute: "numeric",
  hour12: false,
});

const AdminList = () => {
  const { isLoading, isFetching, error, data } = useQuery(
    ["admin-corps"],
    () => getAdminList(),
    {
      initialData: [],
    }
  );

  const columns = React.useMemo(
    () => [
      {
        Header: "Corporation",
        accessor: "name",
      },
      {
        Header: "Character Level Tokens",
        accessor: "char_tokens",
      },
      {
        Header: "Corp Level Tokens",
        accessor: "corp_tokens",
      },
      {
        Header: "Last Observation Update",
        accessor: "obs",
      },
      {
        Header: "Last Frack Update",
        accessor: "frack",
      },
    ],
    []
  );

  return (
    <ErrorBoundary>
      <Panel>
        <Panel.Body>
          <BaseTable {...{ isLoading, isFetching, data, columns, error }} />
        </Panel.Body>
      </Panel>
    </ErrorBoundary>
  );
};

export default AdminList;
