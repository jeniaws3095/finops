/**
 * CostAnomaly Model
 * 
 * Represents detected cost anomalies and spending spikes with
 * root cause analysis and severity assessment.
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4
 */

class CostAnomaly {
  constructor(data = {}) {
    // Required fields
    this.anomalyId = data.anomalyId || this.generateId();
    this.detectedAt = data.detectedAt || new Date().toISOString();
    this.region = data.region || '';
    this.timestamp = data.timestamp || new Date().toISOString();
    
    // Anomaly classification
    this.serviceType = data.serviceType || ''; // 'ec2', 'rds', 'lambda', 's3', etc.
    this.anomalyType = data.anomalyType || ''; // 'spike', 'trend', 'pattern', 'baseline_shift'
    this.severity = data.severity || 'MEDIUM'; // 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    
    // Cost data
    this.baselineCost = data.baselineCost || 0;
    this.actualCost = data.actualCost || 0;
    this.deviationPercentage = data.deviationPercentage || 0;
    this.deviationAmount = data.deviationAmount || 0;
    
    // Analysis and root cause
    this.rootCause = data.rootCause || '';
    this.affectedResources = data.affectedResources || [];
    this.contributingFactors = data.contributingFactors || [];
    this.analysisConfidence = data.analysisConfidence || 0; // 0-100
    
    // Detection details
    this.detectionMethod = data.detectionMethod || 'threshold'; // 'threshold', 'ml', 'statistical'
    this.thresholdUsed = data.thresholdUsed || null;
    this.timeWindow = data.timeWindow || '1h'; // Time window for anomaly detection
    
    // Status and resolution
    this.resolved = data.resolved || false;
    this.resolvedAt = data.resolvedAt || null;
    this.resolvedBy = data.resolvedBy || null;
    this.resolutionNotes = data.resolutionNotes || '';
    
    // Alert and notification
    this.alertSent = data.alertSent || false;
    this.alertSentAt = data.alertSentAt || null;
    this.notificationChannels = data.notificationChannels || [];
    
    // Additional metadata
    this.tags = data.tags || {};
    this.category = data.category || ''; // 'compute', 'storage', 'network', 'database', etc.
    this.impactAssessment = data.impactAssessment || '';
    this.recommendedActions = data.recommendedActions || [];
  }

  /**
   * Generate a unique anomaly ID
   * @returns {string} Unique ID
   */
  generateId() {
    return 'anom_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * Calculate the deviation percentage from baseline
   * @returns {number} Deviation percentage
   */
  calculateDeviationPercentage() {
    if (this.baselineCost === 0) return 0;
    return ((this.actualCost - this.baselineCost) / this.baselineCost) * 100;
  }

  /**
   * Calculate the deviation amount from baseline
   * @returns {number} Deviation amount
   */
  calculateDeviationAmount() {
    return this.actualCost - this.baselineCost;
  }

  /**
   * Determine severity based on deviation percentage and amount
   * @returns {string} Severity level
   */
  determineSeverity() {
    const deviationPct = Math.abs(this.calculateDeviationPercentage());
    const deviationAmt = Math.abs(this.calculateDeviationAmount());
    
    // Critical: >200% increase or >$10,000 deviation
    if (deviationPct > 200 || deviationAmt > 10000) {
      return 'CRITICAL';
    }
    
    // High: >100% increase or >$1,000 deviation
    if (deviationPct > 100 || deviationAmt > 1000) {
      return 'HIGH';
    }
    
    // Medium: >25% increase or >$100 deviation
    if (deviationPct > 25 || deviationAmt > 100) {
      return 'MEDIUM';
    }
    
    // Low: anything else
    return 'LOW';
  }

  /**
   * Mark anomaly as resolved
   * @param {string} resolvedBy User who resolved
   * @param {string} notes Resolution notes
   * @returns {boolean} Success status
   */
  resolve(resolvedBy, notes = '') {
    if (this.resolved) {
      return false;
    }
    
    this.resolved = true;
    this.resolvedAt = new Date().toISOString();
    this.resolvedBy = resolvedBy;
    this.resolutionNotes = notes;
    return true;
  }

  /**
   * Mark alert as sent
   * @param {Array} channels Notification channels used
   * @returns {boolean} Success status
   */
  markAlertSent(channels = []) {
    if (this.alertSent) {
      return false;
    }
    
    this.alertSent = true;
    this.alertSentAt = new Date().toISOString();
    this.notificationChannels = channels;
    return true;
  }

  /**
   * Add a contributing factor to the anomaly
   * @param {Object} factor Contributing factor details
   */
  addContributingFactor(factor) {
    this.contributingFactors.push({
      ...factor,
      addedAt: new Date().toISOString()
    });
  }

  /**
   * Add an affected resource to the anomaly
   * @param {Object} resource Affected resource details
   */
  addAffectedResource(resource) {
    this.affectedResources.push({
      ...resource,
      addedAt: new Date().toISOString()
    });
  }

  /**
   * Validate the anomaly data
   * @returns {Object} Validation result with isValid boolean and errors array
   */
  validate() {
    const errors = [];
    
    if (!this.serviceType) {
      errors.push('serviceType is required');
    }
    
    if (!this.anomalyType) {
      errors.push('anomalyType is required');
    }
    
    const validAnomalyTypes = ['spike', 'trend', 'pattern', 'baseline_shift'];
    if (this.anomalyType && !validAnomalyTypes.includes(this.anomalyType)) {
      errors.push(`anomalyType must be one of: ${validAnomalyTypes.join(', ')}`);
    }
    
    const validSeverities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
    if (!validSeverities.includes(this.severity)) {
      errors.push(`severity must be one of: ${validSeverities.join(', ')}`);
    }
    
    if (typeof this.baselineCost !== 'number' || this.baselineCost < 0) {
      errors.push('baselineCost must be a non-negative number');
    }
    
    if (typeof this.actualCost !== 'number' || this.actualCost < 0) {
      errors.push('actualCost must be a non-negative number');
    }
    
    if (typeof this.analysisConfidence !== 'number' || this.analysisConfidence < 0 || this.analysisConfidence > 100) {
      errors.push('analysisConfidence must be a number between 0 and 100');
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
      anomalyId: this.anomalyId,
      detectedAt: this.detectedAt,
      region: this.region,
      serviceType: this.serviceType,
      anomalyType: this.anomalyType,
      severity: this.severity,
      baselineCost: this.baselineCost,
      actualCost: this.actualCost,
      deviationPercentage: this.deviationPercentage,
      deviationAmount: this.deviationAmount,
      rootCause: this.rootCause,
      affectedResources: this.affectedResources,
      contributingFactors: this.contributingFactors,
      analysisConfidence: this.analysisConfidence,
      detectionMethod: this.detectionMethod,
      thresholdUsed: this.thresholdUsed,
      timeWindow: this.timeWindow,
      resolved: this.resolved,
      resolvedAt: this.resolvedAt,
      resolvedBy: this.resolvedBy,
      resolutionNotes: this.resolutionNotes,
      alertSent: this.alertSent,
      alertSentAt: this.alertSentAt,
      notificationChannels: this.notificationChannels,
      tags: this.tags,
      category: this.category,
      impactAssessment: this.impactAssessment,
      recommendedActions: this.recommendedActions,
      timestamp: this.timestamp
    };
  }

  /**
   * Create CostAnomaly from JSON data
   * @param {Object} json JSON object
   * @returns {CostAnomaly} New CostAnomaly instance
   */
  static fromJSON(json) {
    return new CostAnomaly(json);
  }
}

module.exports = CostAnomaly;