const request = require('supertest');
const app = require('../server');

describe('Resource Routes', () => {
    const resourceData = {
        resourceId: 'i-test-123',
        resourceType: 'ec2',
        region: 'us-east-1',
        currentCost: 100.00,
        state: 'running',
        utilizationMetrics: { averageUtilization: 50 },
        timestamp: new Date().toISOString()
    };

    const resourceData2 = {
        resourceId: 'i-test-456',
        resourceType: 'rds',
        region: 'us-west-2',
        currentCost: 200.00,
        state: 'stopped',
        utilizationMetrics: { averageUtilization: 10 },
        timestamp: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(), // 60 days old
        serviceType: 'RDS'
    };

    beforeAll(async () => {
        // Seed some data
        await request(app).post('/api/resources').send(resourceData);
        await request(app).post('/api/resources').send(resourceData2);
    });

    describe('GET /api/resources', () => {
        test('should return all resources', async () => {
            const res = await request(app).get('/api/resources?timeRange=all');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data)).toBe(true);
            expect(res.body.data.length).toBeGreaterThanOrEqual(2);
        });

        test('should filter by resourceType', async () => {
            const res = await request(app).get('/api/resources?resourceType=ec2&timeRange=all');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(r => expect(r.resourceType).toBe('ec2'));
        });

        test('should filter by region', async () => {
            const res = await request(app).get('/api/resources?region=us-west-2&timeRange=all');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(r => expect(r.region).toBe('us-west-2'));
        });

        test('should filter by state', async () => {
            const res = await request(app).get('/api/resources?state=stopped&timeRange=all');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(r => expect(r.state).toBe('stopped'));
        });

        test('should filter by costThreshold', async () => {
            const res = await request(app).get('/api/resources?costThreshold=150&timeRange=all');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(r => expect(r.currentCost).toBeGreaterThanOrEqual(150));
        });

        test('should filter by utilizationThreshold', async () => {
            const res = await request(app).get('/api/resources?utilizationThreshold=20&timeRange=all');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(r => expect(r.utilizationMetrics.averageUtilization).toBeLessThanOrEqual(20));
        });

        test('should filter by timeRange', async () => {
            const res = await request(app).get('/api/resources?timeRange=7d');
            expect(res.statusCode).toBe(200);
            // Expect only recent resource
            // Note: depending on when resourceData timestamp is, but we set it to Now in data definition
            // resourceData2 is 60 days old, should be excluded
            const ids = res.body.data.map(r => r.resourceId);
            expect(ids).toContain(resourceData.resourceId);
            expect(ids).not.toContain(resourceData2.resourceId);
        });

        test('should sort resources', async () => {
            const res = await request(app).get('/api/resources?sortBy=currentCost&sortOrder=desc&timeRange=all');
            expect(res.statusCode).toBe(200);
            const costs = res.body.data.map(r => r.currentCost);
            expect(costs[0]).toBeGreaterThanOrEqual(costs[1]);
        });

        test('should return chart format', async () => {
            const res = await request(app).get('/api/resources?format=chart&timeRange=all');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.serviceDistribution).toBeDefined();
            expect(res.body.data.costUtilizationScatter).toBeDefined();
        });

        test('should return summary format', async () => {
            const res = await request(app).get('/api/resources?format=summary&timeRange=all');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.totalResources).toBeDefined();
            expect(res.body.data.averageCost).toBeDefined();
        });
    });

    describe('GET /api/resources/:resourceId', () => {
        test('should get specific resource', async () => {
            const res = await request(app).get(`/api/resources/${resourceData.resourceId}`);
            expect(res.statusCode).toBe(200);
            expect(res.body.data.resourceId).toBe(resourceData.resourceId);
        });

        test('should filter by region if provided', async () => {
            const res = await request(app).get(`/api/resources/${resourceData.resourceId}?region=${resourceData.region}`);
            expect(res.statusCode).toBe(200);
        });

        test('should not found if region mismatched', async () => {
            const res = await request(app).get(`/api/resources/${resourceData.resourceId}?region=wrong-region`);
            expect(res.statusCode).toBe(404);
        });
    });

    describe('DELETE /api/resources/:resourceId', () => {
        test('should delete resource', async () => {
            const res = await request(app).delete(`/api/resources/${resourceData2.resourceId}`);
            expect(res.statusCode).toBe(200);
        });

        test('should not found if already deleted', async () => {
            const res = await request(app).delete(`/api/resources/${resourceData2.resourceId}`);
            expect(res.statusCode).toBe(404);
        });
    });

    describe('GET /api/resources/stats/summary', () => {
        test('should return stats', async () => {
            const res = await request(app).get('/api/resources/stats/summary');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.totalResources).toBeDefined();
        });
    });
});
