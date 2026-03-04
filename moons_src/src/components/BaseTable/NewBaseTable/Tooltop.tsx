import Tooltip from "react-bootstrap/Tooltip";

export function BaseTooltip(message: string) {
  return <Tooltip id="tooltip">{message}</Tooltip>;
}
