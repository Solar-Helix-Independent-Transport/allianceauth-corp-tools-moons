import BaseTable from "../components/BaseTable/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import { extractionTimeColumn, moonColumn, oreColumn } from "../components/ExtractionColumns";
import { ErrorLoader } from "../components/Loaders/Loaders";
import { OreColourKey } from "../components/OreColourKey";
import { getFutureExtractions } from "../helpers/Api";
import { useQuery } from "react-query";

const FutureExtractions = () => {
  const { isFetching, error, data } = useQuery(
    ["future-extractions"],
    () => getFutureExtractions(),
    { initialData: [], refetchOnWindowFocus: false }
  );

  const columns = [
    extractionTimeColumn,
    moonColumn("Value Estimate:", "col-md-4"),
    oreColumn("estimated"),
  ];

  if (error) {
    return (
      <ErrorLoader title="Failed to load future extractions" message={(error as Error).message} />
    );
  }

  return (
    <ErrorBoundary>
      <h5 className="text-center small">Key:</h5>
      <OreColourKey />
      <br />
      <BaseTable {...{ isFetching, data, columns }} />
    </ErrorBoundary>
  );
};

export default FutureExtractions;
