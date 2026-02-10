const express = require('express');
const router = express.Router();
const store = require('../store');

// Reference to shared store
const getAutoScalingGroups = () => store.autoScalingGroups;

/**
 * POST /api/auto-scaling-groups
 * Save Auto Scaling Group data
 */
router.post('/', (req, res) => {
  try {
    const {
      asg_name,
      asg_arn,
      region,
      min_size,
      max_size,
      desired_capacity,
      current_instances,
      instance_ids,
      health_check_type,
      metrics,
      hourly_cost,
      monthly_cost,
      annual_cost,
      instance_costs,
    } = req.body;

    // Validate required fields
    if (!asg_name || !asg_arn || !region) {
      return res.status(400).json({
        error: 'Missing required fields: asg_name, asg_arn, region',
      });
    }

    console.log(`📦 Received ASG: ${asg_name} in ${region}`);

    // Check if ASG already exists and update or create
    const autoScalingGroups = getAutoScalingGroups();
    const existingIndex = autoScalingGroups.findIndex(a => a.asg_arn === asg_arn);
    const asgData = {
      asg_name,
      asg_arn,
      region,
      min_size,
      max_size,
      desired_capacity,
      current_instances,
      instance_ids,
      health_check_type,
      metrics,
      hourly_cost,
      monthly_cost,
      annual_cost,
      instance_costs,
      timestamp: new Date(),
    };

    if (existingIndex >= 0) {
      autoScalingGroups[existingIndex] = asgData;
      console.log(`✅ Updated ASG: ${asg_name}`);
    } else {
      autoScalingGroups.push(asgData);
      console.log(`✅ Created ASG: ${asg_name}`);
    }

    res.status(201).json({
      status: 'success',
      message: 'ASG data saved',
      data: {
        asg_name,
        asg_arn,
        region,
      },
    });
  } catch (error) {
    console.error('❌ Error saving ASG data:', error);
    res.status(500).json({
      error: 'Failed to save ASG data',
      message: error.message,
    });
  }
});

/**
 * GET /api/auto-scaling-groups
 * Retrieve all Auto Scaling Groups
 */
router.get('/', (req, res) => {
  try {
    const autoScalingGroups = getAutoScalingGroups();
    console.log(`📤 Fetching ${autoScalingGroups.length} ASGs`);
    res.json({
      status: 'success',
      data: autoScalingGroups,
      total: autoScalingGroups.length,
    });
  } catch (error) {
    console.error('❌ Error fetching ASGs:', error);
    res.status(500).json({
      error: 'Failed to fetch ASGs',
      message: error.message,
    });
  }
});

/**
 * GET /api/auto-scaling-groups/:asgArn
 * Retrieve a specific Auto Scaling Group
 */
router.get('/:asgArn', (req, res) => {
  try {
    const { asgArn } = req.params;
    const autoScalingGroups = getAutoScalingGroups();
    const asg = autoScalingGroups.find(a => a.asg_arn === asgArn);

    if (!asg) {
      return res.status(404).json({
        error: 'ASG not found',
        asg_arn: asgArn,
      });
    }

    console.log(`📤 Fetching ASG: ${asgArn}`);
    res.json({
      status: 'success',
      data: asg,
    });
  } catch (error) {
    console.error('❌ Error fetching ASG:', error);
    res.status(500).json({
      error: 'Failed to fetch ASG',
      message: error.message,
    });
  }
});

module.exports = router;
