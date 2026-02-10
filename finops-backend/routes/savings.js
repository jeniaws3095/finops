const express = require('express');
const router = express.Router();
const store = require('../store');

// Reference to shared store
const getSavings = () => store.savings;

/**
 * POST /api/savings
 * Record cost savings from optimization actions
 */
router.post('/', (req, res) => {
  try {
    const {
      resource_id,
      cloud,
      money_saved,
      region,
      state,
      instance_type,
      pricing_model,
      estimated_hours_saved,
      date,
    } = req.body;

    // Validate required fields
    if (!resource_id || !cloud || money_saved === undefined) {
      return res.status(400).json({
        error: 'Missing required fields: resource_id, cloud, money_saved',
      });
    }

    const savingsRecord = {
      resource_id,
      cloud,
      money_saved,
      region,
      state,
      instance_type,
      pricing_model,
      estimated_hours_saved,
      date: date ? new Date(date) : new Date(),
      timestamp: new Date(),
    };

    console.log(`💰 Recorded savings: ${resource_id} | ${money_saved} | ${cloud}`);
    getSavings().push(savingsRecord);

    res.status(201).json({
      status: 'success',
      message: 'Savings recorded',
      data: {
        resource_id,
        money_saved,
        cloud,
      },
    });
  } catch (error) {
    console.error('❌ Error recording savings:', error);
    res.status(500).json({
      error: 'Failed to record savings',
      message: error.message,
    });
  }
});

/**
 * GET /api/savings
 * Retrieve all savings records with optional filters
 */
router.get('/', (req, res) => {
  try {
    const { startDate, endDate, cloud } = req.query;

    let filtered = getSavings();

    // Filter by cloud provider
    if (cloud) {
      filtered = filtered.filter(s => s.cloud === cloud);
    }

    // Filter by date range
    if (startDate || endDate) {
      filtered = filtered.filter(s => {
        const recordDate = new Date(s.date);
        if (startDate && recordDate < new Date(startDate)) return false;
        if (endDate && recordDate > new Date(endDate)) return false;
        return true;
      });
    }

    const totalSavings = filtered.reduce((sum, s) => sum + (s.money_saved || 0), 0);

    console.log(`📤 Fetching ${filtered.length} savings records`);
    res.json({
      status: 'success',
      data: filtered,
      total: filtered.length,
      totalSavings: totalSavings,
    });
  } catch (error) {
    console.error('❌ Error fetching savings:', error);
    res.status(500).json({
      error: 'Failed to fetch savings',
      message: error.message,
    });
  }
});

/**
 * GET /api/savings/summary
 * Get savings summary statistics
 */
router.get('/summary', (req, res) => {
  try {
    const savings = getSavings();
    const totalSavings = savings.reduce((sum, s) => sum + (s.money_saved || 0), 0);
    const monthlySavings = totalSavings / 12; // Rough estimate
    const annualSavings = totalSavings * 12;

    console.log(`📊 Fetching savings summary`);
    res.json({
      status: 'success',
      data: {
        totalSavings: totalSavings,
        monthlySavings: monthlySavings,
        annualSavings: annualSavings,
        resourceCount: savings.length,
      },
    });
  } catch (error) {
    console.error('❌ Error fetching savings summary:', error);
    res.status(500).json({
      error: 'Failed to fetch savings summary',
      message: error.message,
    });
  }
});

module.exports = router;
