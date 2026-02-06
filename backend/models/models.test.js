/**
 * Models Unit Tests
 * 
 * Tests for all Advanced FinOps Platform data models to ensure
 * they follow established patterns and include required fields.
 * 
 * Requirements: 1.3, 6.1, 4.1
 */

const { ResourceInventory, CostOptimization, CostAnomaly, BudgetForecast } = require('./index');

describe('Advanced FinOps Platform Models', () => {
  
  describe('ResourceInventory Model', () => {
    test('should create ResourceInventory with required fields', () => {
      const data = {
        resourceId: 'i-1234567890abcdef0',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 100.50
      };
      
      const resource = new ResourceInventory(data);
      
      expect(resource.resourceId).toBe('i-1234567890abcdef0');
      expect(resource.resourceType).toBe('ec2');
      expect(resource.region).toBe('us-east-1');
      expect(resource.currentCost).toBe(100.50);
      expect(resource.timestamp).toBeDefined();
    });

    test('should validate required fields', () => {
      const resource = new ResourceInventory();
      const validation = resource.validate();
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('resourceId is required');
      expect(validation.errors).toContain('resourceType is required');
      expect(validation.errors).toContain('region is required');
    });

    test('should validate resource type', () => {
      const resource = new ResourceInventory({
        resourceId: 'test-id',
        resourceType: 'invalid-type',
        region: 'us-east-1'
      });
      const validation = resource.validate();
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors.some(error => error.includes('resourceType must be one of'))).toBe(true);
    });

    test('should convert to JSON', () => {
      const data = {
        resourceId: 'i-1234567890abcdef0',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 100.50
      };
      
      const resource = new ResourceInventory(data);
      const json = resource.toJSON();
      
      expect(json.resourceId).toBe('i-1234567890abcdef0');
      expect(json.resourceType).toBe('ec2');
      expect(json.region).toBe('us-east-1');
      expect(json.currentCost).toBe(100.50);
    });
  });

  describe('CostOptimization Model', () => {
    test('should create CostOptimization with required fields', () => {
      const data = {
        resourceId: 'i-1234567890abcdef0',
        region: 'us-east-1',
        optimizationType: 'rightsizing',
        currentCost: 200.00,
        projectedCost: 150.00,
        estimatedSavings: 50.00
      };
      
      const optimization = new CostOptimization(data);
      
      expect(optimization.resourceId).toBe('i-1234567890abcdef0');
      expect(optimization.region).toBe('us-east-1');
      expect(optimization.optimizationType).toBe('rightsizing');
      expect(optimization.currentCost).toBe(200.00);
      expect(optimization.projectedCost).toBe(150.00);
      expect(optimization.estimatedSavings).toBe(50.00);
      expect(optimization.optimizationId).toBeDefined();
      expect(optimization.timestamp).toBeDefined();
    });

    test('should calculate savings percentage', () => {
      const optimization = new CostOptimization({
        currentCost: 200.00,
        projectedCost: 150.00
      });
      
      expect(optimization.getSavingsPercentage()).toBe(25);
    });

    test('should determine approval requirements', () => {
      const lowRiskOptimization = new CostOptimization({
        riskLevel: 'LOW',
        estimatedSavings: 50.00
      });
      
      const highRiskOptimization = new CostOptimization({
        riskLevel: 'HIGH',
        estimatedSavings: 50.00
      });
      
      expect(lowRiskOptimization.requiresApproval()).toBe(false);
      expect(highRiskOptimization.requiresApproval()).toBe(true);
    });

    test('should validate optimization data', () => {
      const optimization = new CostOptimization();
      const validation = optimization.validate();
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('resourceId is required');
      expect(validation.errors).toContain('optimizationType is required');
    });
  });

  describe('CostAnomaly Model', () => {
    test('should create CostAnomaly with required fields', () => {
      const data = {
        serviceType: 'ec2',
        region: 'us-east-1',
        anomalyType: 'spike',
        baselineCost: 100.00,
        actualCost: 250.00
      };
      
      const anomaly = new CostAnomaly(data);
      
      expect(anomaly.serviceType).toBe('ec2');
      expect(anomaly.region).toBe('us-east-1');
      expect(anomaly.anomalyType).toBe('spike');
      expect(anomaly.baselineCost).toBe(100.00);
      expect(anomaly.actualCost).toBe(250.00);
      expect(anomaly.anomalyId).toBeDefined();
      expect(anomaly.timestamp).toBeDefined();
    });

    test('should calculate deviation percentage', () => {
      const anomaly = new CostAnomaly({
        baselineCost: 100.00,
        actualCost: 150.00
      });
      
      expect(anomaly.calculateDeviationPercentage()).toBe(50);
    });

    test('should determine severity automatically', () => {
      const criticalAnomaly = new CostAnomaly({
        baselineCost: 100.00,
        actualCost: 400.00 // 300% increase
      });
      
      expect(criticalAnomaly.determineSeverity()).toBe('CRITICAL');
    });

    test('should validate anomaly data', () => {
      const anomaly = new CostAnomaly();
      const validation = anomaly.validate();
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('serviceType is required');
      expect(validation.errors).toContain('anomalyType is required');
    });
  });

  describe('BudgetForecast Model', () => {
    test('should create BudgetForecast with required fields', () => {
      const data = {
        budgetCategory: 'team',
        budgetName: 'Engineering Team Q1',
        region: 'us-east-1',
        currentSpend: 5000.00,
        forecastedSpend: 7500.00,
        budgetLimit: 10000.00
      };
      
      const forecast = new BudgetForecast(data);
      
      expect(forecast.budgetCategory).toBe('team');
      expect(forecast.budgetName).toBe('Engineering Team Q1');
      expect(forecast.region).toBe('us-east-1');
      expect(forecast.currentSpend).toBe(5000.00);
      expect(forecast.forecastedSpend).toBe(7500.00);
      expect(forecast.budgetLimit).toBe(10000.00);
      expect(forecast.forecastId).toBeDefined();
      expect(forecast.timestamp).toBeDefined();
    });

    test('should calculate budget utilization', () => {
      const forecast = new BudgetForecast({
        currentSpend: 5000.00,
        budgetLimit: 10000.00
      });
      
      expect(forecast.getBudgetUtilization()).toBe(50);
    });

    test('should calculate remaining budget', () => {
      const forecast = new BudgetForecast({
        currentSpend: 3000.00,
        budgetLimit: 10000.00
      });
      
      expect(forecast.calculateRemainingBudget()).toBe(7000.00);
    });

    test('should assess budget risk', () => {
      const riskForecast = new BudgetForecast({
        currentSpend: 9500.00,
        budgetLimit: 10000.00,
        forecastedSpend: 11000.00
      });
      
      const risk = riskForecast.assessBudgetRisk();
      expect(risk.riskLevel).toBe('CRITICAL'); // Forecast exceeds budget limit
    });

    test('should validate budget forecast data', () => {
      const forecast = new BudgetForecast();
      const validation = forecast.validate();
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('budgetCategory is required');
      expect(validation.errors).toContain('budgetName is required');
    });
  });

  describe('Model Integration', () => {
    test('all models should include required timestamp and region fields', () => {
      const resource = new ResourceInventory({ resourceId: 'test', resourceType: 'ec2', region: 'us-east-1' });
      const optimization = new CostOptimization({ resourceId: 'test', region: 'us-east-1', optimizationType: 'rightsizing' });
      const anomaly = new CostAnomaly({ serviceType: 'ec2', region: 'us-east-1', anomalyType: 'spike' });
      const forecast = new BudgetForecast({ budgetCategory: 'team', budgetName: 'test', region: 'us-east-1' });
      
      expect(resource.timestamp).toBeDefined();
      expect(resource.region).toBe('us-east-1');
      
      expect(optimization.timestamp).toBeDefined();
      expect(optimization.region).toBe('us-east-1');
      
      expect(anomaly.timestamp).toBeDefined();
      expect(anomaly.region).toBe('us-east-1');
      
      expect(forecast.timestamp).toBeDefined();
      expect(forecast.region).toBe('us-east-1');
    });

    test('all models should support JSON serialization', () => {
      const resource = new ResourceInventory({ resourceId: 'test', resourceType: 'ec2', region: 'us-east-1' });
      const optimization = new CostOptimization({ resourceId: 'test', region: 'us-east-1', optimizationType: 'rightsizing' });
      const anomaly = new CostAnomaly({ serviceType: 'ec2', region: 'us-east-1', anomalyType: 'spike' });
      const forecast = new BudgetForecast({ budgetCategory: 'team', budgetName: 'test', region: 'us-east-1' });
      
      expect(() => JSON.stringify(resource.toJSON())).not.toThrow();
      expect(() => JSON.stringify(optimization.toJSON())).not.toThrow();
      expect(() => JSON.stringify(anomaly.toJSON())).not.toThrow();
      expect(() => JSON.stringify(forecast.toJSON())).not.toThrow();
    });
  });
});