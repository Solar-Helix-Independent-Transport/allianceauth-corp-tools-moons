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

export const TimeAndSince = ({ stringDate }: { stringDate: string | null | undefined }) => {
  if (!stringDate) {
    return <div className="text-center text-muted fst-italic">Never</div>;
  }
  const dateOb = Date.parse(stringDate);
  return (
    <div className="text-center">
      {dateFormat.format(dateOb)} {timeFormat.format(dateOb)}
      <br />
      <small className="text-muted">
        <ReactTimeAgo date={dateOb} />
      </small>
    </div>
  );
};
