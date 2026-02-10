import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';

export const NotFound = () => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const containerStyle = {
    ...commonStyles.flexColumn,
    ...commonStyles.flexCenter,
    gap: '24px',
    minHeight: '400px',
    textAlign: 'center',
  };

  const titleStyle = {
    fontSize: '48px',
    fontWeight: '700',
    color: colors.text,
    margin: 0,
  };

  const messageStyle = {
    fontSize: '18px',
    color: colors.textSecondary,
    margin: 0,
  };

  const linkStyle = {
    display: 'inline-block',
    padding: '12px 24px',
    backgroundColor: colors.primary,
    color: '#ffffff',
    textDecoration: 'none',
    borderRadius: '4px',
    fontWeight: '500',
    transition: commonStyles.transition,
  };

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>404</h1>
      <p style={messageStyle}>Page not found</p>
      <Link to="/dashboard" style={linkStyle}>
        Back to Dashboard
      </Link>
    </div>
  );
};
