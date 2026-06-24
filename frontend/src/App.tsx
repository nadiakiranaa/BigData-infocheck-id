import { useState } from 'react';
import { DashboardPage } from './pages/DashboardPage';
import { LandingPage } from './pages/LandingPage';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  if (isAuthenticated) {
    return <DashboardPage onLogout={() => setIsAuthenticated(false)} />;
  }

  return <LandingPage onLogin={() => setIsAuthenticated(true)} />;
}
