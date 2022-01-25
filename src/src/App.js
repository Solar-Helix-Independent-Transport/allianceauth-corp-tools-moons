import "./App.css";
import React from "react";
import { PanelLoader } from "./components/PanelLoader";
import { MoonRentalPannel } from "./components/MoonRentalPannel";

function App() {
  return (
    <>
      <PanelLoader></PanelLoader>
      <MoonRentalPannel></MoonRentalPannel>
    </>
  );
}

export default App;
