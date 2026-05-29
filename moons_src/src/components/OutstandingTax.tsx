import { getAdminOutstanding } from "../helpers/Api";
import { ProgressBar } from "react-bootstrap";
import { useQuery } from "react-query";

export const OutstandingTax = () => {
  const { isLoading, isFetching, error, data } = useQuery(
    ["outstanding"],
    () => getAdminOutstanding(),
    {
      refetchOnWindowFocus: false,
    }
  );
  return (
    <>
      <ProgressBar
        striped={isFetching}
        variant={error ? "danger" : isFetching ? "info" : "success"}
        now={100}
      />
      <pre>
        {`Mining Taxes:\n`}
        {isLoading && "Loading..."}
        {error && `Error loading outstanding taxes: ${(error as Error).message}\n`}
        {data?.map((i: any) => (
          <>{`${i}\n`}</>
        ))}
      </pre>
    </>
  );
};
