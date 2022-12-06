import React from "react";
import { getAdmimOutstanding } from "../helpers/Api";
import { useQuery } from "react-query";

export const OutstandingTax = () => {
  const { isLoading, isFetching, error, data } = useQuery(
    ["outstanding"],
    () => getAdmimOutstanding(),
    {
      refetchOnWindowFocus: false,
    }
  );
  if (isLoading) return <pre></pre>;
  if (isFetching) return <pre>Loading...</pre>;
  return (
    <pre>
      {console.log(data)}
      {`Mining Taxes:\n`}
      {data.map((i) => (
        <>{`${i}\n`}</>
      ))}
    </pre>
  );
};
