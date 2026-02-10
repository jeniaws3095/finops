/**
 * Shared in-memory data store for all routes
 * TODO: Replace with MongoDB when ready
 */

const store = {
  instances: [],
  savings: [],
  loadBalancers: [],
  autoScalingGroups: [],
  ebsVolumes: [],
  rdsInstances: [],
};

module.exports = store;
