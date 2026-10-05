import * as ReactDOM from "react-dom";
import { NavLink } from "react-router-dom";

const menuRoot = document.getElementById("nav-left");

const MoonMenu = ({
  futureExtractions = false,
  limitedFutureExtractions = false,
  // observers = false,
  rentals = false,
  importScans = false,
  viewScans = false,
  admin = false,
}) => {
  if (!menuRoot) {
    return <></>;
  }

  return ReactDOM.createPortal(
    <>
      <NavLink to={`active`} className={`nav-link`}>
        Active Moons
      </NavLink>
      {(futureExtractions || limitedFutureExtractions) && (
        <NavLink to={`future`} className={`nav-link`}>
          Future Extractions
        </NavLink>
      )}
      {futureExtractions && (
        <NavLink to={`past`} className={`nav-link`}>
          Past Extractions
        </NavLink>
      )}
      {rentals && (
        <NavLink to={`rentals`} className={`nav-link`}>
          Rentals
        </NavLink>
      )}
      {viewScans && (
        <NavLink to={`scans/values`} className={`nav-link`}>
          Moon Values
        </NavLink>
      )}
      {importScans && (
        <NavLink to={`scans/import`} className={`nav-link`}>
          Import Scans
        </NavLink>
      )}
      {admin && (
        <NavLink to={`admin`} className={`nav-link`}>
          Admin
        </NavLink>
      )}
    </>,
    menuRoot
  );
};

export default MoonMenu;
