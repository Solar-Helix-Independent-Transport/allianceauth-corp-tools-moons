import React from "react";
import { getAdmimOutstanding } from "../helpers/Api";
import { useQuery } from "react-query";
import { ProgressBar } from "react-bootstrap";

export const OutstandingTax = () => {
  const { isLoading, isFetching, error, data } = useQuery(
    ["outstanding"],
    () => getAdmimOutstanding(),
    {
      refetchOnWindowFocus: false,
    }
  );
  return (
    <>
      <ProgressBar
        striped={isFetching}
        active={isFetching}
        bsStyle={error ? "danger" : isFetching ? "info" : "success"}
        now={100}
      />

      <pre>
        {`Mining Taxes:\n`}
        {isLoading ? "Loading..." : ""}
        {data?.map((i) => (
          <>{`${i}\n`}</>
        ))}
      </pre>
    </>
  );
};
