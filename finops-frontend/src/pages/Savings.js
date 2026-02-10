import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';
import { LoadingSpinner, MetricCard } from '../components';
import { getSavingsData } from '../services/api';

export const Savings = () => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const result = await getSavingsData();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch savings data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const containerStyle = {
    ...commonStyles.flexColumn,
    gap: '24px',
  };

  const titleStyle = {
    fontSize: '24px',
    fontWeight: '700',
    color: colors.text,
    margin: 0,
  };

  const metricsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '16px',
  };

  const errorStyle = {
    backgroundColor: colors.error,
    color: '#ffffff',
    padding: '16px',
    borderRadius: '8px',
  };

  if (loading) {
    return <LoadingSpinner message="Loading savings data..." />;
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Savings</h1>
      
      {error && <div style={errorStyle}>{error}</div>}

      {data && (
        <div style={metricsGridStyle}>
          <MetricCard
            title="Total Savings"
            value={`$${(data.totalSavings || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}`}
          />
          <MetricCard
            title="Savings Trend"
            value={`${data.savingsTrend || 0}%`}
          />
        </div>
      )}
    </div>
  );
};
