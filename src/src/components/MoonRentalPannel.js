import React, { useState } from "react";
import { ApiSelect } from "./ApiSelect";
import { searchChars, searchCorps, searchMoons } from "../helpers/Api";
import {
  Panel,
  FormGroup,
  FormControl,
  ControlLabel,
  HelpBlock,
} from "react-bootstrap";

export const MoonRentalPannel = ({ setValue, apiLookup }) => {
  const [character_id, setCharacter] = useState({ label: "", value: 0 });
  const [corporation_id, setCorporation] = useState({ label: "", value: 0 });
  const [moon_id, setMoon] = useState({ label: "", value: 0 });
  const [isk, setIsk] = useState(100000000);

  function handleIskChange(e) {
    setIsk(e.target.value);
  }

  return (
    <Panel bsStyle="primary">
      <Panel.Heading>Moon Rental</Panel.Heading>
      <Panel.Body>
        <form>
          <FormGroup controlId="formMoons">
            <ControlLabel>Charater</ControlLabel>
            <ApiSelect apiLookup={searchChars} setValue={setCharacter} />
            <ControlLabel>Corp</ControlLabel>
            <ApiSelect apiLookup={searchCorps} setValue={setCorporation} />
            <ControlLabel>Moon</ControlLabel>
            <ApiSelect apiLookup={searchMoons} setValue={setMoon} />
            <HelpBlock>Search for who and what you want to rent.</HelpBlock>
            <FormControl
              type="text"
              value={isk}
              placeholder="Enter text"
              onChange={handleIskChange}
            />
          </FormGroup>

          <h3>
            Rent {moon_id.label}({moon_id.value}) to {character_id.label}(
            {character_id.value}) from {corporation_id.label}(
            {corporation_id.value}) for ${isk}
          </h3>
        </form>
      </Panel.Body>
    </Panel>
  );
};
