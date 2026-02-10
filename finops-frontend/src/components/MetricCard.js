import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export const MetricCard = ({
  title,
  value,
  unit,
  trend,
  icon,
  loading = false,
  error,
}) => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const cardStyle = {
    backgroundColor: colors.surface,
    border: `1px solid ${colors.border}`,
    borderRadius: '8px',
    padding: '20px',
    transition: commonStyles.transition,
    cursor: 'default',
  };

  const headerStyle = {
    ...commonStyles.flexBetween,
    marginBottom: '16px',
  };

  const titleStyle = {
    fontSize: '14px',
    fontWeight: '500',
    color: colors.textSecondary,
    margin: 0,
  };

  const iconStyle = {
    width: '24px',
    height: '24px',
    color: colors.primary,
  };

  const valueContainerStyle = {
    marginBottom: '12px',
  };

  const valueStyle = {
    fontSize: '32px',
    fontWeight: '700',
    color: colors.text,
    margin: 0,
    lineHeight: '1.2',
  };

  const unitStyle = {
    fontSize: '14px',
    color: colors.textSecondary,
    marginLeft: '4px',
  };

  const trendContainerStyle = {
    ...commonStyles.flexCenter,
    gap: '8px',
    marginTop: '12px',
  };

  const trendStyle = {
    fontSize: '14px',
    fontWeight: '500',
    color: trend?.direction === 'up' ? colors.error : trend?.direction === 'down' ? colors.success : colors.textSecondary,
  };

  const trendIconStyle = {
    width: '16px',
    height: '16px',
  };

  const loadingStyle = {
    ...commonStyles.flexCenter,
    minHeight: '100px',
    color: colors.textSecondary,
  };

  const errorStyle = {
    ...commonStyles.flexCenter,
    minHeight: '100px',
    color: colors.error,
    fontSize: '14px',
    textAlign: 'center',
  };

  if (loading) {
    return (
      <div style={cardStyle}>
        <div style={loadingStyle}>
          <div style={{
            width: '20px',
            height: '20px',
            border: `2px solid ${colors.border}`,
            borderTop: `2px solid ${colors.primary}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }} />
        </div>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={cardStyle}>
        <div style={errorStyle}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div style={cardStyle}>
      <div style={headerStyle}>
        <h3 style={titleStyle}>{title}</h3>
        {icon && <div style={iconStyle}>{icon}</div>}
      </div>
      <div style={valueContainerStyle}>
        <p style={valueStyle}>
          {value}
          {unit && <span style={unitStyle}>{unit}</span>}
        </p>
      </div>
      {trend && (
        <div style={trendContainerStyle}>
          {trend.direction === 'up' && <TrendingUp style={trendIconStyle} />}
          {trend.direction === 'down' && <TrendingDown style={trendIconStyle} />}
          {trend.direction === 'neutral' && <Minus style={trendIconStyle} />}
          <span style={trendStyle}>
            {trend.direction === 'up' ? '+' : ''}{trend.value}% {trend.label}
          </span>
        </div>
      )}
    </div>
  );
};
