const express = require('express');
const router = express.Router();
const store = require('../store');

// Reference to shared store
const getRdsInstances = () => store.rdsInstances;

/**
 * POST /api/rds-instances
 * Save RDS instance data
 */
router.post('/', (req, res) => {
  try {
    const {
      db_instance_id,
      db_instance_arn,
      engine,
      engine_version,
      db_instance_class,
      region,
      status,
      allocated_storage_gb,
      storage_type,
      multi_az,
      backup_retention_days,
      publicly_accessible,
      read_replicas,
      metrics,
      instance_hourly_cost,
      storage_hourly_cost,
      hourly_cost,
      monthly_cost,
      annual_cost,
      tags,
    } = req.body;

    // Validate required fields
    if (!db_instance_id || !db_instance_arn || !region) {
      return res.status(400).json({
        error: 'Missing required fields: db_instance_id, db_instance_arn, region',
      });
    }

    console.log(`📦 Received RDS instance: ${db_instance_id} in ${region}`);

    // Check if RDS instance already exists and update or create
    const rdsInstances = getRdsInstances();
    const existingIndex = rdsInstances.findIndex(
      r => r.db_instance_id === db_instance_id
    );
    const rdsData = {
      db_instance_id,
      db_instance_arn,
      engine,
      engine_version,
      db_instance_class,
      region,
      status,
      allocated_storage_gb,
      storage_type,
      multi_az,
      backup_retention_days,
      publicly_accessible,
      read_replicas,
      metrics,
      instance_hourly_cost,
      storage_hourly_cost,
      hourly_cost,
      monthly_cost,
      annual_cost,
      tags,
      timestamp: new Date(),
    };

    if (existingIndex >= 0) {
      rdsInstances[existingIndex] = rdsData;
      console.log(`✅ Updated RDS instance: ${db_instance_id}`);
    } else {
      rdsInstances.push(rdsData);
      console.log(`✅ Created RDS instance: ${db_instance_id}`);
    }

    res.status(201).json({
      status: 'success',
      message: 'RDS instance data saved',
      data: {
        db_instance_id,
        db_instance_arn,
        region,
      },
    });
  } catch (error) {
    console.error('❌ Error saving RDS instance data:', error);
    res.status(500).json({
      error: 'Failed to save RDS instance data',
      message: error.message,
    });
  }
});

/**
 * GET /api/rds-instances
 * Retrieve all RDS instances
 */
router.get('/', (req, res) => {
  try {
    const rdsInstances = getRdsInstances();
    console.log(`📤 Fetching ${rdsInstances.length} RDS instances`);
    res.json({
      status: 'success',
      data: rdsInstances,
      total: rdsInstances.length,
    });
  } catch (error) {
    console.error('❌ Error fetching RDS instances:', error);
    res.status(500).json({
      error: 'Failed to fetch RDS instances',
      message: error.message,
    });
  }
});

/**
 * GET /api/rds-instances/:dbInstanceId
 * Retrieve a specific RDS instance
 */
router.get('/:dbInstanceId', (req, res) => {
  try {
    const { dbInstanceId } = req.params;
    const rdsInstances = getRdsInstances();
    const rds = rdsInstances.find(r => r.db_instance_id === dbInstanceId);

    if (!rds) {
      return res.status(404).json({
        error: 'RDS instance not found',
        db_instance_id: dbInstanceId,
      });
    }

    console.log(`📤 Fetching RDS instance: ${dbInstanceId}`);
    res.json({
      status: 'success',
      data: rds,
    });
  } catch (error) {
    console.error('❌ Error fetching RDS instance:', error);
    res.status(500).json({
      error: 'Failed to fetch RDS instance',
      message: error.message,
    });
  }
});

module.exports = router;
