import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';
import { LoadingSpinner } from '../components';
import { getResourcesData } from '../services/api';

export const Resources = () => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const result = await getResourcesData();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch resources');
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

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: colors.surface,
    borderRadius: '8px',
    overflow: 'hidden',
    border: `1px solid ${colors.border}`,
  };

  const thStyle = {
    padding: '12px',
    textAlign: 'left',
    backgroundColor: colors.background,
    borderBottom: `1px solid ${colors.border}`,
    fontWeight: '600',
    color: colors.text,
  };

  const tdStyle = {
    padding: '12px',
    borderBottom: `1px solid ${colors.border}`,
    color: colors.text,
  };

  const errorStyle = {
    backgroundColor: colors.error,
    color: '#ffffff',
    padding: '16px',
    borderRadius: '8px',
  };

  if (loading) {
    return <LoadingSpinner message="Loading resources..." />;
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Resources</h1>
      
      {error && <div style={errorStyle}>{error}</div>}

      {data && data.length > 0 ? (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Instance ID</th>
              <th style={thStyle}>Type</th>
              <th style={thStyle}>Region</th>
              <th style={thStyle}>State</th>
              <th style={thStyle}>Monthly Cost</th>
            </tr>
          </thead>
          <tbody>
            {data.map((resource) => (
              <tr key={resource.instance_id}>
                <td style={tdStyle}>{resource.instance_id}</td>
                <td style={tdStyle}>{resource.instance_type}</td>
                <td style={tdStyle}>{resource.region}</td>
                <td style={tdStyle}>{resource.state}</td>
                <td style={tdStyle}>${resource.monthly_cost?.toFixed(2) || '0.00'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div style={{ padding: '40px', textAlign: 'center', color: colors.textSecondary }}>
          No resources found
        </div>
      )}
    </div>
  );
};
