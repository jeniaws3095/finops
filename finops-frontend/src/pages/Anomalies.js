import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';
import { LoadingSpinner } from '../components';
import { getAnomaliesData } from '../services/api';

export const Anomalies = () => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const result = await getAnomaliesData();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch anomalies');
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

  const severityBadgeStyle = (severity) => ({
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500',
    backgroundColor: severity === 'critical' ? colors.error : severity === 'warning' ? colors.warning : colors.info,
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
    return <LoadingSpinner message="Loading anomalies..." />;
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Anomalies</h1>
      
      {error && <div style={errorStyle}>{error}</div>}

      {data && data.anomalies && data.anomalies.length > 0 ? (
        <div style={{ ...commonStyles.flexColumn, gap: '12px' }}>
          {data.anomalies.map((anomaly) => (
            <div key={anomaly.id} style={cardStyle}>
              <div style={commonStyles.flexBetween}>
                <h3 style={cardTitleStyle}>{anomaly.service}</h3>
                <span style={severityBadgeStyle(anomaly.severity)}>
                  {anomaly.severity.toUpperCase()}
                </span>
              </div>
              <p style={{ margin: 0, color: colors.textSecondary, fontSize: '14px' }}>
                {anomaly.description}
              </p>
              <span style={{ fontSize: '12px', color: colors.textSecondary }}>
                Detected: {new Date(anomaly.detectedAt).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ padding: '40px', textAlign: 'center', color: colors.textSecondary }}>
          No anomalies detected
        </div>
      )}
    </div>
  );
};
