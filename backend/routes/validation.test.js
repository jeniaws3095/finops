/**
 * Data Validation Unit Tests
 * 
 * Focused tests for data model validation and input sanitization.
 * Tests edge cases, boundary conditions, and security considerations.
 * 
 * Requirements: 9.1
 */

const request = require('supertest');
const app = require('../server');

describe('Data Validation Tests', () => {
  
  describe('Resource Data Validation', () => {
    test('should reject empty resourceId', async () => {
      const invalidData = {
        resourceId: '',
        resourceType: 'ec2',
        region: 'us-east-1'
      };

      const response = await request(app)
        .post('/api/resources')
        .send(invalidData)
        .expect(400);
      
      expect(response.body.errors).toContain('resourceId is required');
    });

    test('should reject whitespace-only resourceId', async () => {
      const invalidData = {
        resourceId: '   ',
        resourceType: 'ec2',
        region: 'us-east-1'
      };

      const response = await request(app)
        .post('/api/resources')
        .send(invalidData)
        .expect(400);
      
      expect(response.body.errors).toContain('resourceId is required');
    });

    test('should reject invalid resourceType', async () => {
      const invalidData = {
        resourceId: 'i-test123',
        resourceType: 'invalid-service',
        region: 'us-east-1'
      };

      const response = await request(app)
        .post('/api/resources')
        .send(invalidData)
        .expect(400);
      
      expect(response.body.errors).toEqual(
        expect.arrayContaining([
          expect.stringContaining('resourceType must be one of')
        ])
      );
    });

    test('should accept all valid resourceTypes', async () => {
      const validTypes = ['ec2', 'rds', 'lambda', 's3', 'ebs', 'elb', 'cloudwatch'];
      
      for (const resourceType of validTypes) {
        const validData = {
          resourceId: `test-${resourceType}-${Date.now()}`,
          resourceType: resourceType,
          region: 'us-east-1',
          currentCost: 50
        };

        const response = await request(app)
          .post('/api/resources')
          .send(validData)
          .expect(200);
        
        expect(response.body.data.resourceType).toBe(resourceType);
      }
    });

    test('should validate currentCost as number', async () => {
      const invalidData = {
        resourceId: 'i-test123',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 'not-a-number'
      };

      const response = await request(app)
        .post('/api/resources')
        .send(invalidData)
        .expect(400);
      
      expect(response.body.errors).toEqual(
        expect.arrayContaining([
          expect.stringContaining('currentCost must be a non-negative number')
        ])
      );
    });

    test('should reject negative currentCost', async () => {
      const invalidData = {
        resourceId: 'i-test123',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: -100
      };

      const response = await request(app)
        .post('/api/resources')
        .send(invalidData)
        .expect(400);
      
      expect(response.body.errors).toEqual(
        expect.arrayContaining([
          expect.stringContaining('currentCost must be a non-negative number')
        ])
      );
    });

    test('should accept zero currentCost', async () => {
      const validData = {
        resourceId: 'i-zero-cost',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 0
      };

      const response = await request(app)
        .post('/api/resources')
        .send(validData)
        .expect(200);
      
      expect(response.body.data.currentCost).toBe(0);
    });
  });

  describe('Optimization Data Validation', () => {
    test('should reject empty resourceId', async () => {
      const invalidData = {
        resourceId: '',
        optimizationType: 'rightsizing',
        currentCost: 100,
        projectedCost: 60,
        estimatedSavings: 40
      };

      const response = await request(app)
        .post('/api/optimizations')
        .send(invalidData)
        .expect(400);
      
      expect(response.body.errors).toContain('resourceId is required');
    });

    test('should reject invalid optimizationType', async () => {
      const invalidData = {
        resourceId: 'i-test123',
        optimizationType: 'invalid-type',
        currentCost: 100,
        projectedCost: 60,
        estimatedSavings: 40
      };

      const response = await request(app)
        .post('/api/optimizations')
        .send(invalidData)
        .expect(400);
      
      expect(response.body.errors).toEqual(
        expect.arrayContaining([
          expect.stringContaining('optimizationType must be one of')
        ])
      );
    });

    test('should accept all valid optimizationTypes', async () => {
      const validTypes = ['rightsizing', 'pricing', 'cleanup', 'scheduling'];
      
      for (const optimizationType of validTypes) {
        const validData = {
          resourceId: `i-opt-${optimizationType}-${Date.now()}`,
          optimizationType: optimizationType,
          currentCost: 100,
          projectedCost: 60,
          estimatedSavings: 40,
          confidenceScore: 85,
          riskLevel: 'LOW'
        };

        const response = await request(app)
          .post('/api/optimizations')
          .send(validData)
          .expect(200);
        
        expect(response.body.data.optimizationType).toBe(optimizationType);
      }
    });

    test('should reject invalid riskLevel', async () => {
      const invalidData = {
        resourceId: 'i-test123',
        optimizationType: 'rightsizing',
        currentCost: 100,
        projectedCost: 60,
        estimatedSavings: 40,
        riskLevel: 'INVALID'
      };

      const response = await request(app)
        .post('/api/optimizations')
        .send(invalidData)
        .expect(400);
      
      expect(response.body.errors).toEqual(
        expect.arrayContaining([
          expect.stringContaining('riskLevel must be one of')
        ])
      );
    });

    test('should accept all valid riskLevels', async () => {
      const validLevels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
      
      for (const riskLevel of validLevels) {
        const validData = {
          resourceId: `i-risk-${riskLevel.toLowerCase()}-${Date.now()}`,
          optimizationType: 'rightsizing',
          currentCost: 100,
          projectedCost: 60,
          estimatedSavings: 40,
          confidenceScore: 85,
          riskLevel: riskLevel
        };

        const response = await request(app)
          .post('/api/optimizations')
          .send(validData)
          .expect(200);
        
        expect(response.body.data.riskLevel).toBe(riskLevel);
      }
    });

    test('should validate confidenceScore range', async () => {
      const testCases = [
        { score: -1, shouldFail: true },
        { score: 0, shouldFail: false },
        { score: 50, shouldFail: false },
        { score: 100, shouldFail: false },
        { score: 101, shouldFail: true },
        { score: 'invalid', shouldFail: true }
      ];

      for (const testCase of testCases) {
        const data = {
          resourceId: `i-confidence-${Date.now()}`,
          optimizationType: 'rightsizing',
          currentCost: 100,
          projectedCost: 60,
          estimatedSavings: 40,
          confidenceScore: testCase.score,
          riskLevel: 'LOW'
        };

        const response = await request(app)
          .post('/api/optimizations')
          .send(data);
        
        if (testCase.shouldFail) {
          expect(response.status).toBe(400);
          expect(response.body.errors).toEqual(
            expect.arrayContaining([
              expect.stringContaining('confidenceScore must be a number between 0 and 100')
            ])
          );
        } else {
          expect(response.status).toBe(200);
          expect(response.body.data.confidenceScore).toBe(testCase.score);
        }
      }
    });

    test('should validate cost fields as non-negative numbers', async () => {
      const testCases = [
        { field: 'currentCost', value: -50 },
        { field: 'projectedCost', value: -25 },
        { field: 'currentCost', value: 'invalid' },
        { field: 'projectedCost', value: 'invalid' }
      ];

      for (const testCase of testCases) {
        const data = {
          resourceId: `i-cost-validation-${Date.now()}`,
          optimizationType: 'rightsizing',
          currentCost: 100,
          projectedCost: 60,
          estimatedSavings: 40,
          confidenceScore: 85,
          riskLevel: 'LOW'
        };

        data[testCase.field] = testCase.value;

        const response = await request(app)
          .post('/api/optimizations')
          .send(data)
          .expect(400);
        
        expect(response.body.errors).toEqual(
          expect.arrayContaining([
            expect.stringContaining(`${testCase.field} must be a non-negative number`)
          ])
        );
      }
    });
  });

  describe('Input Sanitization', () => {
    test('should handle SQL injection attempts gracefully', async () => {
      const maliciousData = {
        resourceId: "'; DROP TABLE resources; --",
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 100
      };

      const response = await request(app)
        .post('/api/resources')
        .send(maliciousData)
        .expect(200);
      
      // Should store the data as-is (since we're using in-memory storage, not SQL)
      expect(response.body.data.resourceId).toBe("'; DROP TABLE resources; --");
    });

    test('should handle XSS attempts in descriptions', async () => {
      const maliciousData = {
        resourceId: 'i-xss-test',
        optimizationType: 'rightsizing',
        currentCost: 100,
        projectedCost: 60,
        estimatedSavings: 40,
        confidenceScore: 85,
        riskLevel: 'LOW',
        description: '<script>alert("XSS")</script>'
      };

      const response = await request(app)
        .post('/api/optimizations')
        .send(maliciousData)
        .expect(200);
      
      // Should store the data as-is (XSS protection should be handled by frontend)
      expect(response.body.data.description).toBe('<script>alert("XSS")</script>');
    });

    test('should handle very long strings', async () => {
      const longString = 'a'.repeat(10000);
      const data = {
        resourceId: 'i-long-string',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 100,
        resourceName: longString
      };

      const response = await request(app)
        .post('/api/resources')
        .send(data);
      
      // Should either accept or reject gracefully
      expect([200, 400, 413]).toContain(response.status);
      expect(response.body).toHaveProperty('success');
    });

    test('should handle null bytes in strings', async () => {
      const data = {
        resourceId: 'i-null-byte\x00test',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 100
      };

      const response = await request(app)
        .post('/api/resources')
        .send(data);
      
      expect([200, 400]).toContain(response.status);
      expect(response.body).toHaveProperty('success');
    });
  });

  describe('Boundary Value Testing', () => {
    test('should handle maximum safe integer values', async () => {
      const data = {
        resourceId: 'i-max-int',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: Number.MAX_SAFE_INTEGER
      };

      const response = await request(app)
        .post('/api/resources')
        .send(data);
      
      expect([200, 400]).toContain(response.status);
      expect(response.body).toHaveProperty('success');
    });

    test('should handle floating point precision', async () => {
      const data = {
        resourceId: 'i-float-precision',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 123.456789012345
      };

      const response = await request(app)
        .post('/api/resources')
        .send(data)
        .expect(200);
      
      // Should handle floating point numbers appropriately
      expect(typeof response.body.data.currentCost).toBe('number');
    });

    test('should handle edge case confidence scores', async () => {
      const edgeCases = [0, 0.1, 99.9, 100];
      
      for (const score of edgeCases) {
        const data = {
          resourceId: `i-edge-confidence-${score}`,
          optimizationType: 'rightsizing',
          currentCost: 100,
          projectedCost: 60,
          estimatedSavings: 40,
          confidenceScore: score,
          riskLevel: 'LOW'
        };

        const response = await request(app)
          .post('/api/optimizations')
          .send(data)
          .expect(200);
        
        expect(response.body.data.confidenceScore).toBe(score);
      }
    });
  });
});