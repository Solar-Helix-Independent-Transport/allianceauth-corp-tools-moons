import AdminList from "./pages/Admin";
import CorporateLedger from "./pages/CorporateLedger";
import FutureExtractions from "./pages/FutureExtractions";
import MoonsPage from "./pages/MoonsPage";
import PastLedger from "./pages/PastLedger";
import TimeAgo from "javascript-time-ago";
import en from "javascript-time-ago/locale/en";
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";

TimeAgo.addDefaultLocale(en);

const Moons = () => {
  return (
    <>
      <Router>
        <Routes>
          <Route index element={<Navigate to="m/r/" replace />} />
          <Route path={"m/r/"} element={<MoonsPage />}>
            <Route index element={<Navigate to="active" replace />} />
            <Route path={"active"} element={<CorporateLedger />} />
            <Route path={"admin"} element={<AdminList />} />
            <Route path={"future"} element={<FutureExtractions />} />
            <Route path={"past"} element={<PastLedger />} />
          </Route>
        </Routes>
      </Router>
    </>
  );
};

export default Moons;
