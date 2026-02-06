import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';

const Settings = () => {
  const [settings, setSettings] = useState({
    general: {
      autoRefreshInterval: 300,
      defaultTimeRange: '7d',
      currency: 'USD',
      timezone: 'UTC'
    },
    thresholds: {
      cpuUtilization: 5,
      memoryUtilization: 10,
      costAnomalyThreshold: 20,
      budgetWarningThreshold: 80,
      budgetCriticalThreshold: 95
    },
    notifications: {
      emailAlerts: true,
      anomalyAlerts: true,
      budgetAlerts: true,
      optimizationAlerts: false,
      weeklyReports: true
    },
    automation: {
      autoExecuteLowRisk: false,
      dryRunMode: true,
      approvalRequired: true,
      rollbackEnabled: true
    },
    aws: {
      defaultRegions: ['us-east-1', 'us-west-2'],
      scanInterval: 3600,
      retentionPeriod: 90,
      costExplorerEnabled: true
    }
  });


  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [activeTab, setActiveTab] = useState('general');

  useEffect(() => {
    // In a real app, load settings from API
    // fetchSettings();
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);

      // In a real app, save to API
      // await apiService.updateSettings(settings);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      setMessage({ type: 'success', text: 'Settings saved successfully!' });
    } catch (err) {
      console.error('Error saving settings:', err);
      setMessage({ type: 'error', text: 'Failed to save settings. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (window.confirm('Are you sure you want to reset all settings to defaults?')) {
      // Reset to default values
      setSettings({
        general: {
          autoRefreshInterval: 300,
          defaultTimeRange: '7d',
          currency: 'USD',
          timezone: 'UTC'
        },
        thresholds: {
          cpuUtilization: 5,
          memoryUtilization: 10,
          costAnomalyThreshold: 20,
          budgetWarningThreshold: 80,
          budgetCriticalThreshold: 95
        },
        notifications: {
          emailAlerts: true,
          anomalyAlerts: true,
          budgetAlerts: true,
          optimizationAlerts: false,
          weeklyReports: true
        },
        automation: {
          autoExecuteLowRisk: false,
          dryRunMode: true,
          approvalRequired: true,
          rollbackEnabled: true
        },
        aws: {
          defaultRegions: ['us-east-1', 'us-west-2'],
          scanInterval: 3600,
          retentionPeriod: 90,
          costExplorerEnabled: true
        }
      });
      setMessage({ type: 'info', text: 'Settings reset to defaults.' });
    }
  };

  const updateSetting = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  const tabs = [
    { id: 'general', name: 'General', icon: SettingsIcon },
    { id: 'thresholds', name: 'Thresholds', icon: AlertTriangle },
    { id: 'notifications', name: 'Notifications', icon: Info },
    { id: 'automation', name: 'Automation', icon: RefreshCw },
    { id: 'aws', name: 'AWS Config', icon: CheckCircle }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <div className="flex space-x-3">
          <button
            onClick={handleReset}
            className="btn-secondary"
          >
            Reset to Defaults
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-primary flex items-center"
          >
            {saving ? (
              <LoadingSpinner size="sm" className="mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            Save Changes
          </button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-md ${message.type === 'success' ? 'bg-green-50 text-green-800' :
            message.type === 'error' ? 'bg-red-50 text-red-800' :
              'bg-blue-50 text-blue-800'
          }`}>
          <div className="flex">
            {message.type === 'success' && <CheckCircle className="h-5 w-5 mr-2" />}
            {message.type === 'error' && <AlertTriangle className="h-5 w-5 mr-2" />}
            {message.type === 'info' && <Info className="h-5 w-5 mr-2" />}
            <span>{message.text}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md ${activeTab === tab.id
                      ? 'bg-primary-100 text-primary-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="card">
            {/* General Settings */}
            {activeTab === 'general' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">General Settings</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Auto Refresh Interval (seconds)
                    </label>
                    <input
                      type="number"
                      value={settings.general.autoRefreshInterval}
                      onChange={(e) => updateSetting('general', 'autoRefreshInterval', parseInt(e.target.value))}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Default Time Range
                    </label>
                    <select
                      value={settings.general.defaultTimeRange}
                      onChange={(e) => updateSetting('general', 'defaultTimeRange', e.target.value)}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    >
                      <option value="24h">24 Hours</option>
                      <option value="7d">7 Days</option>
                      <option value="30d">30 Days</option>
                      <option value="90d">90 Days</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Currency
                    </label>
                    <select
                      value={settings.general.currency}
                      onChange={(e) => updateSetting('general', 'currency', e.target.value)}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    >
                      <option value="USD">USD ($)</option>
                      <option value="EUR">EUR (€)</option>
                      <option value="GBP">GBP (£)</option>
                      <option value="JPY">JPY (¥)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Timezone
                    </label>
                    <select
                      value={settings.general.timezone}
                      onChange={(e) => updateSetting('general', 'timezone', e.target.value)}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    >
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="Europe/London">London</option>
                      <option value="Asia/Tokyo">Tokyo</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Threshold Settings */}
            {activeTab === 'thresholds' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">Optimization Thresholds</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CPU Utilization Threshold (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={settings.thresholds.cpuUtilization}
                      onChange={(e) => updateSetting('thresholds', 'cpuUtilization', parseInt(e.target.value))}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Resources below this threshold are considered underutilized</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Memory Utilization Threshold (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={settings.thresholds.memoryUtilization}
                      onChange={(e) => updateSetting('thresholds', 'memoryUtilization', parseInt(e.target.value))}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Cost Anomaly Threshold (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="1000"
                      value={settings.thresholds.costAnomalyThreshold}
                      onChange={(e) => updateSetting('thresholds', 'costAnomalyThreshold', parseInt(e.target.value))}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Cost increases above this percentage trigger anomaly alerts</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Budget Warning Threshold (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={settings.thresholds.budgetWarningThreshold}
                      onChange={(e) => updateSetting('thresholds', 'budgetWarningThreshold', parseInt(e.target.value))}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Budget Critical Threshold (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={settings.thresholds.budgetCriticalThreshold}
                      onChange={(e) => updateSetting('thresholds', 'budgetCriticalThreshold', parseInt(e.target.value))}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Notification Settings */}
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">Notification Preferences</h3>

                <div className="space-y-4">
                  {Object.entries(settings.notifications).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-900">
                          {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                        </label>
                        <p className="text-xs text-gray-500">
                          {key === 'emailAlerts' && 'Receive email notifications for important events'}
                          {key === 'anomalyAlerts' && 'Get notified when cost anomalies are detected'}
                          {key === 'budgetAlerts' && 'Receive alerts when budgets exceed thresholds'}
                          {key === 'optimizationAlerts' && 'Get notified about new optimization opportunities'}
                          {key === 'weeklyReports' && 'Receive weekly cost optimization reports'}
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={value}
                          onChange={(e) => updateSetting('notifications', key, e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Automation Settings */}
            {activeTab === 'automation' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">Automation Settings</h3>

                <div className="space-y-4">
                  {Object.entries(settings.automation).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-900">
                          {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                        </label>
                        <p className="text-xs text-gray-500">
                          {key === 'autoExecuteLowRisk' && 'Automatically execute low-risk optimizations without approval'}
                          {key === 'dryRunMode' && 'Run in dry-run mode to preview changes without executing them'}
                          {key === 'approvalRequired' && 'Require manual approval for all optimization actions'}
                          {key === 'rollbackEnabled' && 'Enable automatic rollback capabilities for failed optimizations'}
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={value}
                          onChange={(e) => updateSetting('automation', key, e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  ))}
                </div>

                {settings.automation.dryRunMode && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                    <div className="flex">
                      <AlertTriangle className="h-5 w-5 text-yellow-400 mr-2" />
                      <div>
                        <h4 className="text-sm font-medium text-yellow-800">Dry Run Mode Enabled</h4>
                        <p className="text-sm text-yellow-700 mt-1">
                          All optimization actions will be simulated without making actual changes to your AWS resources.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AWS Configuration */}
            {activeTab === 'aws' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">AWS Configuration</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Default Regions
                    </label>
                    <select
                      multiple
                      value={settings.aws.defaultRegions}
                      onChange={(e) => updateSetting('aws', 'defaultRegions', Array.from(e.target.selectedOptions, option => option.value))}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                      size="4"
                    >
                      <option value="us-east-1">US East (N. Virginia)</option>
                      <option value="us-west-2">US West (Oregon)</option>
                      <option value="eu-west-1">Europe (Ireland)</option>
                      <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                      <option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple regions</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Scan Interval (seconds)
                    </label>
                    <input
                      type="number"
                      min="300"
                      value={settings.aws.scanInterval}
                      onChange={(e) => updateSetting('aws', 'scanInterval', parseInt(e.target.value))}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">How often to scan AWS resources for optimization opportunities</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Data Retention Period (days)
                    </label>
                    <input
                      type="number"
                      min="7"
                      max="365"
                      value={settings.aws.retentionPeriod}
                      onChange={(e) => updateSetting('aws', 'retentionPeriod', parseInt(e.target.value))}
                      className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-gray-900">
                        Cost Explorer Integration
                      </label>
                      <p className="text-xs text-gray-500">
                        Enable integration with AWS Cost Explorer for enhanced cost analysis
                      </p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.aws.costExplorerEnabled}
                        onChange={(e) => updateSetting('aws', 'costExplorerEnabled', e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;