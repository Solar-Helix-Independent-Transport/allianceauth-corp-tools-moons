import { getAdminExplain } from "../helpers/Api";
import { ProgressBar } from "react-bootstrap";
import { useQuery } from "react-query";

export const ExplainPre = () => {
  const { isLoading, isFetching, error, data } = useQuery(["explain"], () => getAdminExplain(), {
    refetchOnWindowFocus: true,
  });
  return (
    <>
      <ProgressBar
        striped={isFetching}
        variant={error ? "danger" : isFetching ? "info" : "success"}
        now={100}
      />
      <pre>
        {`#Tax Steps Explanation (Highest Rank First):\n`}
        {isLoading && "Loading..."}
        {error != null &&
          `Error loading tax explanation: ${(error as Error).message ?? "Unknown error"}\n`}
        {!isLoading && !error && (
          <>
            {`---------------------------------------------------------------------------------------------------------\n`}
            {data?.taxes.map((i: any) => (
              <>
                {`${i.name}\n`}
                {`  - Structures Captured in Tax Rank:\n`}
                {i.structures.map((s: any) => `     - ${s}\n`)}
                {`---------------------------------------------------------------------------------------------------------\n`}
              </>
            ))}
            {`\n#All Structures Seen:\n`}
            {data?.structures.map((i: any) => (
              <>{`  - ${i}\n`}</>
            ))}
          </>
        )}
      </pre>
    </>
  );
};
