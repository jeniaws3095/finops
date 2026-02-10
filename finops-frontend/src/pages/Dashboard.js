import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';
import { MetricCard, LoadingSpinner } from '../components';
import { getDashboardData } from '../services/api';

export const Dashboard = () => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const result = await getDashboardData();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const containerStyle = {
    ...commonStyles.flexColumn,
    gap: '24px',
  };

  const titleStyle = {
    fontSize: '28px',
    fontWeight: '700',
    color: colors.text,
    margin: 0,
  };

  const metricsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '16px',
  };

  const chartsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '16px',
  };

  const chartStyle = {
    backgroundColor: colors.surface,
    padding: '20px',
    borderRadius: '8px',
    border: `1px solid ${colors.border}`,
  };

  const chartTitleStyle = {
    fontSize: '16px',
    fontWeight: '600',
    color: colors.text,
    marginBottom: '12px',
  };

  const errorStyle = {
    backgroundColor: colors.error,
    color: '#ffffff',
    padding: '16px',
    borderRadius: '8px',
  };

  if (loading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Dashboard</h1>

      {error && <div style={errorStyle}>{error}</div>}

      {data && (
        <>
          {/* Key Metrics */}
          <div style={metricsGridStyle}>
            <MetricCard
              title="Total Monthly Cost"
              value={`$${data.total_monthly_cost?.toFixed(2) || '0.00'}`}
              trend={data.cost_trend}
              trendLabel="vs last month"
            />
            <MetricCard
              title="Daily Average"
              value={`$${data.total_daily_cost?.toFixed(2) || '0.00'}`}
              trend={null}
              trendLabel=""
            />
            <MetricCard
              title="Annual Projection"
              value={`$${data.total_annual_cost?.toFixed(2) || '0.00'}`}
              trend={null}
              trendLabel=""
            />
            <MetricCard
              title="Potential Savings"
              value={`$${data.potential_savings?.toFixed(2) || '0.00'}`}
              trend={null}
              trendLabel="per month"
            />
          </div>

          {/* Charts Section */}
          <div style={chartsContainerStyle}>
            {/* Cost by Service */}
            <div style={chartStyle}>
              <div style={chartTitleStyle}>Cost by Service</div>
              {data.service_breakdown && (
                <div style={{ fontSize: '14px', color: colors.textSecondary }}>
                  <div style={{ marginBottom: '8px' }}>
                    EC2: <span style={{ color: colors.text, fontWeight: '600' }}>
                      ${data.service_breakdown.ec2?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                  <div style={{ marginBottom: '8px' }}>
                    Load Balancers: <span style={{ color: colors.text, fontWeight: '600' }}>
                      ${data.service_breakdown.load_balancers?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                  <div>
                    EBS: <span style={{ color: colors.text, fontWeight: '600' }}>
                      ${data.service_breakdown.ebs_volumes?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Cost by Region */}
            <div style={chartStyle}>
              <div style={chartTitleStyle}>Top Regions</div>
              {data.region_breakdown && data.region_breakdown.length > 0 ? (
                <div style={{ fontSize: '14px', color: colors.textSecondary }}>
                  {data.region_breakdown.slice(0, 3).map((region, idx) => (
                    <div key={idx} style={{ marginBottom: '8px' }}>
                      {region.region}: <span style={{ color: colors.text, fontWeight: '600' }}>
                        ${region.monthly?.toFixed(2) || '0.00'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ color: colors.textSecondary }}>No region data available</div>
              )}
            </div>

            {/* Resource Summary */}
            <div style={chartStyle}>
              <div style={chartTitleStyle}>Resource Summary</div>
              {data.resource_summary ? (
                <div style={{ fontSize: '14px', color: colors.textSecondary }}>
                  <div style={{ marginBottom: '8px' }}>
                    EC2 Instances: <span style={{ color: colors.text, fontWeight: '600' }}>
                      {data.resource_summary.ec2_count || 0}
                    </span>
                  </div>
                  <div style={{ marginBottom: '8px' }}>
                    EBS Volumes: <span style={{ color: colors.text, fontWeight: '600' }}>
                      {data.resource_summary.ebs_count || 0}
                    </span>
                  </div>
                  <div>
                    Load Balancers: <span style={{ color: colors.text, fontWeight: '600' }}>
                      {data.resource_summary.lb_count || 0}
                    </span>
                  </div>
                </div>
              ) : (
                <div style={{ color: colors.textSecondary }}>No resource data available</div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
