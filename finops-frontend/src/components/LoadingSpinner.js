import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';

export const LoadingSpinner = ({
  size = 'md',
  message,
}) => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const sizeMap = {
    sm: { spinner: '24px', border: '2px' },
    md: { spinner: '40px', border: '3px' },
    lg: { spinner: '56px', border: '4px' },
  };

  const containerStyle = {
    ...commonStyles.flexColumn,
    ...commonStyles.flexCenter,
    gap: '16px',
    padding: '32px',
  };

  const spinnerStyle = {
    width: sizeMap[size].spinner,
    height: sizeMap[size].spinner,
    border: `${sizeMap[size].border} solid ${colors.border}`,
    borderTop: `${sizeMap[size].border} solid ${colors.primary}`,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  };

  const messageStyle = {
    fontSize: '14px',
    color: colors.textSecondary,
    textAlign: 'center',
  };

  return (
    <>
      <div style={containerStyle}>
        <div style={spinnerStyle} />
        {message && <p style={messageStyle}>{message}</p>}
      </div>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
};
