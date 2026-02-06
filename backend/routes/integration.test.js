const request = require('supertest');
const app = require('../server');

describe('Integration Routes', () => {
    const analysisPayload = {
        summary: 'Test Analysis',
        findings: []
    };

    describe('POST /api/optimization-analysis', () => {
        test('should accept optimization analysis', async () => {
            const res = await request(app)
                .post('/api/optimization-analysis')
                .send(analysisPayload);
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
            expect(res.body.data.summary).toBe('Test Analysis');
        });

        test('should accept optimization analysis via integration route', async () => {
            const res = await request(app)
                .post('/api/integration/optimization-analysis')
                .send(analysisPayload);
            expect(res.statusCode).toBe(200);
        });
    });

    describe('POST /api/anomaly-analysis', () => {
        test('should accept anomaly analysis', async () => {
            const res = await request(app)
                .post('/api/anomaly-analysis')
                .send(analysisPayload);
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
        });

        test('should accept anomaly analysis via integration route', async () => {
            const res = await request(app)
                .post('/api/integration/anomaly-analysis')
                .send(analysisPayload);
            expect(res.statusCode).toBe(200);
        });
    });

    describe('POST /api/budget-analysis', () => {
        test('should accept budget analysis', async () => {
            const res = await request(app)
                .post('/api/budget-analysis')
                .send(analysisPayload);
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
        });

        test('should accept budget analysis via integration route', async () => {
            const res = await request(app)
                .post('/api/integration/budget-analysis')
                .send(analysisPayload);
            expect(res.statusCode).toBe(200);
        });
    });

    describe('POST /api/execution-results', () => {
        test('should accept execution results', async () => {
            const res = await request(app)
                .post('/api/execution-results')
                .send({ executed: true, result: 'success' });
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
        });

        test('should accept execution results via integration route', async () => {
            const res = await request(app)
                .post('/api/integration/execution-results')
                .send({ executed: true, result: 'success' });
            expect(res.statusCode).toBe(200);
        });
    });

    describe('POST /api/reports', () => {
        test('should accept workflow reports', async () => {
            const res = await request(app)
                .post('/api/reports')
                .send({ reportType: 'daily', content: '...' });
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
        });

        test('should accept workflow reports via integration route', async () => {
            const res = await request(app)
                .post('/api/integration/reports')
                .send({ reportType: 'daily', content: '...' });
            expect(res.statusCode).toBe(200);
        });
    });

    describe('GET /api/integration/status', () => {
        test('should return integration status', async () => {
            const res = await request(app).get('/api/integration/status');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.integrationHealth).toBeDefined();
        });
    });

    describe('GET /api/integration/recent', () => {
        test('should return recent activity', async () => {
            const res = await request(app).get('/api/integration/recent');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data.items)).toBe(true);
        });

        test('should filter recent activity by type', async () => {
            const res = await request(app).get('/api/integration/recent?type=report');
            expect(res.statusCode).toBe(200);
            res.body.data.items.forEach(item => {
                expect(item.itemType).toBe('report');
            });
        });
    });

    describe('DELETE /api/integration/cleanup', () => {
        test('should cleanup old data', async () => {
            const res = await request(app).delete('/api/integration/cleanup?olderThanDays=0');
            // Using 0 to try and clear things we just added, though exact timing might vary.
            // The important thing is ensuring the call succeeds.
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
            expect(res.body.data.cleaned).toBeDefined();
        });
    });
});
