/**
 * Simple Property-Based Test for Data Model Completeness
 * 
 * **Feature: advanced-finops-platform, Property 1: Comprehensive Resource Discovery**
 * **Validates: Requirements 1.1, 1.2, 1.3**
 */

const fc = require('fast-check');
const { ResourceInventory, CostOptimization, CostAnomaly, BudgetForecast } = require('./index');

describe('Simple Property-Based Tests: Data Model Completeness', () => {
  
  test('ResourceInventory should maintain required fields for any valid input', () => {
    fc.assert(fc.property(
      fc.string({ minLength: 1, maxLength: 20 }),
      fc.constantFrom('ec2', 'rds', 'lambda', 's3'),
      fc.constantFrom('us-east-1', 'us-west-2', 'eu-west-1'),
      fc.float({ min: 0, max: 1000, noNaN: true }),
      (resourceId, resourceType, region, currentCost) => {
        
        const resource = new ResourceInventory({
          resourceId,
          resourceType,
          region,
          currentCost
        });

        // Validate required fields are present
        expect(resource.resourceId).toBe(resourceId);
        expect(resource.resourceType).toBe(resourceType);
        expect(resource.region).toBe(region);
        expect(resource.currentCost).toBe(currentCost);
        expect(resource.timestamp).toBeDefined();
        
        // Validate model validation passes
        const validation = resource.validate();
        expect(validation.isValid).toBe(true);
      }
    ), { numRuns: 20 });
  });

  test('All models should have consistent timestamp and region fields', () => {
    fc.assert(fc.property(
      fc.constantFrom('us-east-1', 'us-west-2'),
      (region) => {
        
        const resource = new ResourceInventory({ 
          resourceId: 'test-id', 
          resourceType: 'ec2', 
          region 
        });
        
        const optimization = new CostOptimization({ 
          resourceId: 'test-id', 
          region, 
          optimizationType: 'rightsizing' 
        });
        
        const anomaly = new CostAnomaly({ 
          serviceType: 'ec2', 
          region, 
          anomalyType: 'spike' 
        });
        
        const forecast = new BudgetForecast({ 
          budgetCategory: 'team', 
          budgetName: 'test', 
          region 
        });

        // All models should have timestamp and region
        [resource, optimization, anomaly, forecast].forEach(model => {
          expect(model.timestamp).toBeDefined();
          expect(typeof model.timestamp).toBe('string');
          expect(model.region).toBe(region);
        });
      }
    ), { numRuns: 10 });
  });
});