import React from "react";
import CorporateLedger from "./pages/CorporateLedger";
import { QueryClient, QueryClientProvider } from "react-query";
import en from "javascript-time-ago/locale/en";
import TimeAgo from "javascript-time-ago";

TimeAgo.addDefaultLocale(en);

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <CorporateLedger></CorporateLedger>
    </QueryClientProvider>
  );
}

export default App;
