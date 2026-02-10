import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';
import { LoadingSpinner } from '../components';
import { getBudgetsData } from '../services/api';

export const Budgets = () => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const result = await getBudgetsData();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch budgets');
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
    gap: '12px',
  };

  const cardTitleStyle = {
    fontSize: '16px',
    fontWeight: '600',
    color: colors.text,
    margin: 0,
  };

  const progressBarStyle = {
    width: '100%',
    height: '8px',
    backgroundColor: colors.border,
    borderRadius: '4px',
    overflow: 'hidden',
  };

  const progressFillStyle = (percentage) => ({
    height: '100%',
    width: `${Math.min(percentage, 100)}%`,
    backgroundColor: percentage > 80 ? colors.error : percentage > 60 ? colors.warning : colors.success,
    transition: 'width 0.3s ease',
  });

  const errorStyle = {
    backgroundColor: colors.error,
    color: '#ffffff',
    padding: '16px',
    borderRadius: '8px',
  };

  if (loading) {
    return <LoadingSpinner message="Loading budgets..." />;
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Budgets</h1>
      
      {error && <div style={errorStyle}>{error}</div>}

      {data && data.budgets && data.budgets.length > 0 ? (
        <div style={{ ...commonStyles.flexColumn, gap: '12px' }}>
          {data.budgets.map((budget) => (
            <div key={budget.id} style={cardStyle}>
              <div style={commonStyles.flexBetween}>
                <h3 style={cardTitleStyle}>{budget.name}</h3>
                <span style={{ color: colors.textSecondary, fontSize: '14px' }}>
                  ${budget.spent.toLocaleString()} / ${budget.limit.toLocaleString()}
                </span>
              </div>
              <div style={progressBarStyle}>
                <div style={progressFillStyle(budget.percentage)} />
              </div>
              <span style={{ fontSize: '12px', color: colors.textSecondary }}>
                {budget.percentage}% used
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ padding: '40px', textAlign: 'center', color: colors.textSecondary }}>
          No budgets configured
        </div>
      )}
    </div>
  );
};
