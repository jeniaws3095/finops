import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';

export const Settings = () => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

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

  const placeholderStyle = {
    padding: '40px',
    backgroundColor: colors.surface,
    borderRadius: '8px',
    border: `1px solid ${colors.border}`,
    textAlign: 'center',
    color: colors.textSecondary,
  };

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>Settings</h1>
      <div style={placeholderStyle}>
        <p>Settings page content coming soon...</p>
      </div>
    </div>
  );
};
