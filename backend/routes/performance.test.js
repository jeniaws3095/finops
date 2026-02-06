/**
 * Performance and Load Testing
 * 
 * Tests API performance under various load conditions and validates
 * response times, memory usage, and concurrent request handling.
 * 
 * Requirements: 9.1
 */

const request = require('supertest');
const app = require('../server');

describe('Performance and Load Tests', () => {
  
  describe('Response Time Tests', () => {
    test('GET /api/resources should respond within acceptable time', async () => {
      const startTime = Date.now();
      
      const response = await request(app)
        .get('/api/resources')
        .expect(200);
      
      const responseTime = Date.now() - startTime;
      
      expect(responseTime).toBeLessThan(1000); // Should respond within 1 second
      expect(response.body.success).toBe(true);
    });

    test('POST /api/resources should respond within acceptable time', async () => {
      const resourceData = {
        resourceId: 'i-performance-test',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 100
      };

      const startTime = Date.now();
      
      const response = await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(200);
      
      const responseTime = Date.now() - startTime;
      
      expect(responseTime).toBeLessThan(1000); // Should respond within 1 second
      expect(response.body.success).toBe(true);
    });

    test('Complex queries should respond within acceptable time', async () => {
      // First create some test data
      const resources = [];
      for (let i = 0; i < 10; i++) {
        resources.push({
          resourceId: `i-perf-${i}`,
          resourceType: i % 2 === 0 ? 'ec2' : 'rds',
          region: i % 3 === 0 ? 'us-east-1' : 'us-west-2',
          currentCost: Math.random() * 1000,
          state: 'running'
        });
      }

      // Create resources
      for (const resource of resources) {
        await request(app).post('/api/resources').send(resource);
      }

      const startTime = Date.now();
      
      const response = await request(app)
        .get('/api/resources?resourceType=ec2&region=us-east-1&state=running&limit=5')
        .expect(200);
      
      const responseTime = Date.now() - startTime;
      
      expect(responseTime).toBeLessThan(500); // Complex queries should be fast
      expect(response.body.success).toBe(true);
    });
  });

  describe('Concurrent Request Handling', () => {
    test('should handle multiple concurrent GET requests', async () => {
      const concurrentRequests = 20;
      const promises = [];

      for (let i = 0; i < concurrentRequests; i++) {
        promises.push(
          request(app)
            .get('/api/resources')
            .expect(200)
        );
      }

      const startTime = Date.now();
      const responses = await Promise.all(promises);
      const totalTime = Date.now() - startTime;

      // All requests should succeed
      responses.forEach(response => {
        expect(response.body.success).toBe(true);
      });

      // Total time should be reasonable (not much slower than sequential)
      expect(totalTime).toBeLessThan(5000);
    });

    test('should handle concurrent POST requests without data corruption', async () => {
      const concurrentRequests = 10;
      const promises = [];

      for (let i = 0; i < concurrentRequests; i++) {
        const resourceData = {
          resourceId: `i-concurrent-${i}`,
          resourceType: 'ec2',
          region: 'us-east-1',
          currentCost: i * 10
        };

        promises.push(
          request(app)
            .post('/api/resources')
            .send(resourceData)
            .expect(200)
        );
      }

      const responses = await Promise.all(promises);

      // All requests should succeed
      responses.forEach((response, index) => {
        expect(response.body.success).toBe(true);
        expect(response.body.data.resourceId).toBe(`i-concurrent-${index}`);
        expect(response.body.data.currentCost).toBe(index * 10);
      });

      // Verify all resources were created
      const getResponse = await request(app)
        .get('/api/resources')
        .expect(200);

      const concurrentResources = getResponse.body.data.filter(r => 
        r.resourceId.startsWith('i-concurrent-')
      );

      expect(concurrentResources.length).toBe(concurrentRequests);
    });

    test('should handle mixed concurrent operations', async () => {
      const promises = [];

      // Mix of GET, POST, and other operations
      for (let i = 0; i < 5; i++) {
        // GET requests
        promises.push(
          request(app).get('/api/resources').expect(200)
        );

        // POST requests
        promises.push(
          request(app)
            .post('/api/resources')
            .send({
              resourceId: `i-mixed-${i}`,
              resourceType: 'ec2',
              region: 'us-east-1',
              currentCost: 100
            })
            .expect(200)
        );

        // Stats requests
        promises.push(
          request(app).get('/api/resources/stats/summary').expect(200)
        );
      }

      const responses = await Promise.all(promises);

      // All requests should succeed
      responses.forEach(response => {
        expect(response.body.success).toBe(true);
      });
    });
  });

  describe('Large Dataset Handling', () => {
    test('should handle large number of resources efficiently', async () => {
      const resourceCount = 100;
      const batchSize = 10;

      // Create resources in batches to avoid overwhelming the system
      for (let batch = 0; batch < resourceCount / batchSize; batch++) {
        const batchPromises = [];
        
        for (let i = 0; i < batchSize; i++) {
          const resourceIndex = batch * batchSize + i;
          const resourceData = {
            resourceId: `i-large-dataset-${resourceIndex}`,
            resourceType: ['ec2', 'rds', 'lambda'][resourceIndex % 3],
            region: ['us-east-1', 'us-west-2', 'eu-west-1'][resourceIndex % 3],
            currentCost: Math.random() * 1000,
            state: 'running',
            tags: {
              Environment: resourceIndex % 2 === 0 ? 'prod' : 'dev',
              Team: `team-${resourceIndex % 5}`
            }
          };

          batchPromises.push(
            request(app)
              .post('/api/resources')
              .send(resourceData)
              .expect(200)
          );
        }

        await Promise.all(batchPromises);
      }

      // Test retrieval performance with large dataset
      const startTime = Date.now();
      
      const response = await request(app)
        .get('/api/resources?limit=50')
        .expect(200);
      
      const responseTime = Date.now() - startTime;

      expect(responseTime).toBeLessThan(2000); // Should handle large datasets efficiently
      expect(response.body.data.length).toBeLessThanOrEqual(50);
      expect(response.body.metadata.total).toBeGreaterThanOrEqual(resourceCount);
    });

    test('should handle pagination efficiently with large datasets', async () => {
      const pageSize = 10;
      const maxPages = 5;

      for (let page = 0; page < maxPages; page++) {
        const startTime = Date.now();
        
        const response = await request(app)
          .get(`/api/resources?limit=${pageSize}&offset=${page * pageSize}`)
          .expect(200);
        
        const responseTime = Date.now() - startTime;

        expect(responseTime).toBeLessThan(1000); // Each page should load quickly
        expect(response.body.data.length).toBeLessThanOrEqual(pageSize);
        expect(response.body.metadata.limit).toBe(pageSize);
        expect(response.body.metadata.offset).toBe(page * pageSize);
      }
    });

    test('should handle complex filtering on large datasets', async () => {
      const startTime = Date.now();
      
      const response = await request(app)
        .get('/api/resources?resourceType=ec2&region=us-east-1&state=running')
        .expect(200);
      
      const responseTime = Date.now() - startTime;

      expect(responseTime).toBeLessThan(1500); // Complex filtering should be reasonably fast
      
      // Verify filtering worked correctly
      response.body.data.forEach(resource => {
        expect(resource.resourceType).toBe('ec2');
        expect(resource.region).toBe('us-east-1');
        expect(resource.state).toBe('running');
      });
    });
  });

  describe('Memory Usage Tests', () => {
    test('should not have significant memory leaks during repeated operations', async () => {
      const initialMemory = process.memoryUsage().heapUsed;
      
      // Perform many operations
      for (let i = 0; i < 50; i++) {
        const resourceData = {
          resourceId: `i-memory-test-${i}`,
          resourceType: 'ec2',
          region: 'us-east-1',
          currentCost: 100
        };

        await request(app)
          .post('/api/resources')
          .send(resourceData)
          .expect(200);

        await request(app)
          .get('/api/resources')
          .expect(200);

        // Occasionally clean up to simulate real usage
        if (i % 10 === 0) {
          await request(app)
            .delete(`/api/resources/i-memory-test-${i}`)
            .expect(200);
        }
      }

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      const finalMemory = process.memoryUsage().heapUsed;
      const memoryIncrease = finalMemory - initialMemory;

      // Memory increase should be reasonable (less than 50MB for this test)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    });
  });

  describe('Error Handling Under Load', () => {
    test('should handle validation errors gracefully under load', async () => {
      const promises = [];

      // Send many invalid requests concurrently
      for (let i = 0; i < 20; i++) {
        promises.push(
          request(app)
            .post('/api/resources')
            .send({}) // Invalid data
            .expect(400)
        );
      }

      const responses = await Promise.all(promises);

      // All should fail gracefully with proper error messages
      responses.forEach(response => {
        expect(response.body.success).toBe(false);
        expect(response.body.errors).toBeDefined();
        expect(Array.isArray(response.body.errors)).toBe(true);
      });
    });

    test('should handle 404 errors gracefully under load', async () => {
      const promises = [];

      // Send many requests for non-existent resources
      for (let i = 0; i < 20; i++) {
        promises.push(
          request(app)
            .get(`/api/resources/nonexistent-${i}`)
            .expect(404)
        );
      }

      const responses = await Promise.all(promises);

      // All should return proper 404 responses
      responses.forEach(response => {
        expect(response.body.success).toBe(false);
        expect(response.body.message).toContain('Resource not found');
      });
    });
  });
});