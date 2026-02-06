/**
 * ResourceInventory Model
 * 
 * Represents discovered AWS resources across multiple services
 * with utilization metrics and optimization opportunities.
 * 
 * Requirements: 1.1, 1.2, 1.3
 */

class ResourceInventory {
  constructor(data = {}) {
    // Required fields
    this.resourceId = data.resourceId || '';
    this.resourceType = data.resourceType || ''; // 'ec2', 'rds', 'lambda', 's3', 'ebs', 'elb', 'cloudwatch'
    this.region = data.region || '';
    this.timestamp = data.timestamp || new Date().toISOString();
    
    // Cost and utilization data
    this.currentCost = data.currentCost || 0;
    this.utilizationMetrics = data.utilizationMetrics || {
      cpu: [],
      memory: [],
      network: [],
      storage: [],
      timeRange: {
        start: null,
        end: null
      },
      samplingInterval: '5m'
    };
    
    // Optimization opportunities
    this.optimizationOpportunities = data.optimizationOpportunities || [];
    
    // Additional metadata
    this.resourceName = data.resourceName || '';
    this.tags = data.tags || {};
    this.configuration = data.configuration || {};
    this.state = data.state || 'unknown'; // 'running', 'stopped', 'terminated', etc.
    this.lastModified = data.lastModified || new Date().toISOString();
  }

  /**
   * Validate the resource inventory data
   * @returns {Object} Validation result with isValid boolean and errors array
   */
  validate() {
    const errors = [];
    
    if (!this.resourceId || (typeof this.resourceId === 'string' && this.resourceId.trim() === '')) {
      errors.push('resourceId is required');
    }
    
    if (!this.resourceType) {
      errors.push('resourceType is required');
    }
    
    const validResourceTypes = ['ec2', 'rds', 'lambda', 's3', 'ebs', 'elb', 'cloudwatch'];
    if (this.resourceType && !validResourceTypes.includes(this.resourceType)) {
      errors.push(`resourceType must be one of: ${validResourceTypes.join(', ')}`);
    }
    
    if (!this.region) {
      errors.push('region is required');
    }
    
    if (typeof this.currentCost !== 'number' || this.currentCost < 0) {
      errors.push('currentCost must be a non-negative number');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Convert to JSON representation
   * @returns {Object} JSON object
   */
  toJSON() {
    return {
      resourceId: this.resourceId,
      resourceType: this.resourceType,
      region: this.region,
      currentCost: this.currentCost,
      utilizationMetrics: this.utilizationMetrics,
      optimizationOpportunities: this.optimizationOpportunities,
      resourceName: this.resourceName,
      tags: this.tags,
      configuration: this.configuration,
      state: this.state,
      timestamp: this.timestamp,
      lastModified: this.lastModified
    };
  }

  /**
   * Create ResourceInventory from JSON data
   * @param {Object} json JSON object
   * @returns {ResourceInventory} New ResourceInventory instance
   */
  static fromJSON(json) {
    return new ResourceInventory(json);
  }
}

module.exports = ResourceInventory;