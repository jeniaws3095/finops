/**
 * API Routes Unit Tests
 * 
 * Comprehensive tests for resource management and optimization API endpoints.
 * Validates endpoint response formats, error handling, data storage, and edge cases.
 * 
 * Requirements: 9.1, 8.1, 8.3
 */

const request = require('supertest');
const app = require('../server');

// Test data generators for consistent test data
const generateResourceData = (overrides = {}) => ({
  resourceId: 'i-test' + Date.now(),
  resourceType: 'ec2',
  region: 'us-east-1',
  currentCost: 100.00,
  state: 'running',
  utilizationMetrics: {
    cpu: [25.5, 30.2, 28.1],
    memory: [60.2, 65.8, 62.3],
    network: [10.5, 12.3, 11.8],
    storage: [45.2, 47.1, 46.5]
  },
  optimizationOpportunities: ['rightsizing'],
  tags: { Environment: 'test', Team: 'finops' },
  ...overrides
});

const generateOptimizationData = (overrides = {}) => ({
  resourceId: 'i-opt' + Date.now(),
  region: 'us-east-1',
  optimizationType: 'rightsizing',
  currentCost: 100,
  projectedCost: 60,
  estimatedSavings: 40,
  confidenceScore: 85,
  riskLevel: 'LOW',
  description: 'Test optimization',
  ...overrides
});

describe('Advanced FinOps Platform API Routes', () => {
  
  describe('Health and Documentation Endpoints', () => {
    test('GET /health should return server status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        message: expect.stringContaining('Advanced FinOps Platform API is running'),
        timestamp: expect.any(String),
        port: 5002
      });
    });

    test('GET /api/health should return API health status', async () => {
      const response = await request(app)
        .get('/api/health')
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        message: expect.stringContaining('Advanced FinOps Platform API is healthy'),
        timestamp: expect.any(String),
        version: '1.0.0',
        endpoints: expect.arrayContaining([
          '/api/resources',
          '/api/optimizations'
        ])
      });
    });

    test('GET /api/docs should return API documentation', async () => {
      const response = await request(app)
        .get('/api/docs')
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        message: expect.stringContaining('API Documentation'),
        timestamp: expect.any(String),
        endpoints: expect.objectContaining({
          '/api/resources': expect.any(Object),
          '/api/optimizations': expect.any(Object)
        })
      });
    });
  });

  describe('Resource Management Endpoints', () => {
    test('GET /api/resources should return empty array initially', async () => {
      const response = await request(app)
        .get('/api/resources')
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: [],
        message: expect.stringContaining('Retrieved 0 resources'),
        metadata: {
          total: 0,
          limit: 100,
          offset: 0,
          hasMore: false
        },
        timestamp: expect.any(String)
      });
    });

    test('POST /api/resources should create new resource with valid data', async () => {
      const resourceData = generateResourceData({
        resourceId: 'i-1234567890abcdef0',
        currentCost: 150.50
      });

      const response = await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          resourceId: 'i-1234567890abcdef0',
          resourceType: 'ec2',
          region: 'us-east-1',
          currentCost: 150.50,
          timestamp: expect.any(String)
        }),
        message: expect.stringContaining('Resource added successfully'),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/resources should validate required fields', async () => {
      const invalidResourceData = {
        resourceType: 'ec2',
        region: 'us-east-1'
        // Missing required resourceId
      };

      const response = await request(app)
        .post('/api/resources')
        .send(invalidResourceData)
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid resource data'),
        errors: expect.arrayContaining([
          expect.stringContaining('resourceId is required')
        ]),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/resources should validate resourceType enum', async () => {
      const invalidResourceData = generateResourceData({
        resourceType: 'invalid-type'
      });

      const response = await request(app)
        .post('/api/resources')
        .send(invalidResourceData)
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid resource data'),
        errors: expect.arrayContaining([
          expect.stringContaining('resourceType must be one of')
        ]),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/resources should validate currentCost as non-negative number', async () => {
      const invalidResourceData = generateResourceData({
        currentCost: -50
      });

      const response = await request(app)
        .post('/api/resources')
        .send(invalidResourceData)
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid resource data'),
        errors: expect.arrayContaining([
          expect.stringContaining('currentCost must be a non-negative number')
        ]),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/resources should update existing resource', async () => {
      const resourceData = generateResourceData({
        resourceId: 'i-update-test',
        currentCost: 100
      });

      // Create initial resource
      await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(200);

      // Update the same resource
      const updatedData = { ...resourceData, currentCost: 150 };
      const response = await request(app)
        .post('/api/resources')
        .send(updatedData)
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          resourceId: 'i-update-test',
          currentCost: 150
        }),
        message: expect.stringContaining('Resource updated successfully'),
        timestamp: expect.any(String)
      });
    });

    test('GET /api/resources should return created resources', async () => {
      // Create multiple resources
      const resource1 = generateResourceData({
        resourceId: 'i-test123',
        resourceType: 'ec2',
        region: 'us-west-2',
        currentCost: 75.25
      });

      const resource2 = generateResourceData({
        resourceId: 'db-test456',
        resourceType: 'rds',
        region: 'us-east-1',
        currentCost: 200.00
      });

      await request(app).post('/api/resources').send(resource1).expect(200);
      await request(app).post('/api/resources').send(resource2).expect(200);

      // Retrieve all resources
      const response = await request(app)
        .get('/api/resources')
        .expect(200);
      
      expect(response.body.data.length).toBeGreaterThanOrEqual(2);
      expect(response.body.data).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            resourceId: 'i-test123',
            resourceType: 'ec2',
            region: 'us-west-2'
          }),
          expect.objectContaining({
            resourceId: 'db-test456',
            resourceType: 'rds',
            region: 'us-east-1'
          })
        ])
      );
    });

    test('GET /api/resources with resourceType filter should work correctly', async () => {
      const response = await request(app)
        .get('/api/resources?resourceType=ec2')
        .expect(200);
      
      response.body.data.forEach(resource => {
        expect(resource.resourceType).toBe('ec2');
      });
    });

    test('GET /api/resources with region filter should work correctly', async () => {
      const response = await request(app)
        .get('/api/resources?region=us-west-2')
        .expect(200);
      
      response.body.data.forEach(resource => {
        expect(resource.region).toBe('us-west-2');
      });
    });

    test('GET /api/resources with state filter should work correctly', async () => {
      const response = await request(app)
        .get('/api/resources?state=running')
        .expect(200);
      
      response.body.data.forEach(resource => {
        expect(resource.state).toBe('running');
      });
    });

    test('GET /api/resources with pagination should work correctly', async () => {
      const response = await request(app)
        .get('/api/resources?limit=1&offset=0')
        .expect(200);
      
      expect(response.body.metadata.limit).toBe(1);
      expect(response.body.metadata.offset).toBe(0);
      expect(response.body.data.length).toBeLessThanOrEqual(1);
    });

    test('GET /api/resources/:resourceId should return specific resource', async () => {
      const resourceData = generateResourceData({
        resourceId: 'i-specific-test'
      });

      await request(app).post('/api/resources').send(resourceData).expect(200);

      const response = await request(app)
        .get('/api/resources/i-specific-test')
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          resourceId: 'i-specific-test'
        }),
        message: expect.stringContaining('Resource retrieved successfully'),
        timestamp: expect.any(String)
      });
    });

    test('GET /api/resources/:resourceId should return 404 for non-existent resource', async () => {
      const response = await request(app)
        .get('/api/resources/i-nonexistent')
        .expect(404);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Resource not found'),
        timestamp: expect.any(String)
      });
    });

    test('DELETE /api/resources/:resourceId should remove resource', async () => {
      const resourceData = generateResourceData({
        resourceId: 'i-delete-test'
      });

      await request(app).post('/api/resources').send(resourceData).expect(200);

      const response = await request(app)
        .delete('/api/resources/i-delete-test')
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          resourceId: 'i-delete-test'
        }),
        message: expect.stringContaining('Resource removed successfully'),
        timestamp: expect.any(String)
      });

      // Verify resource is actually deleted
      await request(app)
        .get('/api/resources/i-delete-test')
        .expect(404);
    });

    test('DELETE /api/resources/:resourceId should return 404 for non-existent resource', async () => {
      const response = await request(app)
        .delete('/api/resources/i-nonexistent')
        .expect(404);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Resource not found'),
        timestamp: expect.any(String)
      });
    });

    test('GET /api/resources/stats/summary should return accurate statistics', async () => {
      const response = await request(app)
        .get('/api/resources/stats/summary')
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          totalResources: expect.any(Number),
          byType: expect.any(Object),
          byRegion: expect.any(Object),
          byState: expect.any(Object),
          totalCost: expect.any(Number),
          optimizationOpportunities: expect.any(Number)
        }),
        message: expect.stringContaining('Resource statistics retrieved successfully'),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/resources should handle malformed JSON gracefully', async () => {
      const response = await request(app)
        .post('/api/resources')
        .send('invalid json')
        .expect(400);
      
      expect(response.body.success).toBe(false);
    });

    test('POST /api/resources should handle empty request body', async () => {
      const response = await request(app)
        .post('/api/resources')
        .send({})
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid resource data'),
        timestamp: expect.any(String)
      });
    });
  });

  describe('Optimization Management Endpoints', () => {
    test('GET /api/optimizations should return empty array initially', async () => {
      const response = await request(app)
        .get('/api/optimizations')
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: [],
        message: expect.stringContaining('Retrieved 0 optimization recommendations'),
        metadata: {
          total: 0,
          limit: 100,
          offset: 0,
          hasMore: false,
          totalSavings: 0
        },
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations should create new optimization with valid data', async () => {
      const optimizationData = generateOptimizationData({
        resourceId: 'i-1234567890abcdef0',
        description: 'Right-size EC2 instance from m5.large to m5.medium'
      });

      const response = await request(app)
        .post('/api/optimizations')
        .send(optimizationData)
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          resourceId: 'i-1234567890abcdef0',
          optimizationType: 'rightsizing',
          currentCost: 100,
          projectedCost: 60,
          estimatedSavings: 40,
          confidenceScore: 85,
          riskLevel: 'LOW',
          status: 'pending',
          optimizationId: expect.any(String),
          timestamp: expect.any(String),
          savingsPercentage: 40
        }),
        message: expect.stringContaining('Optimization created successfully'),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations should validate required fields', async () => {
      const invalidOptimizationData = {
        region: 'us-east-1',
        currentCost: 100
        // Missing required resourceId and optimizationType
      };

      const response = await request(app)
        .post('/api/optimizations')
        .send(invalidOptimizationData)
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid optimization data'),
        errors: expect.arrayContaining([
          expect.stringContaining('resourceId is required'),
          expect.stringContaining('optimizationType is required')
        ]),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations should validate optimizationType enum', async () => {
      const invalidOptimizationData = generateOptimizationData({
        optimizationType: 'invalid-type'
      });

      const response = await request(app)
        .post('/api/optimizations')
        .send(invalidOptimizationData)
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid optimization data'),
        errors: expect.arrayContaining([
          expect.stringContaining('optimizationType must be one of')
        ]),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations should validate riskLevel enum', async () => {
      const invalidOptimizationData = generateOptimizationData({
        riskLevel: 'INVALID'
      });

      const response = await request(app)
        .post('/api/optimizations')
        .send(invalidOptimizationData)
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid optimization data'),
        errors: expect.arrayContaining([
          expect.stringContaining('riskLevel must be one of')
        ]),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations should validate confidenceScore range', async () => {
      const invalidOptimizationData = generateOptimizationData({
        confidenceScore: 150
      });

      const response = await request(app)
        .post('/api/optimizations')
        .send(invalidOptimizationData)
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid optimization data'),
        errors: expect.arrayContaining([
          expect.stringContaining('confidenceScore must be a number between 0 and 100')
        ]),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations should validate negative costs', async () => {
      const invalidOptimizationData = generateOptimizationData({
        currentCost: -50
      });

      const response = await request(app)
        .post('/api/optimizations')
        .send(invalidOptimizationData)
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid optimization data'),
        errors: expect.arrayContaining([
          expect.stringContaining('currentCost must be a non-negative number')
        ]),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations should update existing optimization', async () => {
      const optimizationData = generateOptimizationData({
        resourceId: 'i-update-opt-test',
        estimatedSavings: 50
      });

      // Create initial optimization
      await request(app)
        .post('/api/optimizations')
        .send(optimizationData)
        .expect(200);

      // Update the same optimization
      const updatedData = { ...optimizationData, estimatedSavings: 75 };
      const response = await request(app)
        .post('/api/optimizations')
        .send(updatedData)
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          resourceId: 'i-update-opt-test',
          estimatedSavings: 75
        }),
        message: expect.stringContaining('Optimization updated successfully'),
        timestamp: expect.any(String)
      });
    });

    test('GET /api/optimizations with filters should work correctly', async () => {
      // Create test optimizations with different properties
      const opt1 = generateOptimizationData({
        resourceId: 'i-filter-test-1',
        riskLevel: 'HIGH',
        optimizationType: 'cleanup',
        estimatedSavings: 200
      });

      const opt2 = generateOptimizationData({
        resourceId: 'i-filter-test-2',
        riskLevel: 'LOW',
        optimizationType: 'rightsizing',
        estimatedSavings: 50
      });

      await request(app).post('/api/optimizations').send(opt1).expect(200);
      await request(app).post('/api/optimizations').send(opt2).expect(200);

      // Test riskLevel filter
      const riskResponse = await request(app)
        .get('/api/optimizations?riskLevel=HIGH')
        .expect(200);
      
      riskResponse.body.data.forEach(opt => {
        expect(opt.riskLevel).toBe('HIGH');
      });

      // Test optimizationType filter
      const typeResponse = await request(app)
        .get('/api/optimizations?optimizationType=cleanup')
        .expect(200);
      
      typeResponse.body.data.forEach(opt => {
        expect(opt.optimizationType).toBe('cleanup');
      });

      // Test savings range filter
      const savingsResponse = await request(app)
        .get('/api/optimizations?minSavings=100')
        .expect(200);
      
      savingsResponse.body.data.forEach(opt => {
        expect(opt.estimatedSavings).toBeGreaterThanOrEqual(100);
      });
    });

    test('GET /api/optimizations with sorting should work correctly', async () => {
      const response = await request(app)
        .get('/api/optimizations?sortBy=estimatedSavings&sortOrder=desc')
        .expect(200);
      
      // Verify sorting (if there are multiple optimizations)
      if (response.body.data.length > 1) {
        for (let i = 0; i < response.body.data.length - 1; i++) {
          expect(response.body.data[i].estimatedSavings)
            .toBeGreaterThanOrEqual(response.body.data[i + 1].estimatedSavings);
        }
      }
    });

    test('GET /api/optimizations with pagination should work correctly', async () => {
      const response = await request(app)
        .get('/api/optimizations?limit=2&offset=0')
        .expect(200);
      
      expect(response.body.metadata.limit).toBe(2);
      expect(response.body.metadata.offset).toBe(0);
      expect(response.body.data.length).toBeLessThanOrEqual(2);
    });

    test('POST /api/optimizations/approve should approve optimizations', async () => {
      // First create an optimization
      const optimizationData = generateOptimizationData({
        resourceId: 'i-approval-test',
        optimizationType: 'cleanup',
        currentCost: 50,
        projectedCost: 0,
        estimatedSavings: 50,
        confidenceScore: 95,
        riskLevel: 'LOW',
        description: 'Terminate unused EC2 instance'
      });

      const createResponse = await request(app)
        .post('/api/optimizations')
        .send(optimizationData)
        .expect(200);

      const optimizationId = createResponse.body.data.optimizationId;

      // Then approve it
      const approvalData = {
        optimizationIds: [optimizationId],
        approvedBy: 'test@company.com',
        comments: 'Approved for testing'
      };

      const approvalResponse = await request(app)
        .post('/api/optimizations/approve')
        .send(approvalData)
        .expect(200);
      
      expect(approvalResponse.body).toMatchObject({
        success: true,
        data: {
          approved: expect.arrayContaining([
            expect.objectContaining({
              optimizationId: optimizationId,
              status: 'approved',
              approvedBy: 'test@company.com',
              approvedAt: expect.any(String)
            })
          ]),
          failed: []
        },
        message: expect.stringContaining('Approved 1 of 1 optimizations'),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations/approve should handle multiple optimizations', async () => {
      // Create multiple optimizations
      const opt1Data = generateOptimizationData({
        resourceId: 'i-multi-approve-1'
      });
      const opt2Data = generateOptimizationData({
        resourceId: 'i-multi-approve-2'
      });

      const response1 = await request(app).post('/api/optimizations').send(opt1Data).expect(200);
      const response2 = await request(app).post('/api/optimizations').send(opt2Data).expect(200);

      const optimizationIds = [
        response1.body.data.optimizationId,
        response2.body.data.optimizationId
      ];

      // Approve both
      const approvalData = {
        optimizationIds: optimizationIds,
        approvedBy: 'test@company.com'
      };

      const approvalResponse = await request(app)
        .post('/api/optimizations/approve')
        .send(approvalData)
        .expect(200);
      
      expect(approvalResponse.body.data.approved).toHaveLength(2);
      expect(approvalResponse.body.data.failed).toHaveLength(0);
    });

    test('POST /api/optimizations/approve should validate required fields', async () => {
      const invalidApprovalData = {
        approvedBy: 'test@company.com'
        // Missing required optimizationIds
      };

      const response = await request(app)
        .post('/api/optimizations/approve')
        .send(invalidApprovalData)
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('optimizationIds array is required'),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations/approve should handle non-existent optimizations', async () => {
      const approvalData = {
        optimizationIds: ['non-existent-id'],
        approvedBy: 'test@company.com'
      };

      const response = await request(app)
        .post('/api/optimizations/approve')
        .send(approvalData)
        .expect(200);
      
      expect(response.body.data.approved).toHaveLength(0);
      expect(response.body.data.failed).toHaveLength(1);
      expect(response.body.data.failed[0]).toMatchObject({
        optimizationId: 'non-existent-id',
        reason: 'Optimization not found'
      });
    });

    test('GET /api/optimizations/:optimizationId should return specific optimization', async () => {
      const optimizationData = generateOptimizationData({
        resourceId: 'i-specific-opt-test'
      });

      const createResponse = await request(app)
        .post('/api/optimizations')
        .send(optimizationData)
        .expect(200);

      const optimizationId = createResponse.body.data.optimizationId;

      const response = await request(app)
        .get(`/api/optimizations/${optimizationId}`)
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          optimizationId: optimizationId,
          resourceId: 'i-specific-opt-test'
        }),
        message: expect.stringContaining('Optimization retrieved successfully'),
        timestamp: expect.any(String)
      });
    });

    test('GET /api/optimizations/:optimizationId should return 404 for non-existent optimization', async () => {
      const response = await request(app)
        .get('/api/optimizations/nonexistent-id')
        .expect(404);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Optimization not found'),
        timestamp: expect.any(String)
      });
    });

    test('PUT /api/optimizations/:optimizationId/status should update optimization status', async () => {
      const optimizationData = generateOptimizationData({
        resourceId: 'i-status-test'
      });

      const createResponse = await request(app)
        .post('/api/optimizations')
        .send(optimizationData)
        .expect(200);

      const optimizationId = createResponse.body.data.optimizationId;

      // First approve the optimization
      await request(app)
        .post('/api/optimizations/approve')
        .send({
          optimizationIds: [optimizationId],
          approvedBy: 'test@company.com'
        })
        .expect(200);

      // Then update status to executed
      const statusUpdate = {
        status: 'executed',
        executionResult: {
          success: true,
          actualSavings: 45,
          executedAt: new Date().toISOString()
        }
      };

      const response = await request(app)
        .put(`/api/optimizations/${optimizationId}/status`)
        .send(statusUpdate)
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          optimizationId: optimizationId,
          status: 'executed',
          executionResult: expect.any(Object)
        }),
        message: expect.stringContaining('Optimization status updated to executed'),
        timestamp: expect.any(String)
      });
    });

    test('PUT /api/optimizations/:optimizationId/status should return 404 for non-existent optimization', async () => {
      const response = await request(app)
        .put('/api/optimizations/nonexistent-id/status')
        .send({ status: 'executed' })
        .expect(404);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Optimization not found'),
        timestamp: expect.any(String)
      });
    });

    test('GET /api/optimizations/stats/summary should return accurate statistics', async () => {
      const response = await request(app)
        .get('/api/optimizations/stats/summary')
        .expect(200);
      
      expect(response.body).toMatchObject({
        success: true,
        data: expect.objectContaining({
          totalOptimizations: expect.any(Number),
          byStatus: expect.any(Object),
          byRiskLevel: expect.any(Object),
          byType: expect.any(Object),
          totalPotentialSavings: expect.any(Number),
          approvedSavings: expect.any(Number),
          executedSavings: expect.any(Number),
          averageConfidenceScore: expect.any(Number)
        }),
        message: expect.stringContaining('Optimization statistics retrieved successfully'),
        timestamp: expect.any(String)
      });
    });

    test('POST /api/optimizations should handle malformed JSON gracefully', async () => {
      const response = await request(app)
        .post('/api/optimizations')
        .send('invalid json')
        .expect(400);
      
      expect(response.body.success).toBe(false);
    });

    test('POST /api/optimizations should handle empty request body', async () => {
      const response = await request(app)
        .post('/api/optimizations')
        .send({})
        .expect(400);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Invalid optimization data'),
        timestamp: expect.any(String)
      });
    });
  });

  describe('Error Handling', () => {
    test('GET /api/nonexistent should return 404', async () => {
      const response = await request(app)
        .get('/api/nonexistent')
        .expect(404);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Endpoint not found'),
        timestamp: expect.any(String)
      });
    });

    test('GET /api/optimizations/:optimizationId should return 404 for non-existent optimization', async () => {
      const response = await request(app)
        .get('/api/optimizations/nonexistent-id')
        .expect(404);
      
      expect(response.body).toMatchObject({
        success: false,
        data: null,
        message: expect.stringContaining('Optimization not found'),
        timestamp: expect.any(String)
      });
    });

    test('POST endpoints should handle Content-Type validation', async () => {
      const response = await request(app)
        .post('/api/resources')
        .set('Content-Type', 'text/plain')
        .send('not json')
        .expect(400);
      
      expect(response.body.success).toBe(false);
    });

    test('API should handle very large request bodies gracefully', async () => {
      const largeData = generateResourceData({
        tags: {}
      });
      
      // Create a large tags object
      for (let i = 0; i < 1000; i++) {
        largeData.tags[`tag${i}`] = `value${i}`.repeat(100);
      }

      const response = await request(app)
        .post('/api/resources')
        .send(largeData);
      
      // Should either succeed or fail gracefully (not crash)
      expect([200, 400, 413]).toContain(response.status);
      expect(response.body).toHaveProperty('success');
    });

    test('API should handle special characters in resource IDs', async () => {
      const resourceData = generateResourceData({
        resourceId: 'i-test@#$%^&*()'
      });

      const response = await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(200);
      
      expect(response.body.data.resourceId).toBe('i-test@#$%^&*()');
    });

    test('API should handle Unicode characters in descriptions', async () => {
      const optimizationData = generateOptimizationData({
        description: 'Optimización de recursos 🚀 节省成本 💰'
      });

      const response = await request(app)
        .post('/api/optimizations')
        .send(optimizationData)
        .expect(200);
      
      expect(response.body.data.description).toBe('Optimización de recursos 🚀 节省成本 💰');
    });

    test('API should handle null and undefined values gracefully', async () => {
      const resourceData = {
        resourceId: 'i-null-test',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: null,
        tags: undefined,
        configuration: null
      };

      const response = await request(app)
        .post('/api/resources')
        .send(resourceData);
      
      // Should either validate and reject, or handle gracefully
      expect([200, 400]).toContain(response.status);
      expect(response.body).toHaveProperty('success');
    });

    test('API should handle concurrent requests correctly', async () => {
      const promises = [];
      
      // Create multiple concurrent requests
      for (let i = 0; i < 10; i++) {
        const resourceData = generateResourceData({
          resourceId: `i-concurrent-${i}`
        });
        
        promises.push(
          request(app)
            .post('/api/resources')
            .send(resourceData)
        );
      }

      const responses = await Promise.all(promises);
      
      // All requests should succeed
      responses.forEach(response => {
        expect(response.status).toBe(200);
        expect(response.body.success).toBe(true);
      });
    });

    test('API should handle malformed query parameters gracefully', async () => {
      const response = await request(app)
        .get('/api/resources?limit=invalid&offset=notanumber')
        .expect(200);
      
      // Should use default values or handle gracefully
      expect(response.body.success).toBe(true);
    });

    test('API should handle extremely large numbers', async () => {
      const resourceData = generateResourceData({
        currentCost: Number.MAX_SAFE_INTEGER
      });

      const response = await request(app)
        .post('/api/resources')
        .send(resourceData);
      
      expect([200, 400]).toContain(response.status);
      expect(response.body).toHaveProperty('success');
    });

    test('API should handle negative numbers appropriately', async () => {
      const resourceData = generateResourceData({
        currentCost: -100
      });

      const response = await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(400);
      
      expect(response.body.success).toBe(false);
      expect(response.body.errors).toEqual(
        expect.arrayContaining([
          expect.stringContaining('currentCost must be a non-negative number')
        ])
      );
    });
  });

  describe('Response Format Validation', () => {
    test('All endpoints should follow {success, data, message, timestamp} format', async () => {
      const endpoints = [
        { method: 'get', path: '/health' },
        { method: 'get', path: '/api/health' },
        { method: 'get', path: '/api/resources' },
        { method: 'get', path: '/api/optimizations' }
      ];

      for (const endpoint of endpoints) {
        const response = await request(app)[endpoint.method](endpoint.path);
        
        expect(response.body).toHaveProperty('success');
        expect(response.body).toHaveProperty('data');
        expect(response.body).toHaveProperty('message');
        expect(response.body).toHaveProperty('timestamp');
        expect(typeof response.body.success).toBe('boolean');
        expect(typeof response.body.message).toBe('string');
        expect(typeof response.body.timestamp).toBe('string');
      }
    });

    test('All timestamps should be valid ISO 8601 format', async () => {
      const response = await request(app)
        .get('/api/resources')
        .expect(200);
      
      const timestamp = response.body.timestamp;
      expect(timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
      expect(new Date(timestamp).toISOString()).toBe(timestamp);
    });

    test('Error responses should include appropriate HTTP status codes', async () => {
      // Test 400 Bad Request
      await request(app)
        .post('/api/resources')
        .send({})
        .expect(400);

      // Test 404 Not Found
      await request(app)
        .get('/api/resources/nonexistent')
        .expect(404);

      // Test 404 for invalid endpoints
      await request(app)
        .get('/api/invalid-endpoint')
        .expect(404);
    });

    test('Success responses should use 200 status code', async () => {
      await request(app)
        .get('/api/resources')
        .expect(200);

      await request(app)
        .get('/api/optimizations')
        .expect(200);

      await request(app)
        .get('/health')
        .expect(200);
    });
  });

  describe('In-Memory Data Storage and Retrieval', () => {
    test('Data should persist across requests within the same test session', async () => {
      const resourceData = generateResourceData({
        resourceId: 'i-persistence-test'
      });

      // Create resource
      await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(200);

      // Verify it exists in subsequent request
      const getResponse = await request(app)
        .get('/api/resources/i-persistence-test')
        .expect(200);
      
      expect(getResponse.body.data.resourceId).toBe('i-persistence-test');
    });

    test('Resource updates should modify existing data in memory', async () => {
      const resourceData = generateResourceData({
        resourceId: 'i-update-memory-test',
        currentCost: 100
      });

      // Create initial resource
      await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(200);

      // Update the resource
      const updatedData = { ...resourceData, currentCost: 200 };
      await request(app)
        .post('/api/resources')
        .send(updatedData)
        .expect(200);

      // Verify the update persisted
      const getResponse = await request(app)
        .get('/api/resources/i-update-memory-test')
        .expect(200);
      
      expect(getResponse.body.data.currentCost).toBe(200);
    });

    test('Resource deletion should remove data from memory', async () => {
      const resourceData = generateResourceData({
        resourceId: 'i-delete-memory-test'
      });

      // Create resource
      await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(200);

      // Verify it exists
      await request(app)
        .get('/api/resources/i-delete-memory-test')
        .expect(200);

      // Delete it
      await request(app)
        .delete('/api/resources/i-delete-memory-test')
        .expect(200);

      // Verify it's gone
      await request(app)
        .get('/api/resources/i-delete-memory-test')
        .expect(404);
    });

    test('Optimization approval should update status in memory', async () => {
      const optimizationData = generateOptimizationData({
        resourceId: 'i-approval-memory-test'
      });

      // Create optimization
      const createResponse = await request(app)
        .post('/api/optimizations')
        .send(optimizationData)
        .expect(200);

      const optimizationId = createResponse.body.data.optimizationId;

      // Verify initial status
      expect(createResponse.body.data.status).toBe('pending');

      // Approve it
      await request(app)
        .post('/api/optimizations/approve')
        .send({
          optimizationIds: [optimizationId],
          approvedBy: 'test@company.com'
        })
        .expect(200);

      // Verify status changed in memory
      const getResponse = await request(app)
        .get(`/api/optimizations/${optimizationId}`)
        .expect(200);
      
      expect(getResponse.body.data.status).toBe('approved');
      expect(getResponse.body.data.approvedBy).toBe('test@company.com');
      expect(getResponse.body.data.approvedAt).toBeTruthy();
    });

    test('Statistics should reflect current in-memory data', async () => {
      // Get initial stats
      const initialStats = await request(app)
        .get('/api/resources/stats/summary')
        .expect(200);

      const initialCount = initialStats.body.data.totalResources;

      // Add a resource
      const resourceData = generateResourceData({
        resourceId: 'i-stats-test',
        currentCost: 150
      });

      await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(200);

      // Get updated stats
      const updatedStats = await request(app)
        .get('/api/resources/stats/summary')
        .expect(200);

      expect(updatedStats.body.data.totalResources).toBe(initialCount + 1);
      expect(updatedStats.body.data.totalCost).toBeGreaterThanOrEqual(150);
    });

    test('Filtering should work correctly with in-memory data', async () => {
      // Create resources with different types and regions
      const ec2Resource = generateResourceData({
        resourceId: 'i-filter-ec2',
        resourceType: 'ec2',
        region: 'us-east-1'
      });

      const rdsResource = generateResourceData({
        resourceId: 'db-filter-rds',
        resourceType: 'rds',
        region: 'us-west-2'
      });

      await request(app).post('/api/resources').send(ec2Resource).expect(200);
      await request(app).post('/api/resources').send(rdsResource).expect(200);

      // Test type filtering
      const ec2Response = await request(app)
        .get('/api/resources?resourceType=ec2')
        .expect(200);
      
      ec2Response.body.data.forEach(resource => {
        expect(resource.resourceType).toBe('ec2');
      });

      // Test region filtering
      const westResponse = await request(app)
        .get('/api/resources?region=us-west-2')
        .expect(200);
      
      westResponse.body.data.forEach(resource => {
        expect(resource.region).toBe('us-west-2');
      });
    });

    test('Pagination should work correctly with in-memory data', async () => {
      // Create multiple resources
      const resources = [];
      for (let i = 0; i < 5; i++) {
        resources.push(generateResourceData({
          resourceId: `i-pagination-${i}`
        }));
      }

      for (const resource of resources) {
        await request(app).post('/api/resources').send(resource).expect(200);
      }

      // Test first page
      const page1Response = await request(app)
        .get('/api/resources?limit=2&offset=0')
        .expect(200);
      
      expect(page1Response.body.data.length).toBeLessThanOrEqual(2);
      expect(page1Response.body.metadata.limit).toBe(2);
      expect(page1Response.body.metadata.offset).toBe(0);

      // Test second page
      const page2Response = await request(app)
        .get('/api/resources?limit=2&offset=2')
        .expect(200);
      
      expect(page2Response.body.metadata.offset).toBe(2);
      
      // Ensure different data on different pages (if enough data exists)
      if (page1Response.body.data.length > 0 && page2Response.body.data.length > 0) {
        const page1Ids = page1Response.body.data.map(r => r.resourceId);
        const page2Ids = page2Response.body.data.map(r => r.resourceId);
        
        // Should not have overlapping IDs
        const intersection = page1Ids.filter(id => page2Ids.includes(id));
        expect(intersection.length).toBe(0);
      }
    });

    test('Complex queries should work with in-memory data', async () => {
      // Create optimization with specific criteria
      const optimizationData = generateOptimizationData({
        resourceId: 'i-complex-query',
        riskLevel: 'HIGH',
        estimatedSavings: 500,
        optimizationType: 'cleanup'
      });

      await request(app)
        .post('/api/optimizations')
        .send(optimizationData)
        .expect(200);

      // Test complex query
      const response = await request(app)
        .get('/api/optimizations?riskLevel=HIGH&minSavings=400&optimizationType=cleanup')
        .expect(200);
      
      response.body.data.forEach(opt => {
        expect(opt.riskLevel).toBe('HIGH');
        expect(opt.estimatedSavings).toBeGreaterThanOrEqual(400);
        expect(opt.optimizationType).toBe('cleanup');
      });
    });
  });
});