import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Resources from './pages/Resources';
import Optimizations from './pages/Optimizations';
import Budgets from './pages/Budgets';
import Anomalies from './pages/Anomalies';
import Savings from './pages/Savings';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/optimizations" element={<Optimizations />} />
          <Route path="/budgets" element={<Budgets />} />
          <Route path="/anomalies" element={<Anomalies />} />
          <Route path="/savings" element={<Savings />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;