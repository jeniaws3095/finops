const express = require('express');
const router = express.Router();
const store = require('../store');

// Reference to shared store
const getLoadBalancers = () => store.loadBalancers;

/**
 * POST /api/load-balancers
 * Save load balancer data
 */
router.post('/', (req, res) => {
  try {
    const {
      load_balancer_name,
      load_balancer_arn,
      load_balancer_type,
      region,
      state,
      scheme,
      vpc_id,
      metrics,
      hourly_cost,
      monthly_cost,
      annual_cost,
    } = req.body;

    // Validate required fields
    if (!load_balancer_name || !load_balancer_arn || !region) {
      return res.status(400).json({
        error: 'Missing required fields: load_balancer_name, load_balancer_arn, region',
      });
    }

    console.log(`📦 Received load balancer: ${load_balancer_name} in ${region}`);

    // Check if load balancer already exists and update or create
    const loadBalancers = getLoadBalancers();
    const existingIndex = loadBalancers.findIndex(
      lb => lb.load_balancer_arn === load_balancer_arn
    );
    const lbData = {
      load_balancer_name,
      load_balancer_arn,
      load_balancer_type,
      region,
      state,
      scheme,
      vpc_id,
      metrics,
      hourly_cost,
      monthly_cost,
      annual_cost,
      timestamp: new Date(),
    };

    if (existingIndex >= 0) {
      loadBalancers[existingIndex] = lbData;
      console.log(`✅ Updated load balancer: ${load_balancer_name}`);
    } else {
      loadBalancers.push(lbData);
      console.log(`✅ Created load balancer: ${load_balancer_name}`);
    }

    res.status(201).json({
      status: 'success',
      message: 'Load balancer data saved',
      data: {
        load_balancer_name,
        load_balancer_arn,
        region,
      },
    });
  } catch (error) {
    console.error('❌ Error saving load balancer data:', error);
    res.status(500).json({
      error: 'Failed to save load balancer data',
      message: error.message,
    });
  }
});

/**
 * GET /api/load-balancers
 * Retrieve all load balancers
 */
router.get('/', (req, res) => {
  try {
    const loadBalancers = getLoadBalancers();
    console.log(`📤 Fetching ${loadBalancers.length} load balancers`);
    res.json({
      status: 'success',
      data: loadBalancers,
      total: loadBalancers.length,
    });
  } catch (error) {
    console.error('❌ Error fetching load balancers:', error);
    res.status(500).json({
      error: 'Failed to fetch load balancers',
      message: error.message,
    });
  }
});

/**
 * GET /api/load-balancers/:lbArn
 * Retrieve a specific load balancer
 */
router.get('/:lbArn', (req, res) => {
  try {
    const { lbArn } = req.params;
    const loadBalancers = getLoadBalancers();
    const lb = loadBalancers.find(l => l.load_balancer_arn === lbArn);

    if (!lb) {
      return res.status(404).json({
        error: 'Load balancer not found',
        load_balancer_arn: lbArn,
      });
    }

    console.log(`📤 Fetching load balancer: ${lbArn}`);
    res.json({
      status: 'success',
      data: lb,
    });
  } catch (error) {
    console.error('❌ Error fetching load balancer:', error);
    res.status(500).json({
      error: 'Failed to fetch load balancer',
      message: error.message,
    });
  }
});

module.exports = router;
