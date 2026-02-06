/**
 * Main Routes Index
 * 
 * Central routing configuration for the Advanced FinOps Platform API.
 * Follows the established pattern of /api/{resource} endpoints.
 * 
 * Requirements: 9.1, 10.1
 */

const express = require('express');
const router = express.Router();

// Health check endpoint
router.get('/health', (req, res) => {
  res.json({
    success: true,
    data: {
      status: 'healthy',
      version: '1.0.0',
      endpoints: [
        '/api/resources',
        '/api/optimizations',
        '/api/anomalies',
        '/api/budgets',
        '/api/savings',
        '/api/pricing'
      ]
    },
    message: 'Advanced FinOps Platform API is healthy',
    timestamp: new Date().toISOString()
  });
});

// API documentation endpoint
router.get('/docs', (req, res) => {
  res.json({
    success: true,
    data: {
      endpoints: {
        '/api/resources': {
          'GET': 'Retrieve resource inventory across all AWS services',
          'POST': 'Add or update resource inventory data',
          'GET /:resourceId': 'Get specific resource by ID',
          'DELETE /:resourceId': 'Remove resource from inventory',
          'GET /stats/summary': 'Get resource inventory statistics'
        },
        '/api/optimizations': {
          'GET': 'Get cost optimization recommendations with filtering and sorting',
          'POST': 'Create new optimization recommendation',
          'POST /approve': 'Approve optimization actions',
          'GET /:optimizationId': 'Get specific optimization by ID',
          'PUT /:optimizationId/status': 'Update optimization status',
          'GET /stats/summary': 'Get optimization statistics and summary'
        },
        '/api/anomalies': {
          'GET': 'Retrieve detected cost anomalies',
          'POST': 'Report new cost anomaly'
        },
        '/api/budgets': {
          'GET': 'Get budget status and forecasts',
          'POST': 'Create or update budget forecast'
        },
        '/api/savings': {
          'GET': 'Calculate and retrieve achieved savings',
          'POST': 'Record savings achievement'
        },
        '/api/pricing': {
          'GET': 'Get pricing intelligence recommendations',
          'POST': 'Submit pricing analysis data'
        }
      }
    },
    message: 'Advanced FinOps Platform API Documentation',
    timestamp: new Date().toISOString()
  });
});

module.exports = router;