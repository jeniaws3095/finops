import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';

export const StatusBadge = ({
  status,
  label,
  size = 'md',
}) => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const statusColors = {
    success: { bg: colors.success, text: '#ffffff' },
    warning: { bg: colors.warning, text: '#ffffff' },
    error: { bg: colors.error, text: '#ffffff' },
    info: { bg: colors.info, text: '#ffffff' },
  };

  const sizeStyles = {
    sm: { fontSize: '12px', padding: '4px 8px' },
    md: { fontSize: '14px', padding: '6px 12px' },
    lg: { fontSize: '16px', padding: '8px 16px' },
  };

  const badgeStyle = {
    ...commonStyles.flexCenter,
    backgroundColor: statusColors[status].bg,
    color: statusColors[status].text,
    borderRadius: '20px',
    fontWeight: '500',
    whiteSpace: 'nowrap',
    ...sizeStyles[size],
  };

  return <span style={badgeStyle}>{label}</span>;
};
