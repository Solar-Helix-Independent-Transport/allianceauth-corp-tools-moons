import { ErrorLoader, PanelLoader } from "../components/Loaders/Loaders";
import MoonMenu from "../components/MoonMenu";
import { getPerms } from "../helpers/Api";
import { useQuery } from "react-query";
import { Outlet } from "react-router-dom";

const MoonPage = () => {
  const { isLoading, error, data } = useQuery(["perms"], () => getPerms(), {
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return (
      <>
        <PanelLoader />
        <Outlet />
      </>
    );
  }

  if (error || !data) {
    return <ErrorLoader title="Failed to load permissions" message={(error as Error)?.message} />;
  }

  return (
    <>
      <MoonMenu
        futureExtractions={data.view_observations}
        limitedFutureExtractions={data.view_limited_future}
        rentals={data.view_rentals}
        admin={data.su}
      />
      <Outlet />
    </>
  );
};

export default MoonPage;
