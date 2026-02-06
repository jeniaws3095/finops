/**
 * Property-Based Tests for Data Model Completeness
 * 
 * **Feature: advanced-finops-platform, Property 1: Comprehensive Resource Discovery**
 * **Validates: Requirements 1.1, 1.2, 1.3**
 * 
 * This test validates that the data models (ResourceInventory, CostOptimization, 
 * CostAnomaly, and BudgetForecast) are complete and correctly structured for 
 * comprehensive resource discovery across multiple AWS services.
 */

const fc = require('fast-check');
const { ResourceInventory, CostOptimization, CostAnomaly, BudgetForecast } = require('./index');

describe('Property-Based Tests: Data Model Completeness', () => {
  
  // Generators for valid AWS resource types and regions
  const awsResourceTypes = fc.constantFrom('ec2', 'rds', 'lambda', 's3', 'ebs', 'elb', 'cloudwatch');
  const awsRegions = fc.constantFrom('us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1', 'ca-central-1');
  const riskLevels = fc.constantFrom('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
  const optimizationTypes = fc.constantFrom('rightsizing', 'pricing', 'cleanup', 'scheduling');
  const anomalyTypes = fc.constantFrom('spike', 'trend', 'pattern', 'baseline_shift');
  const budgetCategories = fc.constantFrom('organization', 'team', 'project');
  const severityLevels = fc.constantFrom('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

  // Generator for valid resource IDs
  const resourceIdGenerator = fc.oneof(
    fc.string({ minLength: 8, maxLength: 20 }).map(s => `i-${s}`), // EC2 instances
    fc.string({ minLength: 8, maxLength: 20 }).map(s => `db-${s}`), // RDS instances
    fc.string({ minLength: 8, maxLength: 30 }).map(s => `lambda-${s}`), // Lambda functions
    fc.string({ minLength: 3, maxLength: 63 }).map(s => `bucket-${s}`), // S3 buckets
    fc.string({ minLength: 8, maxLength: 20 }).map(s => `vol-${s}`), // EBS volumes
    fc.string({ minLength: 8, maxLength: 20 }).map(s => `elb-${s}`) // Load balancers
  );

  // Generator for utilization metrics
  const utilizationMetricsGenerator = fc.record({
    cpu: fc.array(fc.float({ min: 0, max: 100, noNaN: true }), { minLength: 1, maxLength: 100 }),
    memory: fc.array(fc.float({ min: 0, max: 100, noNaN: true }), { minLength: 1, maxLength: 100 }),
    network: fc.array(fc.float({ min: 0, max: 1000, noNaN: true }), { minLength: 1, maxLength: 100 }),
    storage: fc.array(fc.float({ min: 0, max: 100, noNaN: true }), { minLength: 1, maxLength: 100 }),
    timeRange: fc.record({
      start: fc.integer({ min: new Date('2020-01-01').getTime(), max: new Date('2024-12-31').getTime() }).map(timestamp => new Date(timestamp).toISOString()),
      end: fc.integer({ min: new Date('2020-01-01').getTime(), max: new Date('2024-12-31').getTime() }).map(timestamp => new Date(timestamp).toISOString())
    }),
    samplingInterval: fc.constantFrom('1m', '5m', '15m', '1h')
  });

  describe('Property 1: Comprehensive Resource Discovery', () => {
    
    /**
     * **Validates: Requirements 1.1, 1.2, 1.3**
     * For any AWS environment with resources across multiple services, 
     * the ResourceInventory model should discover all resources, collect 
     * complete usage metrics and configuration data, and store them with 
     * proper timestamps and regional information.
     */
    test('ResourceInventory should maintain completeness for all AWS service types', () => {
      fc.assert(fc.property(
        resourceIdGenerator,
        awsResourceTypes,
        awsRegions,
        fc.float({ min: 0, max: 10000, noNaN: true }),
        utilizationMetricsGenerator,
        fc.array(fc.string({ minLength: 1, maxLength: 50 }), { maxLength: 10 }),
        (resourceId, resourceType, region, currentCost, utilizationMetrics, optimizationOpportunities) => {
          
          // Create ResourceInventory with generated data
          const resource = new ResourceInventory({
            resourceId,
            resourceType,
            region,
            currentCost,
            utilizationMetrics,
            optimizationOpportunities
          });

          // Validate that all required fields are present and properly typed
          expect(resource.resourceId).toBe(resourceId);
          expect(resource.resourceType).toBe(resourceType);
          expect(resource.region).toBe(region);
          expect(resource.currentCost).toBe(currentCost);
          expect(resource.timestamp).toBeDefined();
          expect(typeof resource.timestamp).toBe('string');
          
          // Validate utilization metrics structure
          expect(resource.utilizationMetrics).toBeDefined();
          expect(Array.isArray(resource.utilizationMetrics.cpu)).toBe(true);
          expect(Array.isArray(resource.utilizationMetrics.memory)).toBe(true);
          expect(Array.isArray(resource.utilizationMetrics.network)).toBe(true);
          expect(Array.isArray(resource.utilizationMetrics.storage)).toBe(true);
          
          // Validate optimization opportunities
          expect(Array.isArray(resource.optimizationOpportunities)).toBe(true);
          
          // Validate model validation passes for complete data
          const validation = resource.validate();
          expect(validation.isValid).toBe(true);
          expect(validation.errors.length).toBe(0);
          
          // Validate JSON serialization works
          const json = resource.toJSON();
          expect(json.resourceId).toBe(resourceId);
          expect(json.resourceType).toBe(resourceType);
          expect(json.region).toBe(region);
          expect(json.currentCost).toBe(currentCost);
          
          // Validate that JSON can be round-tripped
          const reconstructed = ResourceInventory.fromJSON(json);
          expect(reconstructed.resourceId).toBe(resourceId);
          expect(reconstructed.resourceType).toBe(resourceType);
          expect(reconstructed.region).toBe(region);
        }
      ), { numRuns: 100 });
    });

    /**
     * **Validates: Requirements 1.1, 1.2, 1.3**
     * For any cost optimization recommendation, the CostOptimization model 
     * should maintain complete data including risk assessment, approval workflow, 
     * and savings calculations.
     */
    test('CostOptimization should maintain completeness for all optimization types', () => {
      fc.assert(fc.property(
        resourceIdGenerator,
        awsRegions,
        optimizationTypes,
        fc.float({ min: 0, max: 10000, noNaN: true }),
        fc.float({ min: 0, max: 10000, noNaN: true }),
        fc.float({ min: 0, max: 100, noNaN: true }),
        riskLevels,
        (resourceId, region, optimizationType, currentCost, projectedCost, confidenceScore, riskLevel) => {
          
          // Ensure projectedCost is less than or equal to currentCost for positive savings
          const adjustedProjectedCost = Math.min(projectedCost, currentCost);
          const estimatedSavings = Math.max(0, currentCost - adjustedProjectedCost);
          
          const optimization = new CostOptimization({
            resourceId,
            region,
            optimizationType,
            currentCost,
            projectedCost: adjustedProjectedCost,
            estimatedSavings,
            confidenceScore,
            riskLevel
          });

          // Validate all required fields are present
          expect(optimization.resourceId).toBe(resourceId);
          expect(optimization.region).toBe(region);
          expect(optimization.optimizationType).toBe(optimizationType);
          expect(optimization.currentCost).toBe(currentCost);
          expect(optimization.projectedCost).toBe(adjustedProjectedCost);
          expect(optimization.estimatedSavings).toBe(estimatedSavings);
          expect(optimization.confidenceScore).toBe(confidenceScore);
          expect(optimization.riskLevel).toBe(riskLevel);
          expect(optimization.optimizationId).toBeDefined();
          expect(optimization.timestamp).toBeDefined();
          
          // Validate approval workflow fields
          expect(typeof optimization.approvalRequired).toBe('boolean');
          expect(['pending', 'approved', 'executed', 'rolled_back', 'rejected']).toContain(optimization.status);
          
          // Validate savings calculation
          const savingsPercentage = optimization.getSavingsPercentage();
          expect(typeof savingsPercentage).toBe('number');
          expect(savingsPercentage).toBeGreaterThanOrEqual(0);
          
          // Validate model validation passes
          const validation = optimization.validate();
          expect(validation.isValid).toBe(true);
          
          // Validate JSON serialization
          const json = optimization.toJSON();
          expect(json.resourceId).toBe(resourceId);
          expect(json.optimizationType).toBe(optimizationType);
          expect(json.riskLevel).toBe(riskLevel);
        }
      ), { numRuns: 100 });
    });

    /**
     * **Validates: Requirements 1.1, 1.2, 1.3**
     * For any detected cost anomaly, the CostAnomaly model should maintain 
     * complete data including root cause analysis, severity assessment, 
     * and affected resources.
     */
    test('CostAnomaly should maintain completeness for all anomaly types', () => {
      fc.assert(fc.property(
        awsResourceTypes,
        awsRegions,
        anomalyTypes,
        severityLevels,
        fc.float({ min: 0, max: 10000, noNaN: true }),
        fc.float({ min: 0, max: 50000, noNaN: true }),
        fc.float({ min: 0, max: 100, noNaN: true }),
        (serviceType, region, anomalyType, severity, baselineCost, actualCost, analysisConfidence) => {
          
          const anomaly = new CostAnomaly({
            serviceType,
            region,
            anomalyType,
            severity,
            baselineCost,
            actualCost,
            analysisConfidence
          });

          // Validate all required fields are present
          expect(anomaly.serviceType).toBe(serviceType);
          expect(anomaly.region).toBe(region);
          expect(anomaly.anomalyType).toBe(anomalyType);
          expect(anomaly.severity).toBe(severity);
          expect(anomaly.baselineCost).toBe(baselineCost);
          expect(anomaly.actualCost).toBe(actualCost);
          expect(anomaly.analysisConfidence).toBe(analysisConfidence);
          expect(anomaly.anomalyId).toBeDefined();
          expect(anomaly.timestamp).toBeDefined();
          expect(anomaly.detectedAt).toBeDefined();
          
          // Validate deviation calculations
          const deviationPercentage = anomaly.calculateDeviationPercentage();
          const deviationAmount = anomaly.calculateDeviationAmount();
          expect(typeof deviationPercentage).toBe('number');
          expect(typeof deviationAmount).toBe('number');
          
          // Validate severity determination
          const determinedSeverity = anomaly.determineSeverity();
          expect(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']).toContain(determinedSeverity);
          
          // Validate arrays for affected resources and contributing factors
          expect(Array.isArray(anomaly.affectedResources)).toBe(true);
          expect(Array.isArray(anomaly.contributingFactors)).toBe(true);
          expect(Array.isArray(anomaly.recommendedActions)).toBe(true);
          
          // Validate model validation passes
          const validation = anomaly.validate();
          expect(validation.isValid).toBe(true);
          
          // Validate JSON serialization
          const json = anomaly.toJSON();
          expect(json.serviceType).toBe(serviceType);
          expect(json.anomalyType).toBe(anomalyType);
          expect(json.severity).toBe(severity);
        }
      ), { numRuns: 100 });
    });

    /**
     * **Validates: Requirements 1.1, 1.2, 1.3**
     * For any budget forecast, the BudgetForecast model should maintain 
     * complete data including hierarchical budget support, confidence intervals, 
     * and variance tracking.
     */
    test('BudgetForecast should maintain completeness for all budget categories', () => {
      fc.assert(fc.property(
        budgetCategories,
        fc.string({ minLength: 3, maxLength: 50 }).filter(s => s.trim().length >= 3),
        awsRegions,
        fc.float({ min: 0, max: 100000, noNaN: true }),
        fc.float({ min: 0, max: 150000, noNaN: true }),
        fc.float({ min: 0, max: 200000, noNaN: true }),
        fc.constantFrom('1W', '1M', '3M', '6M', '1Y'),
        (budgetCategory, budgetName, region, currentSpend, forecastedSpend, budgetLimit, projectionPeriod) => {
          
          const forecast = new BudgetForecast({
            budgetCategory,
            budgetName,
            region,
            currentSpend,
            forecastedSpend,
            budgetLimit,
            projectionPeriod
          });

          // Validate all required fields are present
          expect(forecast.budgetCategory).toBe(budgetCategory);
          expect(forecast.budgetName).toBe(budgetName);
          expect(forecast.region).toBe(region);
          expect(forecast.currentSpend).toBe(currentSpend);
          expect(forecast.forecastedSpend).toBe(forecastedSpend);
          expect(forecast.budgetLimit).toBe(budgetLimit);
          expect(forecast.projectionPeriod).toBe(projectionPeriod);
          expect(forecast.forecastId).toBeDefined();
          expect(forecast.timestamp).toBeDefined();
          
          // Validate confidence interval structure
          expect(forecast.confidenceInterval).toBeDefined();
          expect(typeof forecast.confidenceInterval.lower).toBe('number');
          expect(typeof forecast.confidenceInterval.upper).toBe('number');
          expect(typeof forecast.confidenceInterval.confidence).toBe('number');
          
          // Validate budget calculations
          const utilization = forecast.getBudgetUtilization();
          const forecastedUtilization = forecast.getForecastedUtilization();
          const remainingBudget = forecast.calculateRemainingBudget();
          
          expect(typeof utilization).toBe('number');
          expect(typeof forecastedUtilization).toBe('number');
          expect(typeof remainingBudget).toBe('number');
          expect(remainingBudget).toBeGreaterThanOrEqual(0);
          
          // Validate variance calculation
          const variance = forecast.calculateVariance();
          expect(variance).toBeDefined();
          expect(typeof variance.amount).toBe('number');
          expect(typeof variance.percentage).toBe('number');
          expect(['favorable', 'unfavorable', 'neutral']).toContain(variance.type);
          
          // Validate risk assessment
          const riskAssessment = forecast.assessBudgetRisk();
          expect(riskAssessment).toBeDefined();
          expect(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']).toContain(riskAssessment.riskLevel);
          expect(typeof riskAssessment.message).toBe('string');
          
          // Validate hierarchical budget support
          expect(Array.isArray(forecast.childBudgets)).toBe(true);
          expect(Array.isArray(forecast.allocationRules)).toBe(true);
          
          // Validate model validation passes
          const validation = forecast.validate();
          expect(validation.isValid).toBe(true);
          
          // Validate JSON serialization
          const json = forecast.toJSON();
          expect(json.budgetCategory).toBe(budgetCategory);
          expect(json.budgetName).toBe(budgetName);
          expect(json.region).toBe(region);
        }
      ), { numRuns: 100 });
    });

    /**
     * **Validates: Requirements 1.1, 1.2, 1.3**
     * For any combination of AWS resources across multiple services and regions,
     * all data models should maintain consistency in required fields and 
     * support comprehensive resource discovery.
     */
    test('All models should maintain cross-service consistency', () => {
      fc.assert(fc.property(
        fc.array(awsResourceTypes, { minLength: 2, maxLength: 7 }).map(arr => [...new Set(arr)]).filter(arr => arr.length >= 2),
        fc.array(awsRegions, { minLength: 1, maxLength: 5 }).map(arr => [...new Set(arr)]),
        (resourceTypes, regions) => {
          
          const resources = [];
          const optimizations = [];
          const anomalies = [];
          const forecasts = [];
          
          // Create instances of each model for each resource type and region combination
          resourceTypes.forEach((resourceType, typeIndex) => {
            regions.forEach((region, regionIndex) => {
              const resourceId = `${resourceType}-${typeIndex}-${regionIndex}`;
              
              // Create ResourceInventory
              const resource = new ResourceInventory({
                resourceId,
                resourceType,
                region,
                currentCost: Math.random() * 1000
              });
              resources.push(resource);
              
              // Create CostOptimization
              const optimization = new CostOptimization({
                resourceId,
                region,
                optimizationType: 'rightsizing',
                currentCost: Math.random() * 1000,
                projectedCost: Math.random() * 800,
                estimatedSavings: Math.random() * 200
              });
              optimizations.push(optimization);
              
              // Create CostAnomaly
              const anomaly = new CostAnomaly({
                serviceType: resourceType,
                region,
                anomalyType: 'spike',
                baselineCost: Math.random() * 500,
                actualCost: Math.random() * 1500
              });
              anomalies.push(anomaly);
              
              // Create BudgetForecast (one per region)
              if (typeIndex === 0) {
                const forecast = new BudgetForecast({
                  budgetCategory: 'team',
                  budgetName: `Team Budget ${region}`,
                  region,
                  currentSpend: Math.random() * 10000,
                  forecastedSpend: Math.random() * 12000,
                  budgetLimit: Math.random() * 15000 + 10000
                });
                forecasts.push(forecast);
              }
            });
          });
          
          // Validate all models have consistent required fields
          [...resources, ...optimizations, ...anomalies, ...forecasts].forEach(model => {
            expect(model.timestamp).toBeDefined();
            expect(typeof model.timestamp).toBe('string');
            expect(model.region).toBeDefined();
            expect(typeof model.region).toBe('string');
            expect(regions).toContain(model.region);
            
            // Validate all models can be serialized to JSON
            expect(() => JSON.stringify(model.toJSON())).not.toThrow();
            
            // Validate all models pass validation
            const validation = model.validate();
            expect(validation.isValid).toBe(true);
          });
          
          // Validate resource discovery completeness
          const discoveredResourceTypes = [...new Set(resources.map(r => r.resourceType))];
          expect(discoveredResourceTypes.length).toBe(resourceTypes.length);
          expect(discoveredResourceTypes.sort()).toEqual(resourceTypes.sort());
          
          const discoveredRegions = [...new Set(resources.map(r => r.region))];
          expect(discoveredRegions.length).toBe(regions.length);
          expect(discoveredRegions.sort()).toEqual(regions.sort());
        }
      ), { numRuns: 50 });
    });
  });
});