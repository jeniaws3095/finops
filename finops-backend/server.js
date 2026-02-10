const express = require("express");
const cors = require("cors");

// Import route handlers
const instancesRoutes = require("./routes/instances");
const savingsRoutes = require("./routes/savings");
const loadBalancersRoutes = require("./routes/load-balancers");
const autoScalingGroupsRoutes = require("./routes/auto-scaling-groups");
const ebsVolumesRoutes = require("./routes/ebs-volumes");
const rdsInstancesRoutes = require("./routes/rds-instances");
const costingRoutes = require("./routes/costing");

const app = express();
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Reset endpoint - clears all data
app.post("/reset", (req, res) => {
  const store = require('./store');
  store.instances = [];
  store.savings = [];
  store.loadBalancers = [];
  store.autoScalingGroups = [];
  store.ebsVolumes = [];
  store.rdsInstances = [];
  
  console.log('🔄 Store reset - all data cleared');
  res.json({
    status: 'success',
    message: 'All data cleared',
    timestamp: new Date().toISOString()
  });
});

// API Routes
app.use("/api/instances", instancesRoutes);
app.use("/api/savings", savingsRoutes);
app.use("/api/load-balancers", loadBalancersRoutes);
app.use("/api/auto-scaling-groups", autoScalingGroupsRoutes);
app.use("/api/ebs-volumes", ebsVolumesRoutes);
app.use("/api/rds-instances", rdsInstancesRoutes);
app.use("/api/costing", costingRoutes);

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: "Not Found",
    path: req.path,
    method: req.method
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error("❌ Server error:", err);
  res.status(500).json({
    error: "Internal Server Error",
    message: err.message
  });
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log("\n" + "=".repeat(80));
  console.log("🚀 FinOps Backend Server Started");
  console.log("=".repeat(80));
  console.log(`\n📍 Server running on port ${PORT}`);
  console.log(`\n📋 Available Endpoints:\n`);
  console.log("  Health Check:");
  console.log(`    GET  http://localhost:${PORT}/health\n`);
  console.log("  🔄 RESIZE & RECOMMENDATIONS:");
  console.log(`    GET  http://localhost:${PORT}/api/instances/:instanceId/resize-options`);
  console.log(`    POST http://localhost:${PORT}/api/instances/:instanceId/resize\n`);
  console.log("  💰 SAVINGS & COST TRACKING:");
  console.log(`    POST http://localhost:${PORT}/api/savings`);
  console.log(`    GET  http://localhost:${PORT}/api/savings`);
  console.log(`    GET  http://localhost:${PORT}/api/savings/summary`);
  console.log(`    GET  http://localhost:${PORT}/api/costing/current`);
  console.log(`    GET  http://localhost:${PORT}/api/costing/by-region`);
  console.log(`    GET  http://localhost:${PORT}/api/costing/by-service\n`);
  console.log("  📊 RESOURCE MANAGEMENT:");
  console.log(`    POST http://localhost:${PORT}/api/instances`);
  console.log(`    GET  http://localhost:${PORT}/api/instances`);
  console.log(`    GET  http://localhost:${PORT}/api/instances/:instanceId`);
  console.log(`    POST http://localhost:${PORT}/api/load-balancers`);
  console.log(`    GET  http://localhost:${PORT}/api/load-balancers`);
  console.log(`    GET  http://localhost:${PORT}/api/load-balancers/:lbArn`);
  console.log(`    POST http://localhost:${PORT}/api/auto-scaling-groups`);
  console.log(`    GET  http://localhost:${PORT}/api/auto-scaling-groups`);
  console.log(`    GET  http://localhost:${PORT}/api/auto-scaling-groups/:asgArn`);
  console.log(`    POST http://localhost:${PORT}/api/ebs-volumes`);
  console.log(`    GET  http://localhost:${PORT}/api/ebs-volumes`);
  console.log(`    GET  http://localhost:${PORT}/api/ebs-volumes/:volumeId`);
  console.log(`    POST http://localhost:${PORT}/api/rds-instances`);
  console.log(`    GET  http://localhost:${PORT}/api/rds-instances`);
  console.log(`    GET  http://localhost:${PORT}/api/rds-instances/:dbInstanceId\n`);
  console.log("=".repeat(80) + "\n");
});

module.exports = app;
