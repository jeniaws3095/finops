const express = require('express');
const router = express.Router();
const store = require('../store');

/**
 * GET /api/costing/current
 * Get current total costing across all resources
 */
router.get('/current', (req, res) => {
  try {
    console.log('📊 Calculating current costing...');

    const instances = store.instances;
    const loadBalancers = store.loadBalancers;
    const autoScalingGroups = store.autoScalingGroups;
    const ebsVolumes = store.ebsVolumes;
    const rdsInstances = store.rdsInstances;

    // Calculate EC2 instances cost
    const ec2Cost = instances.reduce((sum, instance) => {
      return sum + (instance.monthly_cost || 0);
    }, 0);

    // Calculate load balancers cost
    const lbCost = loadBalancers.reduce((sum, lb) => {
      return sum + (lb.monthly_cost || 0);
    }, 0);

    // Calculate ASG cost
    const asgCost = autoScalingGroups.reduce((sum, asg) => {
      return sum + (asg.monthly_cost || 0);
    }, 0);

    // Calculate EBS volumes cost
    const ebsCost = ebsVolumes.reduce((sum, volume) => {
      return sum + (volume.monthly_cost || 0);
    }, 0);

    // Calculate RDS instances cost
    const rdsCost = rdsInstances.reduce((sum, rds) => {
      return sum + (rds.monthly_cost || 0);
    }, 0);

    // Calculate totals
    const totalMonthlyCost = ec2Cost + lbCost + asgCost + ebsCost + rdsCost;
    const totalDailyCost = totalMonthlyCost / 30;
    const totalAnnualCost = totalMonthlyCost * 12;

    console.log(`💰 Total Monthly Cost: ${totalMonthlyCost.toFixed(2)}`);

    res.json({
      total_monthly_cost: parseFloat(totalMonthlyCost.toFixed(2)),
      total_daily_cost: parseFloat(totalDailyCost.toFixed(2)),
      total_annual_cost: parseFloat(totalAnnualCost.toFixed(2)),
      timestamp: new Date().toISOString(),
      region_count: new Set([
        ...instances.map(i => i.region),
        ...loadBalancers.map(lb => lb.region),
        ...autoScalingGroups.map(asg => asg.region),
        ...ebsVolumes.map(v => v.region),
        ...rdsInstances.map(r => r.region)
      ]).size,
      service_breakdown: {
        ec2: parseFloat(ec2Cost.toFixed(2)),
        load_balancers: parseFloat(lbCost.toFixed(2)),
        auto_scaling_groups: parseFloat(asgCost.toFixed(2)),
        ebs_volumes: parseFloat(ebsCost.toFixed(2)),
        rds_instances: parseFloat(rdsCost.toFixed(2))
      },
      resource_counts: {
        ec2_instances: instances.length,
        load_balancers: loadBalancers.length,
        auto_scaling_groups: autoScalingGroups.length,
        ebs_volumes: ebsVolumes.length,
        rds_instances: rdsInstances.length
      }
    });
  } catch (error) {
    console.error('❌ Error calculating costing:', error);
    res.status(500).json({
      error: 'Failed to calculate costing',
      message: error.message,
    });
  }
});

/**
 * GET /api/costing/by-region
 * Get costing breakdown by region
 */
router.get('/by-region', (req, res) => {
  try {
    console.log('📊 Calculating costing by region...');

    const instances = store.instances;
    const loadBalancers = store.loadBalancers;
    const autoScalingGroups = store.autoScalingGroups;
    const ebsVolumes = store.ebsVolumes;
    const rdsInstances = store.rdsInstances;

    const costByRegion = {};

    // Aggregate EC2 instances by region
    instances.forEach(instance => {
      const region = instance.region || 'unknown';
      if (!costByRegion[region]) {
        costByRegion[region] = {
          ec2: 0,
          loadBalancers: 0,
          asg: 0,
          ebs: 0,
          rds: 0,
          total: 0,
        };
      }
      costByRegion[region].ec2 += instance.monthly_cost || 0;
    });

    // Aggregate load balancers by region
    loadBalancers.forEach(lb => {
      const region = lb.region || 'unknown';
      if (!costByRegion[region]) {
        costByRegion[region] = {
          ec2: 0,
          loadBalancers: 0,
          asg: 0,
          ebs: 0,
          rds: 0,
          total: 0,
        };
      }
      costByRegion[region].loadBalancers += lb.monthly_cost || 0;
    });

    // Aggregate ASGs by region
    autoScalingGroups.forEach(asg => {
      const region = asg.region || 'unknown';
      if (!costByRegion[region]) {
        costByRegion[region] = {
          ec2: 0,
          loadBalancers: 0,
          asg: 0,
          ebs: 0,
          rds: 0,
          total: 0,
        };
      }
      costByRegion[region].asg += asg.monthly_cost || 0;
    });

    // Aggregate EBS volumes by region
    ebsVolumes.forEach(volume => {
      const region = volume.region || 'unknown';
      if (!costByRegion[region]) {
        costByRegion[region] = {
          ec2: 0,
          loadBalancers: 0,
          asg: 0,
          ebs: 0,
          rds: 0,
          total: 0,
        };
      }
      costByRegion[region].ebs += volume.monthly_cost || 0;
    });

    // Aggregate RDS instances by region
    rdsInstances.forEach(rds => {
      const region = rds.region || 'unknown';
      if (!costByRegion[region]) {
        costByRegion[region] = {
          ec2: 0,
          loadBalancers: 0,
          asg: 0,
          ebs: 0,
          rds: 0,
          total: 0,
        };
      }
      costByRegion[region].rds += rds.monthly_cost || 0;
    });

    // Calculate totals for each region
    Object.keys(costByRegion).forEach(region => {
      costByRegion[region].total =
        costByRegion[region].ec2 +
        costByRegion[region].loadBalancers +
        costByRegion[region].asg +
        costByRegion[region].ebs +
        costByRegion[region].rds;

      // Round to 2 decimal places
      Object.keys(costByRegion[region]).forEach(key => {
        costByRegion[region][key] = parseFloat(costByRegion[region][key].toFixed(2));
      });
    });

    console.log(`📊 Costing by region calculated`);

    res.json({
      status: 'success',
      data: costByRegion,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('❌ Error calculating costing by region:', error);
    res.status(500).json({
      error: 'Failed to calculate costing by region',
      message: error.message,
    });
  }
});

/**
 * GET /api/costing/by-service
 * Get costing breakdown by service type
 */
router.get('/by-service', (req, res) => {
  try {
    console.log('📊 Calculating costing by service...');

    const instances = store.instances;
    const loadBalancers = store.loadBalancers;
    const autoScalingGroups = store.autoScalingGroups;
    const ebsVolumes = store.ebsVolumes;
    const rdsInstances = store.rdsInstances;

    const ec2Cost = instances.reduce((sum, instance) => sum + (instance.monthly_cost || 0), 0);
    const lbCost = loadBalancers.reduce((sum, lb) => sum + (lb.monthly_cost || 0), 0);
    const asgCost = autoScalingGroups.reduce((sum, asg) => sum + (asg.monthly_cost || 0), 0);
    const ebsCost = ebsVolumes.reduce((sum, volume) => sum + (volume.monthly_cost || 0), 0);
    const rdsCost = rdsInstances.reduce((sum, rds) => sum + (rds.monthly_cost || 0), 0);

    const totalCost = ec2Cost + lbCost + asgCost + ebsCost + rdsCost;

    const services = {
      ec2: parseFloat(ec2Cost.toFixed(2)),
      load_balancers: parseFloat(lbCost.toFixed(2)),
      auto_scaling_groups: parseFloat(asgCost.toFixed(2)),
      ebs_volumes: parseFloat(ebsCost.toFixed(2)),
      rds_instances: parseFloat(rdsCost.toFixed(2))
    };

    const service_percentages = {
      ec2: totalCost > 0 ? parseFloat(((ec2Cost / totalCost) * 100).toFixed(2)) : 0,
      load_balancers: totalCost > 0 ? parseFloat(((lbCost / totalCost) * 100).toFixed(2)) : 0,
      auto_scaling_groups: totalCost > 0 ? parseFloat(((asgCost / totalCost) * 100).toFixed(2)) : 0,
      ebs_volumes: totalCost > 0 ? parseFloat(((ebsCost / totalCost) * 100).toFixed(2)) : 0,
      rds_instances: totalCost > 0 ? parseFloat(((rdsCost / totalCost) * 100).toFixed(2)) : 0
    };

    console.log(`📊 Costing by service calculated`);

    res.json({
      services: services,
      total_monthly: parseFloat(totalCost.toFixed(2)),
      timestamp: new Date().toISOString(),
      service_percentages: service_percentages
    });
  } catch (error) {
    console.error('❌ Error calculating costing by service:', error);
    res.status(500).json({
      error: 'Failed to calculate costing by service',
      message: error.message,
    });
  }
});

module.exports = router;
