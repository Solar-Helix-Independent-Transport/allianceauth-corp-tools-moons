import React from "react";
import { Panel, Label } from "react-bootstrap";
import { useQuery } from "react-query";
import { getPastExtractions } from "../helpers/Api";
import ErrorBoundary from "../components/ErrorBoundary";
import "./CorporateLedger.css";

const PastLedger = () => {
  const { isLoading, isFetching, error, data } = useQuery(
    ["extractions", "Past"],
    () => getPastExtractions(),
    {
      initialData: [],
      refetchOnWindowFocus: false,
    }
  );

  return (
    <ErrorBoundary>
      <Panel>
        <Panel.Body></Panel.Body>
      </Panel>
    </ErrorBoundary>
  );
};

export default PastLedger;
