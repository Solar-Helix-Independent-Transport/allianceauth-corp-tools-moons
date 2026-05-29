import BaseTable from "../components/BaseTable/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import {
  extractionTimeColumn,
  jackpotColumn,
  moonColumn,
  oreColumn,
} from "../components/ExtractionColumns";
import { ErrorLoader } from "../components/Loaders/Loaders";
import { OreColourKey } from "../components/OreColourKey";
import { getExtractions } from "../helpers/Api";
import { useQuery } from "react-query";

const CorporateLedger = () => {
  const { isFetching, error, data } = useQuery({
    queryKey: ["extractions"],
    queryFn: () => getExtractions(),
    initialData: [],
    refetchOnWindowFocus: false,
  });

  const columns = [
    extractionTimeColumn,
    moonColumn("Current Mined Value:"),
    jackpotColumn,
    oreColumn("mined"),
  ];

  if (error) {
    return <ErrorLoader title="Failed to load extractions" message={(error as Error).message} />;
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

export default CorporateLedger;
