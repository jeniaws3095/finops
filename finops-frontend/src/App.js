import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { Layout, ErrorBoundary } from './components';
import {
  Dashboard,
  Resources,
  Optimizations,
  Budgets,
  Anomalies,
  Savings,
  Settings,
  NotFound,
} from './pages';

const App = () => {
  return (
    <ThemeProvider>
      <ErrorBoundary>
        <Router>
          <Layout>
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/resources" element={<Resources />} />
              <Route path="/optimizations" element={<Optimizations />} />
              <Route path="/budgets" element={<Budgets />} />
              <Route path="/anomalies" element={<Anomalies />} />
              <Route path="/savings" element={<Savings />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Layout>
        </Router>
      </ErrorBoundary>
    </ThemeProvider>
  );
};

export default App;
