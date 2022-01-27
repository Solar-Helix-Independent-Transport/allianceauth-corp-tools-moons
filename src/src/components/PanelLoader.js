import React from "react";
import { TailSpin } from "@agney/react-loading";
import { Panel } from "react-bootstrap";
export const PanelLoader = () => {
  return (
    <Panel.Body className="flex-container">
      <TailSpin className="spinner-size" />
    </Panel.Body>
  );
};
