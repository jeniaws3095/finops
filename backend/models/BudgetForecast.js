/**
 * BudgetForecast Model
 * 
 * Represents budget forecasts and predictions with confidence intervals,
 * hierarchical budget support, and variance tracking.
 * 
 * Requirements: 5.1, 5.2, 5.3, 6.1
 */

class BudgetForecast {
  constructor(data = {}) {
    // Required fields
    this.forecastId = data.forecastId || this.generateId();
    this.budgetCategory = data.budgetCategory || ''; // 'organization', 'team', 'project'
    this.budgetName = data.budgetName || '';
    this.region = data.region || '';
    this.timestamp = data.timestamp || new Date().toISOString();
    
    // Budget amounts
    this.currentSpend = data.currentSpend || 0;
    this.forecastedSpend = data.forecastedSpend || 0;
    this.budgetLimit = data.budgetLimit || 0;
    this.remainingBudget = data.remainingBudget || 0;
    
    // Forecast details
    this.confidenceInterval = data.confidenceInterval || {
      lower: 0,
      upper: 0,
      confidence: 95 // percentage
    };
    this.projectionPeriod = data.projectionPeriod || '1M'; // '1W', '1M', '3M', '6M', '1Y'
    this.forecastMethod = data.forecastMethod || 'trend'; // 'trend', 'seasonal', 'ml', 'hybrid'
    
    // Historical data and trends
    this.historicalSpend = data.historicalSpend || [];
    this.seasonalFactors = data.seasonalFactors || [];
    this.trendAnalysis = data.trendAnalysis || {
      direction: 'stable', // 'increasing', 'decreasing', 'stable', 'volatile'
      rate: 0, // percentage change per period
      confidence: 0 // 0-100
    };
    
    // Variance tracking
    this.variance = data.variance || {
      amount: 0,
      percentage: 0,
      type: 'neutral' // 'favorable', 'unfavorable', 'neutral'
    };
    
    // Forecast assumptions
    this.assumptions = data.assumptions || [];
    this.riskFactors = data.riskFactors || [];
    this.plannedChanges = data.plannedChanges || [];
    
    // Hierarchy and allocation
    this.parentBudget = data.parentBudget || null;
    this.childBudgets = data.childBudgets || [];
    this.allocationRules = data.allocationRules || [];
    
    // Alert thresholds
    this.alertThresholds = data.alertThresholds || {
      warning: 80, // percentage of budget
      critical: 95,
      forecast_overrun: 100
    };
    
    // Status and metadata
    this.status = data.status || 'active'; // 'active', 'exceeded', 'completed', 'suspended'
    this.lastUpdated = data.lastUpdated || new Date().toISOString();
    this.tags = data.tags || {};
    this.owner = data.owner || '';
    this.approvers = data.approvers || [];
  }

  /**
   * Generate a unique forecast ID
   * @returns {string} Unique ID
   */
  generateId() {
    return 'fcst_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * Calculate budget utilization percentage
   * @returns {number} Utilization percentage
   */
  getBudgetUtilization() {
    if (this.budgetLimit === 0) return 0;
    return (this.currentSpend / this.budgetLimit) * 100;
  }

  /**
   * Calculate forecasted budget utilization percentage
   * @returns {number} Forecasted utilization percentage
   */
  getForecastedUtilization() {
    if (this.budgetLimit === 0) return 0;
    return (this.forecastedSpend / this.budgetLimit) * 100;
  }

  /**
   * Calculate remaining budget
   * @returns {number} Remaining budget amount
   */
  calculateRemainingBudget() {
    return Math.max(0, this.budgetLimit - this.currentSpend);
  }

  /**
   * Calculate variance from budget
   * @returns {Object} Variance details
   */
  calculateVariance() {
    const amount = this.currentSpend - this.budgetLimit;
    const percentage = this.budgetLimit === 0 ? 0 : (amount / this.budgetLimit) * 100;
    
    let type = 'neutral';
    if (amount > 0) {
      type = 'unfavorable'; // over budget
    } else if (amount < 0) {
      type = 'favorable'; // under budget
    }
    
    return {
      amount: Math.abs(amount),
      percentage: Math.abs(percentage),
      type
    };
  }

  /**
   * Check if budget is at risk of being exceeded
   * @returns {Object} Risk assessment
   */
  assessBudgetRisk() {
    const currentUtilization = this.getBudgetUtilization();
    const forecastedUtilization = this.getForecastedUtilization();
    
    let riskLevel = 'LOW';
    let message = 'Budget is on track';
    
    if (forecastedUtilization > this.alertThresholds.forecast_overrun) {
      riskLevel = 'CRITICAL';
      message = 'Forecast indicates budget will be exceeded';
    } else if (currentUtilization > this.alertThresholds.critical) {
      riskLevel = 'HIGH';
      message = 'Budget utilization is at critical level';
    } else if (currentUtilization > this.alertThresholds.warning) {
      riskLevel = 'MEDIUM';
      message = 'Budget utilization approaching warning threshold';
    }
    
    return {
      riskLevel,
      message,
      currentUtilization,
      forecastedUtilization,
      daysRemaining: this.calculateDaysRemaining()
    };
  }

  /**
   * Calculate days remaining in budget period
   * @returns {number} Days remaining
   */
  calculateDaysRemaining() {
    // This is a simplified calculation - in practice, you'd need the budget period end date
    const periodMap = {
      '1W': 7,
      '1M': 30,
      '3M': 90,
      '6M': 180,
      '1Y': 365
    };
    
    return periodMap[this.projectionPeriod] || 30;
  }

  /**
   * Add a forecast assumption
   * @param {Object} assumption Assumption details
   */
  addAssumption(assumption) {
    this.assumptions.push({
      ...assumption,
      addedAt: new Date().toISOString()
    });
  }

  /**
   * Add a risk factor
   * @param {Object} riskFactor Risk factor details
   */
  addRiskFactor(riskFactor) {
    this.riskFactors.push({
      ...riskFactor,
      addedAt: new Date().toISOString()
    });
  }

  /**
   * Update forecast with new data
   * @param {Object} newData Updated forecast data
   */
  updateForecast(newData) {
    Object.assign(this, newData);
    this.lastUpdated = new Date().toISOString();
    this.remainingBudget = this.calculateRemainingBudget();
    this.variance = this.calculateVariance();
  }

  /**
   * Validate the budget forecast data
   * @returns {Object} Validation result with isValid boolean and errors array
   */
  validate() {
    const errors = [];
    
    if (!this.budgetCategory) {
      errors.push('budgetCategory is required');
    }
    
    const validCategories = ['organization', 'team', 'project'];
    if (this.budgetCategory && !validCategories.includes(this.budgetCategory)) {
      errors.push(`budgetCategory must be one of: ${validCategories.join(', ')}`);
    }
    
    if (!this.budgetName) {
      errors.push('budgetName is required');
    }
    
    if (typeof this.currentSpend !== 'number' || this.currentSpend < 0) {
      errors.push('currentSpend must be a non-negative number');
    }
    
    if (typeof this.forecastedSpend !== 'number' || this.forecastedSpend < 0) {
      errors.push('forecastedSpend must be a non-negative number');
    }
    
    if (typeof this.budgetLimit !== 'number' || this.budgetLimit < 0) {
      errors.push('budgetLimit must be a non-negative number');
    }
    
    const validPeriods = ['1W', '1M', '3M', '6M', '1Y'];
    if (!validPeriods.includes(this.projectionPeriod)) {
      errors.push(`projectionPeriod must be one of: ${validPeriods.join(', ')}`);
    }
    
    const validStatuses = ['active', 'exceeded', 'completed', 'suspended'];
    if (!validStatuses.includes(this.status)) {
      errors.push(`status must be one of: ${validStatuses.join(', ')}`);
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
      forecastId: this.forecastId,
      budgetCategory: this.budgetCategory,
      budgetName: this.budgetName,
      region: this.region,
      currentSpend: this.currentSpend,
      forecastedSpend: this.forecastedSpend,
      budgetLimit: this.budgetLimit,
      remainingBudget: this.remainingBudget,
      confidenceInterval: this.confidenceInterval,
      projectionPeriod: this.projectionPeriod,
      forecastMethod: this.forecastMethod,
      historicalSpend: this.historicalSpend,
      seasonalFactors: this.seasonalFactors,
      trendAnalysis: this.trendAnalysis,
      variance: this.variance,
      assumptions: this.assumptions,
      riskFactors: this.riskFactors,
      plannedChanges: this.plannedChanges,
      parentBudget: this.parentBudget,
      childBudgets: this.childBudgets,
      allocationRules: this.allocationRules,
      alertThresholds: this.alertThresholds,
      status: this.status,
      lastUpdated: this.lastUpdated,
      tags: this.tags,
      owner: this.owner,
      approvers: this.approvers,
      timestamp: this.timestamp,
      budgetUtilization: this.getBudgetUtilization(),
      forecastedUtilization: this.getForecastedUtilization(),
      budgetRisk: this.assessBudgetRisk()
    };
  }

  /**
   * Create BudgetForecast from JSON data
   * @param {Object} json JSON object
   * @returns {BudgetForecast} New BudgetForecast instance
   */
  static fromJSON(json) {
    return new BudgetForecast(json);
  }
}

module.exports = BudgetForecast;