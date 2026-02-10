import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';
import { LoadingSpinner } from '../components';
import { getOptimizationsData } from '../services/api';

export const Optimizations = () => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const result = await getOptimizationsData();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch optimizations');
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

  const cardStyle = {
    padding: '16px',
    backgroundColor: colors.surface,
    borderRadius: '8px',
    border: `1px solid ${colors.border}`,
    ...commonStyles.flexColumn,
    gap: '8px',
  };

  const cardTitleStyle = {
    fontSize: '16px',
    fontWeight: '600',
    color: colors.text,
    margin: 0,
  };

  const impactBadgeStyle = (impact) => ({
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500',
    backgroundColor: impact === 'high' ? colors.error : impact === 'medium' ? colors.warning : colors.info,
    color: '#ffffff',
    width: 'fit-content',
  });

  const errorStyle = {
    backgroundColor: colors.error,
    color: '#ffffff',
    padding: '16px',
    borderRadius: '8px',
  };

  if (loading) {
    return <LoadingSpinner message="Loading optimizations..." />;
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Optimizations</h1>
      
      {error && <div style={errorStyle}>{error}</div>}

      {data && data.optimizations && data.optimizations.length > 0 ? (
        <div style={{ ...commonStyles.flexColumn, gap: '12px' }}>
          {data.optimizations.map((opt) => (
            <div key={opt.id} style={cardStyle}>
              <h3 style={cardTitleStyle}>{opt.title}</h3>
              <p style={{ margin: 0, color: colors.textSecondary, fontSize: '14px' }}>
                {opt.description}
              </p>
              <div style={{ ...commonStyles.flexBetween, marginTop: '8px' }}>
                <span style={impactBadgeStyle(opt.impact)}>
                  {opt.impact.toUpperCase()}
                </span>
                <span style={{ color: colors.success, fontWeight: '600' }}>
                  Save: ${opt.estimatedSavings.toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ padding: '40px', textAlign: 'center', color: colors.textSecondary }}>
          No optimizations available
        </div>
      )}
    </div>
  );
};
