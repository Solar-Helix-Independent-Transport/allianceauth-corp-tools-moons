import React from "react";
import { getAdminExpliain } from "../helpers/Api";
import { useQuery } from "react-query";
import { ProgressBar } from "react-bootstrap";

export const ExplainPre = () => {
  const { isLoading, isFetching, error, data } = useQuery(
    ["explain"],
    () => getAdminExpliain(),
    {
      refetchOnWindowFocus: true,
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
        {console.log(data)}
        {`#Tax Steps Explanation (Highest Rank First):\n`}
        {isLoading ? (
          "Loading..."
        ) : (
          <>
            {`---------------------------------------------------------------------------------------------------------\n`}
            {data?.taxes.map((i) => (
              <>
                {console.log(i)}
                {`${i.name}\n`}
                {`  - Structures Captured in Tax Rank:\n`}
                {i.structures.map((s) => `     - ${s}\n`)}
                {`---------------------------------------------------------------------------------------------------------\n`}
              </>
            ))}
            {`\n#All Structures Seen:\n`}
            {data?.structures.map((i) => (
              <>{`  - ${i}\n`}</>
            ))}
          </>
        )}
      </pre>
    </>
  );
};
