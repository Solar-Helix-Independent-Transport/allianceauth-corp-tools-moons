import { PanelLoader } from "../components/Loaders/Loaders";
import MoonMenu from "../components/MoonMenu";
import { getPerms } from "../helpers/Api";
import { useQuery } from "react-query";
import { Outlet } from "react-router-dom";

const MoonPage = () => {
  const { isLoading, data } = useQuery(["perms"], () => getPerms(), {
    refetchOnWindowFocus: false,
  });
  console.log("here");
  return isLoading ? (
    <>
      <PanelLoader></PanelLoader>
      <Outlet /> {/* Render the Children here */}
    </>
  ) : (
    <>
      <MoonMenu
        futureExtractions={data.view_observations}
        limitedFutureExtractions={data.view_limited_future}
        admin={data.su}
      />
      <Outlet /> {/* Render the Children here */}
    </>
  );
};

export default MoonPage;
