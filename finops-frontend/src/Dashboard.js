import { useEffect, useState } from "react";
import { fetchSavingsData, fetchCostingData, fetchCostingByService } from "./data";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend
} from "recharts";
import "./App.css";

const COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626"];

function Dashboard({ onViewDetails }) {
  const [savingsData, setSavingsData] = useState([]);
  const [costingData, setCostingData] = useState(null);
  const [serviceCosting, setServiceCosting] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      const savings = await fetchSavingsData();
      const costing = await fetchCostingData();
      const services = await fetchCostingByService();
      
      setSavingsData(savings);
      setCostingData(costing);
      setServiceCosting(services);
    };

    loadData();

    const interval = setInterval(loadData, 10000); // auto-refresh
    return () => clearInterval(interval);
  }, []);

  const totalSavings = savingsData.reduce(
    (sum, i) => sum + i.money_saved, 0
  );

  const lastRun = savingsData[0]?.date;

  const pieData = savingsData.map(s => ({
    name: s.resource_id,
    value: s.money_saved
  }));

  const serviceChartData = serviceCosting?.services ? [
    { name: "EC2", value: serviceCosting.services.ec2 },
    { name: "Load Balancers", value: serviceCosting.services.load_balancers },
    { name: "EBS Volumes", value: serviceCosting.services.ebs_volumes }
  ] : [];

  return (
    <div className="page">
      <header className="header">
        <h1>🚀 AWS FinOps Dashboard</h1>
        <p>Automated Cost Optimization • Real-time Infrastructure Insights</p>
      </header>

      {/* 🔄 RESIZE & RECOMMENDATIONS SECTION */}
      <div className="section-header">
        <h2>🔄 Resize & Recommendations</h2>
      </div>
      <div className="cards-grid">
        <div className="card">
          <h4>Resize Opportunities</h4>
          <h2>Coming Soon</h2>
          <p>Instance downsizing recommendations</p>
        </div>
      </div>

      {/* 💰 SAVINGS & COST TRACKING SECTION */}
      <div className="section-header">
        <h2>💰 Savings & Cost Tracking</h2>
      </div>
      <div className="cards-grid">
        <div className="card">
          <h4>Total Savings</h4>
          <h2>${totalSavings.toFixed(4)}</h2>
          <p>Generated automatically</p>
        </div>

        <div className="card">
          <h4>Resources Optimized</h4>
          <h2>{savingsData.length}</h2>
          <p>Auto-stopped EC2 instances</p>
        </div>

        <div className="card">
          <h4>Monthly Infrastructure Cost</h4>
          <h2>${costingData?.total_monthly_cost?.toFixed(2) || "0.00"}</h2>
          <p>Current monthly spend</p>
        </div>

        <div className="card">
          <h4>Annual Infrastructure Cost</h4>
          <h2>${costingData?.total_annual_cost?.toFixed(2) || "0.00"}</h2>
          <p>Projected annual spend</p>
        </div>
      </div>

      {/* COST BREAKDOWN CHARTS */}
      <div className="charts-grid">
        <div className="chart-card">
          <h3>Savings Distribution</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  outerRadius={90}
                >
                  {pieData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={COLORS[i % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ textAlign: "center", marginTop: 20 }}>No savings data yet</p>
          )}
        </div>

        <div className="chart-card">
          <h3>Cost by Service</h3>
          {serviceChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={serviceChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ textAlign: "center", marginTop: 20 }}>No costing data yet</p>
          )}
        </div>
      </div>

      {/* 📊 RESOURCE MANAGEMENT SECTION */}
      <div className="section-header">
        <h2>📊 Resource Management</h2>
      </div>

      {/* OPTIMIZATION ACTIONS TABLE */}
      <div className="table-card">
        <h2>Optimization Actions</h2>

        <table>
          <thead>
            <tr>
              <th>Resource ID</th>
              <th>Action</th>
              <th>When</th>
              <th>Region</th>
              <th>Savings</th>
              <th>Details</th>
              <th>AWS</th>
            </tr>
          </thead>
          <tbody>
            {savingsData.map((s, idx) => (
              <tr key={idx}>
                <td>{s.resource_id}</td>
                <td>
                  <span className="badge stopped">
                    Auto-stopped
                  </span>
                </td>
                <td>
                  {new Date(s.date).toLocaleString()}
                </td>
                <td>{s.region}</td>
                <td className="green">
                  ${s.money_saved}
                </td>
                <td>
                  <button 
                    className="btn-details"
                    onClick={() => onViewDetails(s.resource_id, 'instance')}
                  >
                    View
                  </button>
                </td>
                <td>
                  <a
                    href={`https://console.aws.amazon.com/ec2/v2/home?region=${s.region}#InstanceDetails:instanceId=${s.resource_id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="aws-link"
                  >
                    Open
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {savingsData.length === 0 && (
          <p style={{ marginTop: 20 }}>
            No optimization actions yet.
          </p>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
