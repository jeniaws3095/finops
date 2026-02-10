const express = require('express');
const router = express.Router();
const store = require('../store');

// Reference to shared store
const getInstances = () => store.instances;

/**
 * POST /api/instances
 * Save EC2 instance data from the bot
 */
router.post('/', (req, res) => {
  try {
    const {
      instance_id,
      state,
      region,
      cpu,
      instance_type,
      hourly_cost,
      monthly_cost,
      annual_cost,
    } = req.body;

    // Validate required fields
    if (!instance_id || !region || !instance_type) {
      return res.status(400).json({
        error: 'Missing required fields: instance_id, region, instance_type',
      });
    }

    console.log(`📦 Received EC2 instance: ${instance_id} in ${region}`);

    // Check if instance already exists and update or create
    const instances = getInstances();
    const existingIndex = instances.findIndex(i => i.instance_id === instance_id);
    const instanceData = {
      instance_id,
      state,
      region,
      cpu,
      instance_type,
      hourly_cost,
      monthly_cost,
      annual_cost,
      timestamp: new Date(),
    };

    if (existingIndex >= 0) {
      instances[existingIndex] = instanceData;
      console.log(`✅ Updated instance: ${instance_id}`);
    } else {
      instances.push(instanceData);
      console.log(`✅ Created instance: ${instance_id}`);
    }

    res.status(201).json({
      status: 'success',
      message: 'Instance data saved',
      data: {
        instance_id,
        region,
        instance_type,
      },
    });
  } catch (error) {
    console.error('❌ Error saving instance data:', error);
    res.status(500).json({
      error: 'Failed to save instance data',
      message: error.message,
    });
  }
});

/**
 * GET /api/instances
 * Retrieve all EC2 instances
 */
router.get('/', (req, res) => {
  try {
    const instances = getInstances();
    console.log(`📤 Fetching ${instances.length} instances`);
    res.json({
      status: 'success',
      data: instances,
      total: instances.length,
    });
  } catch (error) {
    console.error('❌ Error fetching instances:', error);
    res.status(500).json({
      error: 'Failed to fetch instances',
      message: error.message,
    });
  }
});

/**
 * GET /api/instances/:instanceId
 * Retrieve a specific EC2 instance
 */
router.get('/:instanceId', (req, res) => {
  try {
    const { instanceId } = req.params;
    const instances = getInstances();
    const instance = instances.find(i => i.instance_id === instanceId);

    if (!instance) {
      return res.status(404).json({
        error: 'Instance not found',
        instance_id: instanceId,
      });
    }

    console.log(`📤 Fetching instance: ${instanceId}`);
    res.json({
      status: 'success',
      data: instance,
    });
  } catch (error) {
    console.error('❌ Error fetching instance:', error);
    res.status(500).json({
      error: 'Failed to fetch instance',
      message: error.message,
    });
  }
});

/**
 * POST /api/instances/:instanceId/resize
 * Resize an EC2 instance to a smaller type
 */
router.post('/:instanceId/resize', (req, res) => {
  try {
    const { instanceId } = req.params;
    const { new_instance_type, approval_request_id } = req.body;

    // Validate required fields
    if (!new_instance_type) {
      return res.status(400).json({
        error: 'Missing required field: new_instance_type',
      });
    }

    const instances = getInstances();
    const instance = instances.find(i => i.instance_id === instanceId);

    if (!instance) {
      return res.status(404).json({
        error: 'Instance not found',
        instance_id: instanceId,
      });
    }

    const currentType = instance.instance_type;
    const currentMonthlyCost = instance.monthly_cost || 0;

    // Downsizing hierarchy for common instance families
    const downsizingMap = {
      // t2 family
      't2.2xlarge': ['t2.xlarge', 't2.large', 't2.medium'],
      't2.xlarge': ['t2.large', 't2.medium', 't2.small'],
      't2.large': ['t2.medium', 't2.small', 't2.micro'],
      't2.medium': ['t2.small', 't2.micro'],
      't2.small': ['t2.micro'],
      
      // t3 family
      't3.2xlarge': ['t3.xlarge', 't3.large', 't3.medium'],
      't3.xlarge': ['t3.large', 't3.medium', 't3.small'],
      't3.large': ['t3.medium', 't3.small', 't3.micro'],
      't3.medium': ['t3.small', 't3.micro'],
      't3.small': ['t3.micro'],
      
      // t4g family (Graviton2)
      't4g.2xlarge': ['t4g.xlarge', 't4g.large', 't4g.medium'],
      't4g.xlarge': ['t4g.large', 't4g.medium', 't4g.small'],
      't4g.large': ['t4g.medium', 't4g.small', 't4g.micro'],
      't4g.medium': ['t4g.small', 't4g.micro'],
      't4g.small': ['t4g.micro'],
      
      // m5 family
      'm5.2xlarge': ['m5.xlarge', 'm5.large'],
      'm5.xlarge': ['m5.large'],
      
      // m6g family (Graviton2)
      'm6g.16xlarge': ['m6g.12xlarge', 'm6g.8xlarge'],
      'm6g.12xlarge': ['m6g.8xlarge', 'm6g.4xlarge'],
      'm6g.8xlarge': ['m6g.4xlarge', 'm6g.2xlarge'],
      'm6g.4xlarge': ['m6g.2xlarge', 'm6g.xlarge'],
      'm6g.2xlarge': ['m6g.xlarge', 'm6g.large'],
      'm6g.xlarge': ['m6g.large'],
      
      // m7g family (Graviton3)
      'm7g.16xlarge': ['m7g.12xlarge', 'm7g.8xlarge'],
      'm7g.12xlarge': ['m7g.8xlarge', 'm7g.4xlarge'],
      'm7g.8xlarge': ['m7g.4xlarge', 'm7g.2xlarge'],
      'm7g.4xlarge': ['m7g.2xlarge', 'm7g.xlarge'],
      'm7g.2xlarge': ['m7g.xlarge', 'm7g.large'],
      'm7g.xlarge': ['m7g.large'],
      
      // c5 family
      'c5.2xlarge': ['c5.xlarge', 'c5.large'],
      'c5.xlarge': ['c5.large'],
      
      // c6g family (Graviton2)
      'c6g.16xlarge': ['c6g.12xlarge', 'c6g.8xlarge'],
      'c6g.12xlarge': ['c6g.8xlarge', 'c6g.4xlarge'],
      'c6g.8xlarge': ['c6g.4xlarge', 'c6g.2xlarge'],
      'c6g.4xlarge': ['c6g.2xlarge', 'c6g.xlarge'],
      'c6g.2xlarge': ['c6g.xlarge', 'c6g.large'],
      'c6g.xlarge': ['c6g.large'],
      
      // c7g family (Graviton3)
      'c7g.16xlarge': ['c7g.12xlarge', 'c7g.8xlarge'],
      'c7g.12xlarge': ['c7g.8xlarge', 'c7g.4xlarge'],
      'c7g.8xlarge': ['c7g.4xlarge', 'c7g.2xlarge'],
      'c7g.4xlarge': ['c7g.2xlarge', 'c7g.xlarge'],
      'c7g.2xlarge': ['c7g.xlarge', 'c7g.large'],
      'c7g.xlarge': ['c7g.large'],
      
      // r6g family (Graviton2)
      'r6g.16xlarge': ['r6g.12xlarge', 'r6g.8xlarge'],
      'r6g.12xlarge': ['r6g.8xlarge', 'r6g.4xlarge'],
      'r6g.8xlarge': ['r6g.4xlarge', 'r6g.2xlarge'],
      'r6g.4xlarge': ['r6g.2xlarge', 'r6g.xlarge'],
      'r6g.2xlarge': ['r6g.xlarge', 'r6g.large'],
      'r6g.xlarge': ['r6g.large'],
      
      // r7g family (Graviton3)
      'r7g.16xlarge': ['r7g.12xlarge', 'r7g.8xlarge'],
      'r7g.12xlarge': ['r7g.8xlarge', 'r7g.4xlarge'],
      'r7g.8xlarge': ['r7g.4xlarge', 'r7g.2xlarge'],
      'r7g.4xlarge': ['r7g.2xlarge', 'r7g.xlarge'],
      'r7g.2xlarge': ['r7g.xlarge', 'r7g.large'],
      'r7g.xlarge': ['r7g.large'],
    };

    // Check if current type can be downsized
    const availableOptions = downsizingMap[currentType] || [];
    
    if (availableOptions.length === 0) {
      return res.status(400).json({
        error: 'Instance type cannot be downsized',
        current_instance_type: currentType,
        message: 'Instance is already at the smallest available type or downsizing is not supported',
      });
    }

    // Validate new instance type is in available options
    if (!availableOptions.includes(new_instance_type)) {
      return res.status(400).json({
        error: 'Invalid resize target',
        current_instance_type: currentType,
        requested_type: new_instance_type,
        available_options: availableOptions,
      });
    }

    // Estimate cost savings (simplified - in production, use pricing API)
    const costReductionPercent = {
      't2.micro': 0.5, 't2.small': 0.6, 't2.medium': 0.7, 't2.large': 0.8,
      't3.micro': 0.5, 't3.small': 0.6, 't3.medium': 0.7, 't3.large': 0.8,
      't4g.micro': 0.5, 't4g.small': 0.6, 't4g.medium': 0.7, 't4g.large': 0.8,
      'm5.large': 0.7, 'm5.xlarge': 0.8,
      'm6g.large': 0.7, 'm6g.xlarge': 0.8,
      'm7g.large': 0.7, 'm7g.xlarge': 0.8,
      'c5.large': 0.7, 'c5.xlarge': 0.8,
      'c6g.large': 0.7, 'c6g.xlarge': 0.8,
      'c7g.large': 0.7, 'c7g.xlarge': 0.8,
      'r6g.large': 0.7, 'r6g.xlarge': 0.8,
      'r7g.large': 0.7, 'r7g.xlarge': 0.8,
    };

    const reductionPercent = costReductionPercent[new_instance_type] || 0.5;
    const estimatedMonthlySavings = currentMonthlyCost * (1 - reductionPercent);
    const estimatedAnnualSavings = estimatedMonthlySavings * 12;

    console.log(`🔄 Resize request: ${instanceId} from ${currentType} to ${new_instance_type}`);

    res.status(200).json({
      status: 'success',
      message: 'Resize request processed',
      data: {
        instance_id: instanceId,
        current_instance_type: currentType,
        new_instance_type: new_instance_type,
        current_monthly_cost: parseFloat(currentMonthlyCost.toFixed(2)),
        estimated_monthly_cost: parseFloat((currentMonthlyCost * reductionPercent).toFixed(2)),
        estimated_monthly_savings: parseFloat(estimatedMonthlySavings.toFixed(2)),
        estimated_annual_savings: parseFloat(estimatedAnnualSavings.toFixed(2)),
        approval_request_id: approval_request_id || null,
        status: approval_request_id ? 'pending_approval' : 'ready_for_approval',
        downtime_estimate: '2-5 minutes',
        timestamp: new Date().toISOString(),
      },
    });
  } catch (error) {
    console.error('❌ Error processing resize request:', error);
    res.status(500).json({
      error: 'Failed to process resize request',
      message: error.message,
    });
  }
});

/**
 * GET /api/instances/:instanceId/resize-options
 * Get available resize options for an EC2 instance
 */
router.get('/:instanceId/resize-options', (req, res) => {
  try {
    const { instanceId } = req.params;
    const instances = getInstances();
    const instance = instances.find(i => i.instance_id === instanceId);

    if (!instance) {
      return res.status(404).json({
        error: 'Instance not found',
        instance_id: instanceId,
      });
    }

    const currentType = instance.instance_type;
    const currentMonthlyCost = instance.monthly_cost || 0;

    // Downsizing hierarchy
    const downsizingMap = {
      't2.2xlarge': ['t2.xlarge', 't2.large', 't2.medium'],
      't2.xlarge': ['t2.large', 't2.medium', 't2.small'],
      't2.large': ['t2.medium', 't2.small', 't2.micro'],
      't2.medium': ['t2.small', 't2.micro'],
      't2.small': ['t2.micro'],
      't3.2xlarge': ['t3.xlarge', 't3.large', 't3.medium'],
      't3.xlarge': ['t3.large', 't3.medium', 't3.small'],
      't3.large': ['t3.medium', 't3.small', 't3.micro'],
      't3.medium': ['t3.small', 't3.micro'],
      't3.small': ['t3.micro'],
      't4g.2xlarge': ['t4g.xlarge', 't4g.large', 't4g.medium'],
      't4g.xlarge': ['t4g.large', 't4g.medium', 't4g.small'],
      't4g.large': ['t4g.medium', 't4g.small', 't4g.micro'],
      't4g.medium': ['t4g.small', 't4g.micro'],
      't4g.small': ['t4g.micro'],
      'm5.2xlarge': ['m5.xlarge', 'm5.large'],
      'm5.xlarge': ['m5.large'],
      'm6g.16xlarge': ['m6g.12xlarge', 'm6g.8xlarge'],
      'm6g.12xlarge': ['m6g.8xlarge', 'm6g.4xlarge'],
      'm6g.8xlarge': ['m6g.4xlarge', 'm6g.2xlarge'],
      'm6g.4xlarge': ['m6g.2xlarge', 'm6g.xlarge'],
      'm6g.2xlarge': ['m6g.xlarge', 'm6g.large'],
      'm6g.xlarge': ['m6g.large'],
      'm7g.16xlarge': ['m7g.12xlarge', 'm7g.8xlarge'],
      'm7g.12xlarge': ['m7g.8xlarge', 'm7g.4xlarge'],
      'm7g.8xlarge': ['m7g.4xlarge', 'm7g.2xlarge'],
      'm7g.4xlarge': ['m7g.2xlarge', 'm7g.xlarge'],
      'm7g.2xlarge': ['m7g.xlarge', 'm7g.large'],
      'm7g.xlarge': ['m7g.large'],
      'c5.2xlarge': ['c5.xlarge', 'c5.large'],
      'c5.xlarge': ['c5.large'],
      'c6g.16xlarge': ['c6g.12xlarge', 'c6g.8xlarge'],
      'c6g.12xlarge': ['c6g.8xlarge', 'c6g.4xlarge'],
      'c6g.8xlarge': ['c6g.4xlarge', 'c6g.2xlarge'],
      'c6g.4xlarge': ['c6g.2xlarge', 'c6g.xlarge'],
      'c6g.2xlarge': ['c6g.xlarge', 'c6g.large'],
      'c6g.xlarge': ['c6g.large'],
      'c7g.16xlarge': ['c7g.12xlarge', 'c7g.8xlarge'],
      'c7g.12xlarge': ['c7g.8xlarge', 'c7g.4xlarge'],
      'c7g.8xlarge': ['c7g.4xlarge', 'c7g.2xlarge'],
      'c7g.4xlarge': ['c7g.2xlarge', 'c7g.xlarge'],
      'c7g.2xlarge': ['c7g.xlarge', 'c7g.large'],
      'c7g.xlarge': ['c7g.large'],
      'r6g.16xlarge': ['r6g.12xlarge', 'r6g.8xlarge'],
      'r6g.12xlarge': ['r6g.8xlarge', 'r6g.4xlarge'],
      'r6g.8xlarge': ['r6g.4xlarge', 'r6g.2xlarge'],
      'r6g.4xlarge': ['r6g.2xlarge', 'r6g.xlarge'],
      'r6g.2xlarge': ['r6g.xlarge', 'r6g.large'],
      'r6g.xlarge': ['r6g.large'],
      'r7g.16xlarge': ['r7g.12xlarge', 'r7g.8xlarge'],
      'r7g.12xlarge': ['r7g.8xlarge', 'r7g.4xlarge'],
      'r7g.8xlarge': ['r7g.4xlarge', 'r7g.2xlarge'],
      'r7g.4xlarge': ['r7g.2xlarge', 'r7g.xlarge'],
      'r7g.2xlarge': ['r7g.xlarge', 'r7g.large'],
      'r7g.xlarge': ['r7g.large'],
    };

    const costReductionPercent = {
      't2.micro': 0.5, 't2.small': 0.6, 't2.medium': 0.7, 't2.large': 0.8,
      't3.micro': 0.5, 't3.small': 0.6, 't3.medium': 0.7, 't3.large': 0.8,
      't4g.micro': 0.5, 't4g.small': 0.6, 't4g.medium': 0.7, 't4g.large': 0.8,
      'm5.large': 0.7, 'm5.xlarge': 0.8,
      'm6g.large': 0.7, 'm6g.xlarge': 0.8,
      'm7g.large': 0.7, 'm7g.xlarge': 0.8,
      'c5.large': 0.7, 'c5.xlarge': 0.8,
      'c6g.large': 0.7, 'c6g.xlarge': 0.8,
      'c7g.large': 0.7, 'c7g.xlarge': 0.8,
      'r6g.large': 0.7, 'r6g.xlarge': 0.8,
      'r7g.large': 0.7, 'r7g.xlarge': 0.8,
    };

    const availableOptions = downsizingMap[currentType] || [];
    
    const resizeOptions = availableOptions.map(targetType => {
      const reductionPercent = costReductionPercent[targetType] || 0.5;
      const targetMonthlyCost = currentMonthlyCost * reductionPercent;
      const savings = currentMonthlyCost - targetMonthlyCost;
      
      return {
        target_instance_type: targetType,
        current_monthly_cost: parseFloat(currentMonthlyCost.toFixed(2)),
        target_monthly_cost: parseFloat(targetMonthlyCost.toFixed(2)),
        estimated_monthly_savings: parseFloat(savings.toFixed(2)),
        estimated_annual_savings: parseFloat((savings * 12).toFixed(2)),
        savings_percentage: parseFloat(((savings / currentMonthlyCost) * 100).toFixed(2)),
        downtime_estimate: '2-5 minutes',
      };
    });

    console.log(`📊 Fetching resize options for: ${instanceId}`);

    res.json({
      status: 'success',
      data: {
        instance_id: instanceId,
        current_instance_type: currentType,
        current_monthly_cost: parseFloat(currentMonthlyCost.toFixed(2)),
        current_annual_cost: parseFloat((currentMonthlyCost * 12).toFixed(2)),
        resize_available: availableOptions.length > 0,
        resize_options: resizeOptions,
        total_options: resizeOptions.length,
      },
    });
  } catch (error) {
    console.error('❌ Error fetching resize options:', error);
    res.status(500).json({
      error: 'Failed to fetch resize options',
      message: error.message,
    });
  }
});

module.exports = router;
