import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ReviewDetail from './pages/ReviewDetail';
import Alerts from './pages/Alerts';
import AutomationSettings from './pages/AutomationSettings';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/reviews/:id" element={<ReviewDetail />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/automation" element={<AutomationSettings />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
