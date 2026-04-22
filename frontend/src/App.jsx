import { Routes, Route } from "react-router";
import DashboardLayout from "@medireview/layouts/DashboardLayout";
import Dashboard from "@medireview/views/Dashboard";
import Alerts from "@medireview/views/Alerts";
import Settings from "@medireview/views/Settings";
import ReviewDetail from "@medireview/views/ReviewDetail";
import { AppRootProvider } from "@medireview/lib/app-root.jsx";

export default function App({ basename = "" }) {
  return (
    <AppRootProvider basename={basename}>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="settings" element={<Settings />} />
          <Route path="reviews/:id" element={<ReviewDetail />} />
        </Route>
      </Routes>
    </AppRootProvider>
  );
}
