import { Routes, Route } from "react-router";
import DashboardLayout from "@medireview/layouts/DashboardLayout";
import Dashboard from "@medireview/views/Dashboard";
import Alerts from "@medireview/views/Alerts";
import Settings from "@medireview/views/Settings";
import ReviewDetail from "@medireview/views/ReviewDetail";

export default function App() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="settings" element={<Settings />} />
        <Route path="reviews/:id" element={<ReviewDetail />} />
      </Route>
    </Routes>
  );
}
