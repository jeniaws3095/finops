export const colors = {
  light: {
    background: '#ffffff',
    surface: '#f5f5f5',
    surfaceAlt: '#eeeeee',
    text: '#000000',
    textSecondary: '#666666',
    border: '#e0e0e0',
    primary: '#0ea5e9',
    primaryDark: '#0284c7',
    success: '#22c55e',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
  },
  dark: {
    background: '#1a1a1a',
    surface: '#2d2d2d',
    surfaceAlt: '#3a3a3a',
    text: '#ffffff',
    textSecondary: '#b0b0b0',
    border: '#404040',
    primary: '#0ea5e9',
    primaryDark: '#0284c7',
    success: '#22c55e',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
  },
};

export const getThemeColors = (theme) => colors[theme];

export const commonStyles = {
  flexCenter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  flexBetween: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  flexColumn: {
    display: 'flex',
    flexDirection: 'column',
  },
  transition: 'all 0.3s ease',
};
