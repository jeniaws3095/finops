const request = require('supertest');
const app = require('../server');

describe('Savings Routes', () => {
    const savingsData = {
        optimizationId: 'opt-1',
        savingsAmount: 50.00,
        serviceType: 'EC2',
        achievedAt: new Date().toISOString()
    };

    const targetData = {
        targetAmount: 1000,
        name: 'Q1 Savings',
        startDate: new Date().toISOString()
    };

    describe('GET /api/savings', () => {
        test('should return savings records', async () => {
            const res = await request(app).get('/api/savings');
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
            expect(Array.isArray(res.body.data)).toBe(true);
        });

        test('should filter by service', async () => {
            const res = await request(app).get('/api/savings?service=EC2');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(item => expect(item.serviceType).toBe('EC2'));
        });

        test('should filter by region', async () => {
            const res = await request(app).get('/api/savings?region=us-east-1');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(item => expect(item.region).toBe('us-east-1'));
        });


        test('should filter by timeRange', async () => {
            const res = await request(app).get('/api/savings?timeRange=7d');
            expect(res.statusCode).toBe(200);
        });

        test('should filter by timeRange 90d', async () => {
            const res = await request(app).get('/api/savings?timeRange=90d');
            expect(res.statusCode).toBe(200);
        });

        test('should filter by timeRange 1y', async () => {
            const res = await request(app).get('/api/savings?timeRange=1y');
            expect(res.statusCode).toBe(200);
        });

        test('should return savings chart data', async () => {
            const res = await request(app).get('/api/savings?format=chart');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.timeSeries).toBeDefined();
        });

        test('should return savings summary data', async () => {
            const res = await request(app).get('/api/savings?format=summary');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.totalSavings).toBeDefined();
        });
    });

    describe('POST /api/savings', () => {
        test('should create savings record', async () => {
            const res = await request(app)
                .post('/api/savings')
                .send(savingsData);
            expect(res.statusCode).toBe(200);
            expect(res.body.data.optimizationId).toBe(savingsData.optimizationId);
        });

        test('should fail validation', async () => {
            const res = await request(app)
                .post('/api/savings')
                .send({ optimizationId: 'incomplete' });
            expect(res.statusCode).toBe(400);
        });
    });


    describe('GET /api/savings/chart-data', () => {
        test('should return chart data', async () => {
            const res = await request(app).get('/api/savings/chart-data');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.timeSeries).toBeDefined();
        });

        test('should handle group by hour', async () => {
            const res = await request(app).get('/api/savings/chart-data?groupBy=hour&timeRange=7d');
            expect(res.statusCode).toBe(200);
        });

        test('should handle group by week', async () => {
            const res = await request(app).get('/api/savings/chart-data?groupBy=week');
            expect(res.statusCode).toBe(200);
        });

        test('should handle group by month', async () => {
            const res = await request(app).get('/api/savings/chart-data?groupBy=month');
            expect(res.statusCode).toBe(200);
        });
    });

    describe('GET /api/savings/summary', () => {
        test('should return summary', async () => {
            const res = await request(app).get('/api/savings/summary');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.totalSavings).toBeDefined();
        });
    });

    describe('POST /api/savings/targets', () => {
        test('should create savings target', async () => {
            const res = await request(app)
                .post('/api/savings/targets')
                .send(targetData);
            expect(res.statusCode).toBe(201);
            expect(res.body.data.targetAmount).toBe(1000);
        });
    });

    describe('GET /api/savings/targets', () => {
        test('should retrieve savings targets', async () => {
            const res = await request(app).get('/api/savings/targets');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data)).toBe(true);
        });
    });
});
