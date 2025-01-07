import { PanelLoader } from "./components/Loaders/Loaders";
import MoonMenu from "./components/MoonMenu";
import { getPerms } from "./helpers/Api";
import AdminList from "./pages/Admin";
import CorporateLedger from "./pages/CorporateLedger";
import FutureExtractions from "./pages/FutureExtractions";
import PastLedger from "./pages/PastLedger";
import TimeAgo from "javascript-time-ago";
import en from "javascript-time-ago/locale/en";
import { useQuery } from "react-query";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

TimeAgo.addDefaultLocale(en);

function Moons() {
  const { isLoading, data } = useQuery(["perms"], () => getPerms(), {
    refetchOnWindowFocus: false,
  });

  return isLoading ? (
    <PanelLoader></PanelLoader>
  ) : (
    <Router>
      <br />
      <MoonMenu
        futureExtractions={data.view_observations}
        limitedFutureExtractions={data.view_limited_future}
        admin={data.su}
      />
      <Routes>
        <Route path={"/"} element={<Navigate to="/active" replace />} />
        <Route path={"/active"} element={<CorporateLedger />} />
        <Route path={"/admin"} element={<AdminList />} />
        <Route path={"/future"} element={<FutureExtractions />} />
        <Route path={"/past"} element={<PastLedger />} />
      </Routes>
    </Router>
  );
}

export default Moons;
