/**
 * Dashboard Routes
 * 
 * API endpoints specifically designed for dashboard data formatting and real-time capabilities.
 * Provides aggregated data, time-series formatting, and WebSocket integration.
 * 
 * Requirements: 9.2, 9.3, 9.5
 */

const express = require('express');
// const axios = require("axios");
const router = express.Router();

// Import data from other route modules (in production, this would be from database)
const resourceRoutes = require('./resources');
const optimizationRoutes = require('./optimizations');
const budgetRoutes = require('./budgets');
const anomalyRoutes = require('./anomalies');
const savingsRoutes = require('./savings');
const pricingRoutes = require('./pricing');

// Python bot base URL
// const FINOPS_BOT_URL = process.env.FINOPS_BOT_URL || "http://localhost:7000";

/**
 * GET /api/dashboard (base endpoint)
 * Get main dashboard data - matches frontend getDashboardData() call
 */
router.get('/', async (req, res) => {
  try {
    const { timeRange = '7d' } = req.query;

    const dashboardData = {
      totalCost: 45678.90,
      monthlySavings: 8234.56,
      optimizationOpportunities: 23,
      activeAnomalies: 3,
      resourceCount: 1247,
      budgetUtilization: 78.5,
      lastUpdated: new Date().toISOString()
    };

    console.log('📊 SENDING BASE DASHBOARD DATA');

    res.json({
      success: true,
      data: dashboardData,
      message: 'Dashboard data retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving dashboard data:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve dashboard data: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// /**
//  * GET /api/dashboard
//  * Main dashboard summary
//  * Frontend: apiService.getDashboardData()
//  */
// router.get("/", async (req, res) => {
//   try {
//     // Quick health check
//     // await axios.get(`${FINOPS_BOT_URL}/health`, { timeout: 3000 });

//     const botResponse = await axios.get(`${FINOPS_BOT_URL}/dashboard`, {
//       timeout: 120000 // FinOps scans can be heavy
//     });

//     console.log("🤖 Dashboard data received from Python FinOps bot");

//     res.json({
//       success: true,
//       source: botResponse.data.source || "python-finops-bot",
//       data: botResponse.data.data,
//       timestamp: new Date().toISOString()
//     });
//   } catch (error) {
//     console.error("❌ Failed to fetch dashboard data from FinOps bot:", error.message);

//     res.status(503).json({
//       success: false,
//       source: "backend",
//       message: "FinOps bot is unavailable",
//       error: error.message,
//       timestamp: new Date().toISOString()
//     });
//   }
// });


/**
 * GET /api/dashboard/metrics
 * Get dashboard metrics - matches frontend getDashboardMetrics() call
 */
router.get('/metrics', async (req, res) => {
  try {
    const metrics = {
      costTrend: '+12.3%',
      savingsRate: '+15.7%',
      efficiencyScore: 87.2,
      optimizationRate: 65.4,
      anomalyDetectionRate: 95.2
    };

    console.log('📈 SENDING DASHBOARD METRICS');

    res.json({
      success: true,
      data: metrics,
      message: 'Dashboard metrics retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving dashboard metrics:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve dashboard metrics: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/dashboard/charts
 * Get dashboard chart data - matches frontend getDashboardCharts() call
 */
router.get('/charts', async (req, res) => {
  try {
    const { timeRange = '7d' } = req.query;

    const charts = {
      costTrend: [
        { date: '2024-01-01', cost: 42000, savings: 7500 },
        { date: '2024-01-02', cost: 43200, savings: 7800 },
        { date: '2024-01-03', cost: 44100, savings: 8100 },
        { date: '2024-01-04', cost: 45600, savings: 8200 },
        { date: '2024-01-05', cost: 45678, savings: 8234 }
      ],
      serviceBreakdown: [
        { name: 'EC2', value: 18500, color: '#3b82f6' },
        { name: 'RDS', value: 12300, color: '#10b981' },
        { name: 'S3', value: 8900, color: '#f59e0b' },
        { name: 'Lambda', value: 3200, color: '#ef4444' },
        { name: 'EBS', value: 2778, color: '#8b5cf6' }
      ],
      regionCosts: [
        { region: 'us-east-1', cost: 18500 },
        { region: 'us-west-2', cost: 15200 },
        { region: 'eu-west-1', cost: 8900 },
        { region: 'ap-southeast-1', cost: 3078 }
      ]
    };

    console.log(`📊 SENDING DASHBOARD CHARTS (${timeRange})`);

    res.json({
      success: true,
      data: charts,
      message: 'Dashboard charts retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving dashboard charts:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve dashboard charts: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/dashboard/overview
 * Get comprehensive dashboard overview with KPIs
 */
router.get('/overview', async (req, res) => {
  try {
    const { timeRange = '30d', region, service } = req.query;

    // This would typically aggregate data from database
    // For now, we'll simulate the aggregation
    const overview = {
      kpis: {
        totalResources: 0,
        totalOptimizations: 0,
        totalSavings: 0,
        activeAnomalies: 0,
        budgetUtilization: 0,
        lastUpdated: new Date().toISOString()
      },
      trends: {
        savingsTrend: generateTrendData(timeRange, 'savings'),
        costTrend: generateTrendData(timeRange, 'cost'),
        optimizationsTrend: generateTrendData(timeRange, 'optimizations'),
        anomaliesTrend: generateTrendData(timeRange, 'anomalies')
      },
      distributions: {
        serviceDistribution: generateServiceDistribution(),
        regionDistribution: generateRegionDistribution(),
        riskDistribution: generateRiskDistribution()
      },
      alerts: {
        critical: [],
        warnings: [],
        info: []
      }
    };

    console.log('📊 SENDING DASHBOARD OVERVIEW');

    res.json({
      success: true,
      data: overview,
      message: 'Dashboard overview retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving dashboard overview:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve dashboard overview: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/dashboard/time-series
 * Get time-series data formatted for Recharts
 */
router.get('/time-series', (req, res) => {
  try {
    const {
      metric = 'savings',
      timeRange = '30d',
      groupBy = 'day',
      service,
      region
    } = req.query;

    const timeSeriesData = generateTimeSeriesData(metric, timeRange, groupBy, { service, region });

    console.log(`📈 SENDING TIME-SERIES DATA: ${metric}, ${timeRange}, ${groupBy}`);

    res.json({
      success: true,
      data: timeSeriesData,
      message: `Time-series data for ${metric} retrieved successfully`,
      metadata: {
        metric,
        timeRange,
        groupBy,
        dataPoints: timeSeriesData.length,
        filters: { service, region }
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving time-series data:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve time-series data: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/dashboard/filters
 * Get available filter options for dashboard
 */
router.get('/filters', (req, res) => {
  try {
    // In production, this would query the database for unique values
    const filters = {
      services: [
        'EC2',
        'RDS',
        'Lambda',
        'S3',
        'EBS',
        'ELB',
        'CloudWatch'
      ],
      regions: [
        'us-east-1',
        'us-west-2',
        'eu-west-1',
        'ap-southeast-1',
        'ca-central-1'
      ],
      optimizationTypes: [
        'rightsizing',
        'pricing',
        'cleanup',
        'scheduling'
      ],
      riskLevels: [
        'LOW',
        'MEDIUM',
        'HIGH',
        'CRITICAL'
      ],
      timeRanges: [
        { value: '7d', label: 'Last 7 days' },
        { value: '30d', label: 'Last 30 days' },
        { value: '90d', label: 'Last 90 days' },
        { value: '1y', label: 'Last year' }
      ],
      groupByOptions: [
        { value: 'hour', label: 'Hourly' },
        { value: 'day', label: 'Daily' },
        { value: 'week', label: 'Weekly' },
        { value: 'month', label: 'Monthly' }
      ]
    };

    console.log('🔍 SENDING FILTER OPTIONS');

    res.json({
      success: true,
      data: filters,
      message: 'Filter options retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving filter options:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve filter options: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/dashboard/aggregated
 * Get aggregated data for dashboard widgets
 */
router.get('/aggregated', (req, res) => {
  try {
    const {
      widgets = 'all',
      timeRange = '30d',
      service,
      region
    } = req.query;

    const requestedWidgets = widgets === 'all' ?
      ['savings', 'optimizations', 'anomalies', 'budgets', 'resources'] :
      widgets.split(',');

    const aggregatedData = {};

    requestedWidgets.forEach(widget => {
      switch (widget) {
        case 'savings':
          aggregatedData.savings = generateSavingsWidget(timeRange, { service, region });
          break;
        case 'optimizations':
          aggregatedData.optimizations = generateOptimizationsWidget(timeRange, { service, region });
          break;
        case 'anomalies':
          aggregatedData.anomalies = generateAnomaliesWidget(timeRange, { service, region });
          break;
        case 'budgets':
          aggregatedData.budgets = generateBudgetsWidget(timeRange, { service, region });
          break;
        case 'resources':
          aggregatedData.resources = generateResourcesWidget(timeRange, { service, region });
          break;
      }
    });

    console.log(`📊 SENDING AGGREGATED DATA: ${requestedWidgets.join(', ')}`);

    res.json({
      success: true,
      data: aggregatedData,
      message: 'Aggregated dashboard data retrieved successfully',
      metadata: {
        widgets: requestedWidgets,
        timeRange,
        filters: { service, region }
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving aggregated data:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve aggregated data: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/dashboard/refresh
 * Trigger real-time data refresh and broadcast to WebSocket clients
 */
router.post('/refresh', (req, res) => {
  try {
    const { dataType = 'all', force = false } = req.body;

    console.log(`🔄 TRIGGERING DATA REFRESH: ${dataType}`);

    // Simulate data refresh process
    const refreshResults = {
      refreshId: `refresh_${Date.now()}`,
      dataType,
      startedAt: new Date().toISOString(),
      status: 'in_progress'
    };

    // Broadcast refresh start to WebSocket clients
    if (global.broadcastUpdate) {
      global.broadcastUpdate('refresh_started', refreshResults);
    }

    // Simulate async refresh process
    setTimeout(() => {
      const completedResults = {
        ...refreshResults,
        status: 'completed',
        completedAt: new Date().toISOString(),
        updatedRecords: Math.floor(Math.random() * 100) + 10
      };

      // Broadcast refresh completion
      if (global.broadcastUpdate) {
        global.broadcastUpdate('refresh_completed', completedResults);

        // Also broadcast updated data
        global.broadcastUpdate('data_updated', {
          type: dataType,
          timestamp: new Date().toISOString(),
          summary: generateRefreshSummary(dataType)
        });
      }
    }, 2000); // Simulate 2-second refresh process

    res.json({
      success: true,
      data: refreshResults,
      message: 'Data refresh initiated successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error triggering data refresh:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to trigger data refresh: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/dashboard/export
 * Export dashboard data in various formats
 */
router.get('/export', (req, res) => {
  try {
    const {
      format = 'json',
      dataType = 'overview',
      timeRange = '30d',
      service,
      region
    } = req.query;

    let exportData;

    switch (dataType) {
      case 'overview':
        exportData = generateExportOverview(timeRange, { service, region });
        break;
      case 'savings':
        exportData = generateExportSavings(timeRange, { service, region });
        break;
      case 'optimizations':
        exportData = generateExportOptimizations(timeRange, { service, region });
        break;
      default:
        exportData = generateExportOverview(timeRange, { service, region });
    }

    // Set appropriate headers based on format
    if (format === 'csv') {
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', `attachment; filename="finops-${dataType}-${timeRange}.csv"`);
      res.send(convertToCSV(exportData));
    } else {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', `attachment; filename="finops-${dataType}-${timeRange}.json"`);
      res.json({
        success: true,
        data: exportData,
        metadata: {
          format,
          dataType,
          timeRange,
          exportedAt: new Date().toISOString(),
          filters: { service, region }
        }
      });
    }

    console.log(`📤 EXPORTED DATA: ${dataType} as ${format}`);
  } catch (error) {
    console.error('❌ Error exporting data:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to export data: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Helper functions for generating mock data (in production, these would query the database)

function generateTrendData(timeRange, metric) {
  const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365;
  const data = [];

  for (let i = days; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000);
    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.floor(Math.random() * 1000) + 100,
      change: (Math.random() - 0.5) * 20
    });
  }

  return data;
}

function generateServiceDistribution() {
  return [
    { name: 'EC2', value: 45, cost: 4500 },
    { name: 'RDS', value: 25, cost: 2500 },
    { name: 'Lambda', value: 15, cost: 1500 },
    { name: 'S3', value: 10, cost: 1000 },
    { name: 'Other', value: 5, cost: 500 }
  ];
}

function generateRegionDistribution() {
  return [
    { name: 'us-east-1', value: 40, cost: 4000 },
    { name: 'us-west-2', value: 30, cost: 3000 },
    { name: 'eu-west-1', value: 20, cost: 2000 },
    { name: 'ap-southeast-1', value: 10, cost: 1000 }
  ];
}

function generateRiskDistribution() {
  return [
    { name: 'LOW', value: 50, count: 25 },
    { name: 'MEDIUM', value: 30, count: 15 },
    { name: 'HIGH', value: 15, count: 8 },
    { name: 'CRITICAL', value: 5, count: 2 }
  ];
}

function generateTimeSeriesData(metric, timeRange, groupBy, filters) {
  const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : timeRange === '90d' ? 90 : 365;
  const data = [];

  for (let i = days; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000);
    data.push({
      date: date.toISOString().split('T')[0],
      timestamp: date.getTime(),
      value: Math.floor(Math.random() * 1000) + 100,
      metric: metric
    });
  }

  return data;
}

function generateSavingsWidget(timeRange, filters) {
  return {
    totalSavings: 15000,
    monthlySavings: 5000,
    savingsRate: 25.5,
    trend: 'up',
    trendPercentage: 12.3,
    topSavings: [
      { service: 'EC2', amount: 8000 },
      { service: 'RDS', amount: 4000 },
      { service: 'Lambda', amount: 3000 }
    ]
  };
}

function generateOptimizationsWidget(timeRange, filters) {
  return {
    totalOptimizations: 45,
    pendingOptimizations: 12,
    approvedOptimizations: 8,
    executedOptimizations: 25,
    potentialSavings: 25000,
    averageConfidence: 78.5
  };
}

function generateAnomaliesWidget(timeRange, filters) {
  return {
    totalAnomalies: 8,
    unresolvedAnomalies: 3,
    criticalAnomalies: 1,
    costImpact: 2500,
    detectionRate: 95.2,
    averageResolutionTime: 4.5
  };
}

function generateBudgetsWidget(timeRange, filters) {
  return {
    totalBudgets: 12,
    budgetsOverThreshold: 2,
    averageUtilization: 67.8,
    totalBudgetAmount: 100000,
    totalSpend: 67800,
    forecastAccuracy: 92.1
  };
}

function generateResourcesWidget(timeRange, filters) {
  return {
    totalResources: 234,
    optimizedResources: 156,
    underutilizedResources: 45,
    unusedResources: 12,
    optimizationRate: 66.7,
    costPerResource: 428.5
  };
}

function generateRefreshSummary(dataType) {
  return {
    recordsUpdated: Math.floor(Math.random() * 100) + 10,
    newRecords: Math.floor(Math.random() * 20) + 1,
    lastRefresh: new Date().toISOString(),
    dataQuality: 'good'
  };
}

function generateExportOverview(timeRange, filters) {
  return {
    summary: {
      totalSavings: 15000,
      totalOptimizations: 45,
      totalAnomalies: 8,
      totalResources: 234
    },
    trends: generateTrendData(timeRange, 'overview'),
    distributions: {
      services: generateServiceDistribution(),
      regions: generateRegionDistribution(),
      risks: generateRiskDistribution()
    }
  };
}

function generateExportSavings(timeRange, filters) {
  return {
    totalSavings: 15000,
    savingsBreakdown: generateServiceDistribution(),
    timeline: generateTrendData(timeRange, 'savings')
  };
}

function generateExportOptimizations(timeRange, filters) {
  return {
    totalOptimizations: 45,
    optimizationTypes: generateRiskDistribution(),
    timeline: generateTrendData(timeRange, 'optimizations')
  };
}

function convertToCSV(data) {
  // Simple CSV conversion - in production, use a proper CSV library
  const headers = Object.keys(data);
  const csvContent = headers.join(',') + '\n' +
    headers.map(header => JSON.stringify(data[header])).join(',');
  return csvContent;
}

module.exports = router;