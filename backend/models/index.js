/**
 * Models Index
 * 
 * Central export point for all Advanced FinOps Platform data models.
 * Provides easy access to ResourceInventory, CostOptimization, CostAnomaly, 
 * and BudgetForecast models with consistent patterns.
 * 
 * Requirements: 1.3, 6.1, 4.1
 */

const ResourceInventory = require('./ResourceInventory');
const CostOptimization = require('./CostOptimization');
const CostAnomaly = require('./CostAnomaly');
const BudgetForecast = require('./BudgetForecast');

module.exports = {
  ResourceInventory,
  CostOptimization,
  CostAnomaly,
  BudgetForecast
};