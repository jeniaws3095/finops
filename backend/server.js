const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const fs = require("fs");
const path = require("path");

const app = express();

// Enhanced logging and monitoring
const winston = require("winston");
const morgan = require("morgan");
const { v4: uuidv4 } = require("uuid");

// Configure structured logging
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'advanced-finops-backend' },
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

// System monitoring data
const systemMetrics = {
  startTime: Date.now(),
  requestCount: 0,
  errorCount: 0,
  responseTimeSum: 0,
  endpoints: {},
  healthChecks: {},
  alerts: []
};

// Correlation ID middleware
app.use((req, res, next) => {
  req.correlationId = req.headers['x-correlation-id'] || uuidv4();
  res.setHeader('X-Correlation-ID', req.correlationId);

  // Add correlation ID to logger context
  req.logger = logger.child({ correlationId: req.correlationId });

  next();
});

// Enhanced request logging with correlation IDs
app.use(morgan(':method :url :status :res[content-length] - :response-time ms :req[x-correlation-id]', {
  stream: {
    write: (message) => {
      logger.info(message.trim(), { component: 'http' });
    }
  }
}));

// Performance monitoring middleware
app.use((req, res, next) => {
  const startTime = Date.now();

  res.on('finish', () => {
    const responseTime = Date.now() - startTime;
    const endpoint = `${req.method} ${req.route ? req.route.path : req.path}`;

    // Update system metrics
    systemMetrics.requestCount++;
    systemMetrics.responseTimeSum += responseTime;

    if (res.statusCode >= 400) {
      systemMetrics.errorCount++;
    }

    // Update endpoint-specific metrics
    if (!systemMetrics.endpoints[endpoint]) {
      systemMetrics.endpoints[endpoint] = {
        requestCount: 0,
        errorCount: 0,
        responseTimeSum: 0,
        avgResponseTime: 0
      };
    }

    const endpointMetrics = systemMetrics.endpoints[endpoint];
    endpointMetrics.requestCount++;
    endpointMetrics.responseTimeSum += responseTime;
    endpointMetrics.avgResponseTime = endpointMetrics.responseTimeSum / endpointMetrics.requestCount;

    if (res.statusCode >= 400) {
      endpointMetrics.errorCount++;
    }

    // Log performance metrics
    req.logger.info('Request completed', {
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      responseTime,
      userAgent: req.get('User-Agent'),
      component: 'performance'
    });

    // Alert on slow requests
    if (responseTime > 5000) {
      createAlert('WARNING', 'Slow Request', `Request to ${endpoint} took ${responseTime}ms`, {
        endpoint,
        responseTime,
        correlationId: req.correlationId
      });
    }
  });

  next();
});

// Middleware
app.use(cors());
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.json());

// Error handling middleware for JSON parsing
app.use((error, req, res, next) => {
  if (error instanceof SyntaxError && error.status === 400 && 'body' in error) {
    req.logger.error('JSON parsing error', {
      error: error.message,
      body: req.body,
      component: 'middleware'
    });

    return res.status(400).json({
      success: false,
      data: null,
      message: "Invalid JSON in request body",
      timestamp: new Date().toISOString(),
      correlationId: req.correlationId
    });
  }
  next();
});

// Alert creation function
function createAlert(severity, title, message, metadata = {}) {
  const alert = {
    id: uuidv4(),
    severity,
    title,
    message,
    timestamp: new Date().toISOString(),
    metadata,
    resolved: false
  };

  systemMetrics.alerts.push(alert);

  // Keep only last 100 alerts
  if (systemMetrics.alerts.length > 100) {
    systemMetrics.alerts = systemMetrics.alerts.slice(-100);
  }

  logger.warn('Alert created', {
    alertId: alert.id,
    severity,
    title,
    message,
    metadata,
    component: 'alerting'
  });

  return alert;
}

// Health check functions
function checkSystemHealth() {
  const uptime = Date.now() - systemMetrics.startTime;
  const avgResponseTime = systemMetrics.requestCount > 0 ?
    systemMetrics.responseTimeSum / systemMetrics.requestCount : 0;
  const errorRate = systemMetrics.requestCount > 0 ?
    (systemMetrics.errorCount / systemMetrics.requestCount) * 100 : 0;

  let status = 'HEALTHY';
  const issues = [];

  if (avgResponseTime > 2000) {
    status = 'DEGRADED';
    issues.push(`High average response time: ${avgResponseTime.toFixed(2)}ms`);
  }

  if (errorRate > 10) {
    status = 'UNHEALTHY';
    issues.push(`High error rate: ${errorRate.toFixed(2)}%`);
  }

  if (avgResponseTime > 5000 || errorRate > 25) {
    status = 'CRITICAL';
  }

  return {
    name: 'system_performance',
    status,
    message: issues.length > 0 ? issues.join('; ') : 'System performance normal',
    responseTimeMs: 0,
    metadata: {
      uptime,
      avgResponseTime: avgResponseTime.toFixed(2),
      errorRate: errorRate.toFixed(2),
      requestCount: systemMetrics.requestCount,
      errorCount: systemMetrics.errorCount
    }
  };
}

function checkMemoryUsage() {
  const memUsage = process.memoryUsage();
  const memUsageMB = {
    rss: Math.round(memUsage.rss / 1024 / 1024),
    heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
    heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
    external: Math.round(memUsage.external / 1024 / 1024)
  };

  let status = 'HEALTHY';
  const issues = [];

  if (memUsageMB.heapUsed > 500) {
    status = 'DEGRADED';
    issues.push(`High heap usage: ${memUsageMB.heapUsed}MB`);
  }

  if (memUsageMB.heapUsed > 1000) {
    status = 'UNHEALTHY';
    issues.push(`Very high heap usage: ${memUsageMB.heapUsed}MB`);
  }

  if (memUsageMB.heapUsed > 1500) {
    status = 'CRITICAL';
  }

  return {
    name: 'memory_usage',
    status,
    message: issues.length > 0 ? issues.join('; ') : `Memory usage normal (${memUsageMB.heapUsed}MB heap)`,
    responseTimeMs: 0,
    metadata: memUsageMB
  };
}


function startMonitoring() {
  // Update health checks periodically
  setInterval(() => {
    systemMetrics.healthChecks.system_performance = checkSystemHealth();
    systemMetrics.healthChecks.memory_usage = checkMemoryUsage();

    // Create alerts for critical health issues
    Object.values(systemMetrics.healthChecks).forEach(check => {
      if (check.status === 'CRITICAL') {
        createAlert('CRITICAL', `Critical Health Check: ${check.name}`, check.message, {
          healthCheck: check.name,
          metadata: check.metadata
        });
      } else if (check.status === 'UNHEALTHY') {
        createAlert('ERROR', `Unhealthy System: ${check.name}`, check.message, {
          healthCheck: check.name,
          metadata: check.metadata
        });
      }
    });
  }, 30000); // Check every 30 seconds
}

// Only start monitoring if we're not testing
if (require.main === module) {
  startMonitoring();
}

// In-memory storage arrays for demo simplicity
let resourceInventory = [];
let costOptimizations = [];
let costAnomalies = [];
let budgetForecasts = [];
let savingsRecords = [];
let pricingRecommendations = [];

// Enhanced health check endpoint with comprehensive monitoring
app.get("/health", (req, res) => {
  res.status(200).json({
    status: "ok",
    service: "advanced-finops-backend",
    timestamp: new Date().toISOString()
  });
});

// app.get("/health", (req, res) => {
//   const healthChecks = {
//     system_performance: checkSystemHealth(),
//     memory_usage: checkMemoryUsage()
//   };

//   const overallStatus = Object.values(healthChecks).some(check => check.status === 'CRITICAL') ? 'CRITICAL' :
//     Object.values(healthChecks).some(check => check.status === 'UNHEALTHY') ? 'UNHEALTHY' :
//       Object.values(healthChecks).some(check => check.status === 'DEGRADED') ? 'DEGRADED' : 'HEALTHY';

//   const uptime = Date.now() - systemMetrics.startTime;

//   req.logger.info('Health check requested', {
//     overallStatus,
//     uptime,
//     component: 'health'
//   });

//   res.json({
//     success: true,
//     data: {
//       status: overallStatus,
//       port: 5000,
//       uptime: Math.floor(uptime / 1000), // seconds
//       uptimeHuman: formatUptime(uptime),
//       healthChecks,
//       metrics: {
//         requestCount: systemMetrics.requestCount,
//         errorCount: systemMetrics.errorCount,
//         errorRate: systemMetrics.requestCount > 0 ?
//           ((systemMetrics.errorCount / systemMetrics.requestCount) * 100).toFixed(2) + '%' : '0%',
//         avgResponseTime: systemMetrics.requestCount > 0 ?
//           (systemMetrics.responseTimeSum / systemMetrics.requestCount).toFixed(2) + 'ms' : '0ms'
//       }
//     },
//     message: `Advanced FinOps Platform API is ${overallStatus.toLowerCase()}`,
//     timestamp: new Date().toISOString(),
//     correlationId: req.correlationId
//   });
// });

app.get("/status", (req, res) => {
  const healthChecks = {
    system_performance: checkSystemHealth(),
    memory_usage: checkMemoryUsage()
  };

  res.json({
    success: true,
    data: {
      status: "informational",
      healthChecks,
      metrics: systemMetrics,
      uptime: Math.floor((Date.now() - systemMetrics.startTime) / 1000)
    },
    timestamp: new Date().toISOString()
  });
});


// System monitoring dashboard endpoint
app.get("/api/monitoring/dashboard", (req, res) => {
  const uptime = Date.now() - systemMetrics.startTime;
  const avgResponseTime = systemMetrics.requestCount > 0 ?
    systemMetrics.responseTimeSum / systemMetrics.requestCount : 0;

  req.logger.info('Monitoring dashboard requested', { component: 'monitoring' });

  res.json({
    success: true,
    data: {
      timestamp: new Date().toISOString(),
      uptime: {
        milliseconds: uptime,
        seconds: Math.floor(uptime / 1000),
        human: formatUptime(uptime)
      },
      performance: {
        requestCount: systemMetrics.requestCount,
        errorCount: systemMetrics.errorCount,
        errorRate: systemMetrics.requestCount > 0 ?
          (systemMetrics.errorCount / systemMetrics.requestCount) * 100 : 0,
        avgResponseTime: avgResponseTime,
        endpoints: systemMetrics.endpoints
      },
      healthChecks: systemMetrics.healthChecks,
      alerts: {
        total: systemMetrics.alerts.length,
        active: systemMetrics.alerts.filter(a => !a.resolved).length,
        bySeverity: {
          CRITICAL: systemMetrics.alerts.filter(a => !a.resolved && a.severity === 'CRITICAL').length,
          ERROR: systemMetrics.alerts.filter(a => !a.resolved && a.severity === 'ERROR').length,
          WARNING: systemMetrics.alerts.filter(a => !a.resolved && a.severity === 'WARNING').length,
          INFO: systemMetrics.alerts.filter(a => !a.resolved && a.severity === 'INFO').length
        },
        recent: systemMetrics.alerts.slice(-10)
      },
      system: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
        memory: process.memoryUsage(),
        pid: process.pid
      }
    },
    message: "Monitoring dashboard data",
    timestamp: new Date().toISOString(),
    correlationId: req.correlationId
  });
});

// Alerts management endpoints
app.get("/api/monitoring/alerts", (req, res) => {
  const { severity, resolved } = req.query;
  let alerts = systemMetrics.alerts;

  if (severity) {
    alerts = alerts.filter(a => a.severity === severity.toUpperCase());
  }

  if (resolved !== undefined) {
    const isResolved = resolved === 'true';
    alerts = alerts.filter(a => a.resolved === isResolved);
  }

  req.logger.info('Alerts requested', {
    severity,
    resolved,
    alertCount: alerts.length,
    component: 'alerts'
  });

  res.json({
    success: true,
    data: {
      alerts: alerts.slice(-50), // Last 50 alerts
      summary: {
        total: systemMetrics.alerts.length,
        active: systemMetrics.alerts.filter(a => !a.resolved).length,
        resolved: systemMetrics.alerts.filter(a => a.resolved).length
      }
    },
    message: `Retrieved ${alerts.length} alerts`,
    timestamp: new Date().toISOString(),
    correlationId: req.correlationId
  });
});

app.post("/api/monitoring/alerts/:alertId/resolve", (req, res) => {
  const { alertId } = req.params;
  const alert = systemMetrics.alerts.find(a => a.id === alertId);

  if (!alert) {
    req.logger.warn('Alert not found for resolution', { alertId, component: 'alerts' });
    return res.status(404).json({
      success: false,
      data: null,
      message: `Alert ${alertId} not found`,
      timestamp: new Date().toISOString(),
      correlationId: req.correlationId
    });
  }

  alert.resolved = true;
  alert.resolvedAt = new Date().toISOString();
  alert.resolvedBy = req.body.resolvedBy || 'system';

  req.logger.info('Alert resolved', {
    alertId,
    resolvedBy: alert.resolvedBy,
    component: 'alerts'
  });

  res.json({
    success: true,
    data: alert,
    message: `Alert ${alertId} resolved`,
    timestamp: new Date().toISOString(),
    correlationId: req.correlationId
  });
});

// Metrics endpoint
app.get("/api/monitoring/metrics", (req, res) => {
  const { timeWindow } = req.query;
  const uptime = Date.now() - systemMetrics.startTime;

  req.logger.info('Metrics requested', { timeWindow, component: 'metrics' });

  res.json({
    success: true,
    data: {
      timestamp: new Date().toISOString(),
      timeWindow: timeWindow || 'all',
      global: {
        uptime: uptime,
        requestCount: systemMetrics.requestCount,
        errorCount: systemMetrics.errorCount,
        errorRate: systemMetrics.requestCount > 0 ?
          (systemMetrics.errorCount / systemMetrics.requestCount) * 100 : 0,
        avgResponseTime: systemMetrics.requestCount > 0 ?
          systemMetrics.responseTimeSum / systemMetrics.requestCount : 0,
        requestsPerSecond: systemMetrics.requestCount / (uptime / 1000)
      },
      endpoints: systemMetrics.endpoints,
      healthChecks: systemMetrics.healthChecks
    },
    message: "System metrics",
    timestamp: new Date().toISOString(),
    correlationId: req.correlationId
  });
});

// Utility function to format uptime
function formatUptime(uptimeMs) {
  const seconds = Math.floor(uptimeMs / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d ${hours % 24}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

// Import route modules
const apiRoutes = require('./routes/index');
const resourceRoutes = require('./routes/resources');
const optimizationRoutes = require('./routes/optimizations');
const budgetRoutes = require('./routes/budgets');
const anomalyRoutes = require('./routes/anomalies');
const savingsRoutes = require('./routes/savings');
const pricingRoutes = require('./routes/pricing');
const dashboardRoutes = require('./routes/dashboard');
const integrationRoutes = require('./routes/integration');

// Use routes
app.use('/api', apiRoutes);
app.use('/api/resources', resourceRoutes);
app.use('/api/optimizations', optimizationRoutes);
app.use('/api/budgets', budgetRoutes);
app.use('/api/anomalies', anomalyRoutes);
app.use('/api/savings', savingsRoutes);
app.use('/api/pricing', pricingRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/integration', integrationRoutes);

// Mount integration routes directly for Python bot endpoints
app.use('/api/optimization-analysis', integrationRoutes);
app.use('/api/anomaly-analysis', integrationRoutes);
app.use('/api/budget-analysis', integrationRoutes);
app.use('/api/execution-results', integrationRoutes);
app.use('/api/reports', integrationRoutes);

// Global error handler with enhanced logging and monitoring
app.use((error, req, res, next) => {
  const errorId = uuidv4();

  // Create alert for server errors
  if (error.status >= 500 || !error.status) {
    createAlert('ERROR', 'Server Error', error.message, {
      errorId,
      stack: error.stack,
      url: req.url,
      method: req.method,
      correlationId: req.correlationId
    });
  }

  req.logger.error('Global error handler', {
    errorId,
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method,
    userAgent: req.get('User-Agent'),
    component: 'error_handler'
  });

  const statusCode = error.status || 500;

  res.status(statusCode).json({
    success: false,
    data: null,
    message: process.env.NODE_ENV === 'production' ?
      "Internal server error" :
      `Internal server error: ${error.message}`,
    errorId,
    timestamp: new Date().toISOString(),
    correlationId: req.correlationId
  });
});

// 404 handler with enhanced logging
app.use((req, res) => {
  req.logger.warn('Endpoint not found', {
    method: req.method,
    url: req.url,
    userAgent: req.get('User-Agent'),
    component: 'not_found'
  });

  res.status(404).json({
    success: false,
    data: null,
    message: `Endpoint not found: ${req.method} ${req.path}`,
    timestamp: new Date().toISOString(),
    correlationId: req.correlationId
  });
});

const PORT = process.env.PORT || 5000;

// Enhanced broadcast function with monitoring
function broadcastUpdate(type, data) {
  const broadcastData = {
    type,
    data,
    timestamp: new Date().toISOString(),
    correlationId: uuidv4()
  };

  logger.info('Broadcasting update', {
    type,
    dataSize: JSON.stringify(data).length,
    correlationId: broadcastData.correlationId,
    component: 'broadcast'
  });

  // In a real implementation, this would use WebSockets or Server-Sent Events
  console.log(`📡 Broadcasting ${type} update:`, JSON.stringify(broadcastData, null, 2));
}


// Make enhanced broadcast function available globally
global.broadcastUpdate = broadcastUpdate;

// Export internal functions for testing
app.checkSystemHealth = checkSystemHealth;
app.checkMemoryUsage = checkMemoryUsage;
app.createAlert = createAlert;
app.broadcastUpdate = broadcastUpdate;
app.startMonitoring = startMonitoring;

// Graceful shutdown handling
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully', { component: 'shutdown' });

  // Create final system metrics snapshot
  const finalMetrics = {
    uptime: Date.now() - systemMetrics.startTime,
    totalRequests: systemMetrics.requestCount,
    totalErrors: systemMetrics.errorCount,
    endpoints: Object.keys(systemMetrics.endpoints).length,
    alerts: systemMetrics.alerts.length
  };

  logger.info('Final system metrics', finalMetrics);

  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully', { component: 'shutdown' });
  process.exit(0);
});

// Unhandled promise rejection handler
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Promise Rejection', {
    reason: reason.toString(),
    stack: reason.stack,
    component: 'unhandled_rejection'
  });

  createAlert('CRITICAL', 'Unhandled Promise Rejection', reason.toString(), {
    stack: reason.stack
  });
});

// Uncaught exception handler
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', {
    error: error.message,
    stack: error.stack,
    component: 'uncaught_exception'
  });

  createAlert('CRITICAL', 'Uncaught Exception', error.message, {
    stack: error.stack
  });

  // Exit after logging
  process.exit(1);
});


// Only start the server if we're not testing
if (require.main === module) {
  const server = app.listen(PORT, () => {
    logger.info('Advanced FinOps Platform Backend started', {
      port: PORT,
      nodeVersion: process.version,
      platform: process.platform,
      pid: process.pid,
      component: 'startup'
    });

    console.log(`🚀 Advanced FinOps Platform Backend running on port ${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`🔗 API Base URL: http://localhost:${PORT}/api`);
    console.log(`📊 Dashboard API: http://localhost:${PORT}/api/dashboard`);
    console.log(`💰 Savings API: http://localhost:${PORT}/api/savings`);
    console.log(`💲 Pricing API: http://localhost:${PORT}/api/pricing`);
    console.log(`📈 Monitoring Dashboard: http://localhost:${PORT}/api/monitoring/dashboard`);
    console.log(`🚨 Alerts API: http://localhost:${PORT}/api/monitoring/alerts`);
    console.log(`📊 Metrics API: http://localhost:${PORT}/api/monitoring/metrics`);
  });

  // Handle server errors
  server.on('error', (error) => {
    logger.error('Server error', {
      error: error.message,
      code: error.code,
      component: 'server'
    });

    createAlert('CRITICAL', 'Server Error', error.message, {
      code: error.code,
      stack: error.stack
    });
  });
}

// Export for testing
module.exports = app;