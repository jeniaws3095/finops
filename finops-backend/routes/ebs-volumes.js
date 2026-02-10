const express = require('express');
const router = express.Router();
const store = require('../store');

// Reference to shared store
const getEbsVolumes = () => store.ebsVolumes;

/**
 * POST /api/ebs-volumes
 * Save EBS volume data
 */
router.post('/', (req, res) => {
  try {
    const {
      volume_id,
      volume_type,
      size_gb,
      region,
      state,
      availability_zone,
      encrypted,
      iops,
      throughput,
      attached_instance_id,
      attached_device,
      metrics,
      hourly_cost,
      monthly_cost,
      annual_cost,
      tags,
    } = req.body;

    // Validate required fields
    if (!volume_id || !volume_type || !region) {
      return res.status(400).json({
        error: 'Missing required fields: volume_id, volume_type, region',
      });
    }

    console.log(`📦 Received EBS volume: ${volume_id} in ${region}`);

    // Check if volume already exists and update or create
    const ebsVolumes = getEbsVolumes();
    const existingIndex = ebsVolumes.findIndex(v => v.volume_id === volume_id);
    const volumeData = {
      volume_id,
      volume_type,
      size_gb,
      region,
      state,
      availability_zone,
      encrypted,
      iops,
      throughput,
      attached_instance_id,
      attached_device,
      metrics,
      hourly_cost,
      monthly_cost,
      annual_cost,
      tags,
      timestamp: new Date(),
    };

    if (existingIndex >= 0) {
      ebsVolumes[existingIndex] = volumeData;
      console.log(`✅ Updated EBS volume: ${volume_id}`);
    } else {
      ebsVolumes.push(volumeData);
      console.log(`✅ Created EBS volume: ${volume_id}`);
    }

    res.status(201).json({
      status: 'success',
      message: 'EBS volume data saved',
      data: {
        volume_id,
        volume_type,
        region,
      },
    });
  } catch (error) {
    console.error('❌ Error saving EBS volume data:', error);
    res.status(500).json({
      error: 'Failed to save EBS volume data',
      message: error.message,
    });
  }
});

/**
 * GET /api/ebs-volumes
 * Retrieve all EBS volumes
 */
router.get('/', (req, res) => {
  try {
    const ebsVolumes = getEbsVolumes();
    console.log(`📤 Fetching ${ebsVolumes.length} EBS volumes`);
    res.json({
      status: 'success',
      data: ebsVolumes,
      total: ebsVolumes.length,
    });
  } catch (error) {
    console.error('❌ Error fetching EBS volumes:', error);
    res.status(500).json({
      error: 'Failed to fetch EBS volumes',
      message: error.message,
    });
  }
});

/**
 * GET /api/ebs-volumes/:volumeId
 * Retrieve a specific EBS volume
 */
router.get('/:volumeId', (req, res) => {
  try {
    const { volumeId } = req.params;
    const ebsVolumes = getEbsVolumes();
    const volume = ebsVolumes.find(v => v.volume_id === volumeId);

    if (!volume) {
      return res.status(404).json({
        error: 'EBS volume not found',
        volume_id: volumeId,
      });
    }

    console.log(`📤 Fetching EBS volume: ${volumeId}`);
    res.json({
      status: 'success',
      data: volume,
    });
  } catch (error) {
    console.error('❌ Error fetching EBS volume:', error);
    res.status(500).json({
      error: 'Failed to fetch EBS volume',
      message: error.message,
    });
  }
});

module.exports = router;
