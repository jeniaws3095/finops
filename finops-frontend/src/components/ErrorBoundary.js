import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error) {
    console.error('Error caught by boundary:', error);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorBoundaryContent error={this.state.error} />;
    }

    return this.props.children;
  }
}

const ErrorBoundaryContent = ({ error }) => {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const containerStyle = {
    ...commonStyles.flexColumn,
    ...commonStyles.flexCenter,
    gap: '16px',
    padding: '40px',
    backgroundColor: colors.surface,
    borderRadius: '8px',
    border: `1px solid ${colors.error}`,
    minHeight: '200px',
  };

  const titleStyle = {
    fontSize: '20px',
    fontWeight: '700',
    color: colors.error,
    margin: 0,
  };

  const messageStyle = {
    fontSize: '14px',
    color: colors.textSecondary,
    margin: 0,
    textAlign: 'center',
  };

  const detailsStyle = {
    fontSize: '12px',
    color: colors.textSecondary,
    backgroundColor: colors.background,
    padding: '12px',
    borderRadius: '4px',
    maxWidth: '100%',
    overflow: 'auto',
    fontFamily: 'monospace',
  };

  return (
    <div style={containerStyle}>
      <h2 style={titleStyle}>Something went wrong</h2>
      <p style={messageStyle}>
        An unexpected error occurred. Please try refreshing the page.
      </p>
      {error && (
        <div style={detailsStyle}>
          {error.message}
        </div>
      )}
    </div>
  );
};
