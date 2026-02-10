import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, commonStyles } from '../utils/theme';
import { Menu, X, Moon, Sun } from 'lucide-react';

const navigationItems = [
  { label: 'Dashboard', path: '/dashboard', icon: '📊' },
  { label: 'Resources', path: '/resources', icon: '🔧' },
  { label: 'Optimizations', path: '/optimizations', icon: '⚡' },
  { label: 'Budgets', path: '/budgets', icon: '💰' },
  { label: 'Anomalies', path: '/anomalies', icon: '⚠️' },
  { label: 'Savings', path: '/savings', icon: '💎' },
  { label: 'Settings', path: '/settings', icon: '⚙️' },
];

export const Layout = ({ children }) => {
  const { theme, toggleTheme } = useTheme();
  const colors = getThemeColors(theme);
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const layoutStyle = {
    display: 'flex',
    height: '100vh',
    backgroundColor: colors.background,
    color: colors.text,
  };

  const sidebarStyle = {
    width: sidebarOpen ? '250px' : '0px',
    backgroundColor: colors.surface,
    borderRight: `1px solid ${colors.border}`,
    transition: 'width 0.3s ease',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  };

  const sidebarHeaderStyle = {
    padding: '20px',
    borderBottom: `1px solid ${colors.border}`,
    ...commonStyles.flexBetween,
  };

  const sidebarTitleStyle = {
    fontSize: '18px',
    fontWeight: '700',
    color: colors.text,
    margin: 0,
  };

  const navListStyle = {
    listStyle: 'none',
    padding: '12px 0',
    margin: 0,
    flex: 1,
    overflowY: 'auto',
  };

  const navLinkStyle = (isActive) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 20px',
    color: isActive ? colors.primary : colors.text,
    textDecoration: 'none',
    backgroundColor: isActive ? colors.surfaceAlt : 'transparent',
    borderLeft: isActive ? `3px solid ${colors.primary}` : '3px solid transparent',
    transition: commonStyles.transition,
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: isActive ? '600' : '500',
  });

  const mainContentStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  };

  const headerStyle = {
    ...commonStyles.flexBetween,
    padding: '16px 24px',
    backgroundColor: colors.surface,
    borderBottom: `1px solid ${colors.border}`,
    height: '60px',
  };

  const headerLeftStyle = {
    ...commonStyles.flexCenter,
    gap: '16px',
  };

  const headerRightStyle = {
    ...commonStyles.flexCenter,
    gap: '16px',
  };

  const toggleButtonStyle = {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: colors.text,
    padding: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };

  const contentStyle = {
    flex: 1,
    overflow: 'auto',
    padding: '24px',
  };

  const iconStyle = {
    width: '20px',
    height: '20px',
  };

  return (
    <div style={layoutStyle}>
      {/* Sidebar */}
      <aside style={sidebarStyle}>
        <div style={sidebarHeaderStyle}>
          <h1 style={sidebarTitleStyle}>FinOps</h1>
        </div>
        <nav>
          <ul style={navListStyle}>
            {navigationItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <li key={item.path} style={{ margin: '0', padding: '0' }}>
                  <Link to={item.path} style={navLinkStyle(isActive)}>
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <div style={mainContentStyle}>
        {/* Header */}
        <header style={headerStyle}>
          <div style={headerLeftStyle}>
            <button
              style={toggleButtonStyle}
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle sidebar"
            >
              {sidebarOpen ? (
                <X style={iconStyle} />
              ) : (
                <Menu style={iconStyle} />
              )}
            </button>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '600' }}>
              FinOps Dashboard
            </h2>
          </div>
          <div style={headerRightStyle}>
            <button
              style={toggleButtonStyle}
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {theme === 'light' ? (
                <Moon style={iconStyle} />
              ) : (
                <Sun style={iconStyle} />
              )}
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div style={contentStyle}>
          {children}
        </div>
      </div>
    </div>
  );
};
