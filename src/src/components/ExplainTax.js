import React from "react";
import { getAdminExpliain } from "../helpers/Api";
import { useQuery } from "react-query";

export const ExplainPre = () => {
  const { isLoading, isFetching, error, data } = useQuery(
    ["explain"],
    () => getAdminExpliain(),
    {
      refetchOnWindowFocus: true,
    }
  );
  if (isLoading) return <pre></pre>;
  if (isFetching) return <pre>Loading...</pre>;
  return (
    <pre>
      {console.log(data)}
      {`#Tax Steps Explanation (Highest Rank First):\n`}
      {`---------------------------------------------------------------------------------------------------------\n`}
      {data.taxes.map((i) => (
        <>
          {console.log(i)}
          {`${i.name}\n`}
          {`  - Structures Captured in Tax Rank:\n`}
          {i.structures.map((s) => `     - ${s}\n`)}
          {`---------------------------------------------------------------------------------------------------------\n`}
        </>
      ))}
      {`\n#All Structures Seen:\n`}
      {data.structures.map((i) => (
        <>{`  - ${i}\n`}</>
      ))}
    </pre>
  );
};
