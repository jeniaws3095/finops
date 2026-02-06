/**
 * Integration Routes
 * 
 * API endpoints for handling data integration from the Python automation engine.
 * Provides endpoints for analysis summaries, execution results, and reports.
 * 
 * Requirements: 9.1, 15.1
 */

const express = require('express');
const router = express.Router();

// In-memory storage for integration data
let analysisResults = [];
let executionResults = [];
let reports = [];

/**
 * POST /optimization-analysis (also available as /api/optimization-analysis)
 * Store optimization analysis summary data
 */
router.post('/', (req, res) => {
  // Check if this is the optimization-analysis endpoint
  if (req.originalUrl.includes('optimization-analysis')) {
    try {
      const analysisData = {
        id: `analysis_${Date.now()}`,
        ...req.body,
        receivedAt: new Date().toISOString()
      };
      
      analysisResults.push(analysisData);
      
      console.log('📊 RECEIVED OPTIMIZATION ANALYSIS:', analysisData.id);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('optimization_analysis_received', {
          analysis: analysisData,
          totalAnalyses: analysisResults.length
        });
      }
      
      res.json({
        success: true,
        data: analysisData,
        message: 'Optimization analysis received successfully',
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('❌ Error storing optimization analysis:', error);
      res.status(500).json({
        success: false,
        data: null,
        message: 'Failed to store optimization analysis: ' + error.message,
        timestamp: new Date().toISOString()
      });
    }
    return;
  }
  
  // Check if this is the anomaly-analysis endpoint
  if (req.originalUrl.includes('anomaly-analysis')) {
    try {
      const analysisData = {
        id: `anomaly_analysis_${Date.now()}`,
        ...req.body,
        receivedAt: new Date().toISOString()
      };
      
      analysisResults.push(analysisData);
      
      console.log('🚨 RECEIVED ANOMALY ANALYSIS:', analysisData.id);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('anomaly_analysis_received', {
          analysis: analysisData,
          totalAnalyses: analysisResults.length
        });
      }
      
      res.json({
        success: true,
        data: analysisData,
        message: 'Anomaly analysis received successfully',
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('❌ Error storing anomaly analysis:', error);
      res.status(500).json({
        success: false,
        data: null,
        message: 'Failed to store anomaly analysis: ' + error.message,
        timestamp: new Date().toISOString()
      });
    }
    return;
  }
  
  // Check if this is the budget-analysis endpoint
  if (req.originalUrl.includes('budget-analysis')) {
    try {
      const analysisData = {
        id: `budget_analysis_${Date.now()}`,
        ...req.body,
        receivedAt: new Date().toISOString()
      };
      
      analysisResults.push(analysisData);
      
      console.log('💰 RECEIVED BUDGET ANALYSIS:', analysisData.id);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('budget_analysis_received', {
          analysis: analysisData,
          totalAnalyses: analysisResults.length
        });
      }
      
      res.json({
        success: true,
        data: analysisData,
        message: 'Budget analysis received successfully',
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('❌ Error storing budget analysis:', error);
      res.status(500).json({
        success: false,
        data: null,
        message: 'Failed to store budget analysis: ' + error.message,
        timestamp: new Date().toISOString()
      });
    }
    return;
  }
  
  // Check if this is the execution-results endpoint
  if (req.originalUrl.includes('execution-results')) {
    try {
      const executionData = {
        id: `execution_${Date.now()}`,
        ...req.body,
        receivedAt: new Date().toISOString()
      };
      
      executionResults.push(executionData);
      
      console.log('⚡ RECEIVED EXECUTION RESULTS:', executionData.id);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('execution_results_received', {
          execution: executionData,
          totalExecutions: executionResults.length
        });
      }
      
      res.json({
        success: true,
        data: executionData,
        message: 'Execution results received successfully',
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('❌ Error storing execution results:', error);
      res.status(500).json({
        success: false,
        data: null,
        message: 'Failed to store execution results: ' + error.message,
        timestamp: new Date().toISOString()
      });
    }
    return;
  }
  
  // Check if this is the reports endpoint
  if (req.originalUrl.includes('reports')) {
    try {
      const reportData = {
        id: `report_${Date.now()}`,
        ...req.body,
        receivedAt: new Date().toISOString()
      };
      
      reports.push(reportData);
      
      console.log('📋 RECEIVED WORKFLOW REPORT:', reportData.id);
      
      // Broadcast real-time update
      if (global.broadcastUpdate) {
        global.broadcastUpdate('report_received', {
          report: reportData,
          totalReports: reports.length
        });
      }
      
      res.json({
        success: true,
        data: reportData,
        message: 'Workflow report received successfully',
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('❌ Error storing workflow report:', error);
      res.status(500).json({
        success: false,
        data: null,
        message: 'Failed to store workflow report: ' + error.message,
        timestamp: new Date().toISOString()
      });
    }
    return;
  }
  
  // Default response for unknown endpoints
  res.status(404).json({
    success: false,
    data: null,
    message: 'Integration endpoint not found',
    timestamp: new Date().toISOString()
  });
});

/**
 * POST /api/optimization-analysis
 * Store optimization analysis summary data
 */
router.post('/optimization-analysis', (req, res) => {
  try {
    const analysisData = {
      id: `analysis_${Date.now()}`,
      ...req.body,
      receivedAt: new Date().toISOString()
    };
    
    analysisResults.push(analysisData);
    
    console.log('📊 RECEIVED OPTIMIZATION ANALYSIS:', analysisData.id);
    
    // Broadcast real-time update
    if (global.broadcastUpdate) {
      global.broadcastUpdate('optimization_analysis_received', {
        analysis: analysisData,
        totalAnalyses: analysisResults.length
      });
    }
    
    res.json({
      success: true,
      data: analysisData,
      message: 'Optimization analysis received successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error storing optimization analysis:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to store optimization analysis: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/anomaly-analysis
 * Store anomaly detection analysis summary data
 */
router.post('/anomaly-analysis', (req, res) => {
  try {
    const analysisData = {
      id: `anomaly_analysis_${Date.now()}`,
      ...req.body,
      receivedAt: new Date().toISOString()
    };
    
    analysisResults.push(analysisData);
    
    console.log('🚨 RECEIVED ANOMALY ANALYSIS:', analysisData.id);
    
    // Broadcast real-time update
    if (global.broadcastUpdate) {
      global.broadcastUpdate('anomaly_analysis_received', {
        analysis: analysisData,
        totalAnalyses: analysisResults.length
      });
    }
    
    res.json({
      success: true,
      data: analysisData,
      message: 'Anomaly analysis received successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error storing anomaly analysis:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to store anomaly analysis: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/budget-analysis
 * Store budget management analysis summary data
 */
router.post('/budget-analysis', (req, res) => {
  try {
    const analysisData = {
      id: `budget_analysis_${Date.now()}`,
      ...req.body,
      receivedAt: new Date().toISOString()
    };
    
    analysisResults.push(analysisData);
    
    console.log('💰 RECEIVED BUDGET ANALYSIS:', analysisData.id);
    
    // Broadcast real-time update
    if (global.broadcastUpdate) {
      global.broadcastUpdate('budget_analysis_received', {
        analysis: analysisData,
        totalAnalyses: analysisResults.length
      });
    }
    
    res.json({
      success: true,
      data: analysisData,
      message: 'Budget analysis received successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error storing budget analysis:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to store budget analysis: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/execution-results
 * Store optimization execution results
 */
router.post('/execution-results', (req, res) => {
  try {
    const executionData = {
      id: `execution_${Date.now()}`,
      ...req.body,
      receivedAt: new Date().toISOString()
    };
    
    executionResults.push(executionData);
    
    console.log('⚡ RECEIVED EXECUTION RESULTS:', executionData.id);
    
    // Broadcast real-time update
    if (global.broadcastUpdate) {
      global.broadcastUpdate('execution_results_received', {
        execution: executionData,
        totalExecutions: executionResults.length
      });
    }
    
    res.json({
      success: true,
      data: executionData,
      message: 'Execution results received successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error storing execution results:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to store execution results: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * POST /api/reports
 * Store comprehensive workflow reports
 */
router.post('/reports', (req, res) => {
  try {
    const reportData = {
      id: `report_${Date.now()}`,
      ...req.body,
      receivedAt: new Date().toISOString()
    };
    
    reports.push(reportData);
    
    console.log('📋 RECEIVED WORKFLOW REPORT:', reportData.id);
    
    // Broadcast real-time update
    if (global.broadcastUpdate) {
      global.broadcastUpdate('report_received', {
        report: reportData,
        totalReports: reports.length
      });
    }
    
    res.json({
      success: true,
      data: reportData,
      message: 'Workflow report received successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error storing workflow report:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to store workflow report: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/integration/status
 * Get integration status and statistics
 */
router.get('/status', (req, res) => {
  try {
    const status = {
      analysisResults: analysisResults.length,
      executionResults: executionResults.length,
      reports: reports.length,
      lastActivity: null,
      integrationHealth: 'healthy'
    };
    
    // Find most recent activity
    const allItems = [
      ...analysisResults.map(a => ({ type: 'analysis', timestamp: a.receivedAt })),
      ...executionResults.map(e => ({ type: 'execution', timestamp: e.receivedAt })),
      ...reports.map(r => ({ type: 'report', timestamp: r.receivedAt }))
    ];
    
    if (allItems.length > 0) {
      allItems.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      status.lastActivity = allItems[0];
    }
    
    // Check integration health based on recent activity
    if (status.lastActivity) {
      const lastActivityTime = new Date(status.lastActivity.timestamp);
      const hoursSinceLastActivity = (Date.now() - lastActivityTime.getTime()) / (1000 * 60 * 60);
      
      if (hoursSinceLastActivity > 24) {
        status.integrationHealth = 'stale';
      } else if (hoursSinceLastActivity > 6) {
        status.integrationHealth = 'warning';
      }
    } else {
      status.integrationHealth = 'no_data';
    }
    
    res.json({
      success: true,
      data: status,
      message: 'Integration status retrieved successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving integration status:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve integration status: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/integration/recent
 * Get recent integration activity
 */
router.get('/recent', (req, res) => {
  try {
    const { limit = 10, type } = req.query;
    
    let recentItems = [];
    
    // Collect all items with type information
    if (!type || type === 'analysis') {
      recentItems.push(...analysisResults.map(a => ({ ...a, itemType: 'analysis' })));
    }
    
    if (!type || type === 'execution') {
      recentItems.push(...executionResults.map(e => ({ ...e, itemType: 'execution' })));
    }
    
    if (!type || type === 'report') {
      recentItems.push(...reports.map(r => ({ ...r, itemType: 'report' })));
    }
    
    // Sort by received time (most recent first)
    recentItems.sort((a, b) => new Date(b.receivedAt) - new Date(a.receivedAt));
    
    // Apply limit
    const limitedItems = recentItems.slice(0, parseInt(limit));
    
    res.json({
      success: true,
      data: {
        items: limitedItems,
        total: recentItems.length,
        limit: parseInt(limit)
      },
      message: `Retrieved ${limitedItems.length} recent integration items`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error retrieving recent integration activity:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to retrieve recent integration activity: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * DELETE /api/integration/cleanup
 * Clean up old integration data
 */
router.delete('/cleanup', (req, res) => {
  try {
    const { olderThanDays = 7 } = req.query;
    const cutoffDate = new Date(Date.now() - parseInt(olderThanDays) * 24 * 60 * 60 * 1000);
    
    const initialCounts = {
      analysisResults: analysisResults.length,
      executionResults: executionResults.length,
      reports: reports.length
    };
    
    // Clean up old data
    analysisResults = analysisResults.filter(a => new Date(a.receivedAt) > cutoffDate);
    executionResults = executionResults.filter(e => new Date(e.receivedAt) > cutoffDate);
    reports = reports.filter(r => new Date(r.receivedAt) > cutoffDate);
    
    const finalCounts = {
      analysisResults: analysisResults.length,
      executionResults: executionResults.length,
      reports: reports.length
    };
    
    const cleaned = {
      analysisResults: initialCounts.analysisResults - finalCounts.analysisResults,
      executionResults: initialCounts.executionResults - finalCounts.executionResults,
      reports: initialCounts.reports - finalCounts.reports
    };
    
    const totalCleaned = cleaned.analysisResults + cleaned.executionResults + cleaned.reports;
    
    console.log(`🧹 CLEANED UP ${totalCleaned} old integration records`);
    
    res.json({
      success: true,
      data: {
        cleaned,
        totalCleaned,
        remaining: finalCounts,
        cutoffDate: cutoffDate.toISOString()
      },
      message: `Cleaned up ${totalCleaned} old integration records`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error cleaning up integration data:', error);
    res.status(500).json({
      success: false,
      data: null,
      message: 'Failed to clean up integration data: ' + error.message,
      timestamp: new Date().toISOString()
    });
  }
});

module.exports = router;