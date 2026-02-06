const request = require('supertest');
const app = require('../server');

describe('Dashboard Routes', () => {
    describe('GET /api/dashboard/overview', () => {
        test('should return dashboard overview', async () => {
            const res = await request(app).get('/api/dashboard/overview');
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
            expect(res.body.data.kpis).toBeDefined();
        });
    });

    describe('GET /api/dashboard/time-series', () => {
        test('should return time-series data for default metric', async () => {
            const res = await request(app).get('/api/dashboard/time-series');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data)).toBe(true);
            expect(res.body.metadata.metric).toBe('savings');
        });

        test('should return time-series data for cost metric', async () => {
            const res = await request(app).get('/api/dashboard/time-series?metric=cost');
            expect(res.statusCode).toBe(200);
            expect(res.body.metadata.metric).toBe('cost');
        });
    });

    describe('GET /api/dashboard/filters', () => {
        test('should return available filters', async () => {
            const res = await request(app).get('/api/dashboard/filters');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.services).toBeDefined();
            expect(res.body.data.regions).toBeDefined();
        });
    });

    describe('GET /api/dashboard/aggregated', () => {
        test('should return aggregated data for all widgets', async () => {
            const res = await request(app).get('/api/dashboard/aggregated?widgets=all');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.savings).toBeDefined();
            expect(res.body.data.anomalies).toBeDefined();
        });

        test('should return aggregated data for specific widgets', async () => {
            const res = await request(app).get('/api/dashboard/aggregated?widgets=savings,budgets');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.savings).toBeDefined();
            expect(res.body.data.budgets).toBeDefined();
            expect(res.body.data.anomalies).toBeUndefined();
        });
    });

    describe('POST /api/dashboard/refresh', () => {
        test('should trigger data refresh', async () => {
            const res = await request(app)
                .post('/api/dashboard/refresh')
                .send({ dataType: 'all' });
            expect(res.statusCode).toBe(200);
            expect(res.body.data.status).toBe('in_progress');
        });
    });

    describe('GET /api/dashboard/export', () => {
        test('should export data as JSON', async () => {
            const res = await request(app).get('/api/dashboard/export?format=json&dataType=overview');
            expect(res.statusCode).toBe(200);
            expect(res.headers['content-type']).toContain('application/json');
            expect(res.body.success).toBe(true);
        });

        test('should export data as CSV', async () => {
            const res = await request(app).get('/api/dashboard/export?format=csv&dataType=savings');
            expect(res.statusCode).toBe(200);
            expect(res.headers['content-type']).toContain('text/csv');
            // CSV mock returns a string, so we check text/csv header
            expect(res.text).toBeDefined();
        });
    });
});
