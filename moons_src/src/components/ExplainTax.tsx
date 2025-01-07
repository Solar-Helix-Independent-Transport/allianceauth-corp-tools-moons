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
        variant={error ? "danger" : isFetching ? "info" : "success"}
        now={100}
      />
      <pre>
        {`#Tax Steps Explanation (Highest Rank First):\n`}
        {isLoading ? (
          "Loading..."
        ) : (
          <>
            {`---------------------------------------------------------------------------------------------------------\n`}
            {data?.taxes.map((i: any) => (
              <>
                {console.log(i)}
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
