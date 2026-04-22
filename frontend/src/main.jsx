import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import App from "@medireview/App";
import "@medireview/styles/globals.css";

const ROUTE_PREFIX = import.meta.env.VITE_MEDIREVIEW_ROUTE_PREFIX || "";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter basename={ROUTE_PREFIX || undefined}>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
