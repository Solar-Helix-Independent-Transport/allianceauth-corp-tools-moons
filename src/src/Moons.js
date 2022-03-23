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

TimeAgo.addDefaultLocale(en);

function Moons() {
  const { isLoading, data } = useQuery(["perms"], () => getPerms());

  return isLoading ? (
    <PanelLoader></PanelLoader>
  ) : (
    <Router>
      <br />
      <MoonMenu futureExtractions={data.view_observations} />
      <Switch>
        <Route exact path={"/"} component={() => <Redirect to="/active" />} />
        <Route path={"/active"} component={() => CorporateLedger()} />
        <Route path={"/future"} component={() => FutureExtractions()} />
      </Switch>
    </Router>
  );
}

export default Moons;
