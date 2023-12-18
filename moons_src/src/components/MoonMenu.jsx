import React from "react";
import { Nav } from "react-bootstrap";
import { Navbar } from "react-bootstrap";

import NavLink from "./NavLinkActive";

const MoonMenu = ({
  futureExtractions = false,
  limitedFutureExtractions = false,
  observers = false,
  admin = false,
}) => {
  return (
    <Navbar fluid collapseOnSelect>
      <Navbar.Header>
        <Navbar.Toggle />
      </Navbar.Header>
      <Navbar.Collapse>
        <Nav>
          <Navbar.Brand>Moon Board</Navbar.Brand>
          <NavLink key="active" href={`#/active`}>
            Active Moons
          </NavLink>
          {(futureExtractions || limitedFutureExtractions) && (
            <NavLink key="future" href={`#/future`}>
              Future Extractions
            </NavLink>
          )}
          {futureExtractions && (
            <NavLink key="past" href={`#/past`}>
              Past Extractions
            </NavLink>
          )}
          {admin && (
            <NavLink key="admin" href={`#/admin`}>
              Admin
            </NavLink>
          )}
        </Nav>
      </Navbar.Collapse>
    </Navbar>
  );
};

export default MoonMenu;
