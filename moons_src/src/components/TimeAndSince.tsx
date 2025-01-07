import { Badge } from "react-bootstrap";
import ReactTimeAgo from "react-time-ago";

const dateFormat = Intl.DateTimeFormat("default", {
  year: "numeric",
  month: "long",
  day: "numeric",
});
const timeFormat = Intl.DateTimeFormat("default", {
  hour: "numeric",
  minute: "numeric",
  hour12: false,
});

export const TimeAndSince = ({ stringDate }: { stringDate: string }) => {
  const dateOb = Date.parse(stringDate);
  return (
    <div className="text-center">
      {dateFormat.format(dateOb)} {timeFormat.format(dateOb)}
      <br />
      <Badge className="">
        <ReactTimeAgo date={dateOb} />
      </Badge>
    </div>
  );
};
