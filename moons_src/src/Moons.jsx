import React from "react";
import CorporateLedger from "./pages/CorporateLedger";
import FutureExtractions from "./pages/FutureExtractions";
import en from "javascript-time-ago/locale/en";
import TimeAgo from "javascript-time-ago";
import { getPerms } from "./helpers/Api";
import { PanelLoader } from "./components/PanelLoader";
import { useQuery } from "react-query";
import {
  HashRouter as Router,
  Switch,
  Route,
  Redirect,
} from "react-router-dom";
import MoonMenu from "./components/MoonMenu";
import AdminList from "./pages/Admin";
import PastLedger from "./pages/PastLedger";

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
      <Switch>
        <Route exact path={"/"} component={() => <Redirect to="/active" />} />
        <Route path={"/active"} component={() => CorporateLedger()} />
        {data.su && <Route path={"/admin"} component={() => AdminList()} />}
        {data.view_observations && (
          <>
            <Route path={"/future"} component={() => FutureExtractions()} />
            <Route path={"/past"} component={() => PastLedger()} />
          </>
        )}
      </Switch>
    </Router>
  );
}

export default Moons;
