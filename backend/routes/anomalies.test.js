const request = require('supertest');
const app = require('../server');

describe('Anomaly Routes', () => {
    // Test Data
    const anomalyData = {
        anomalyId: 'test-anomaly-1',
        anomalyType: 'cost_spike',
        severity: 'HIGH',
        actualCost: 150.00,
        expectedCost: 100.00,
        region: 'us-east-1',
        serviceType: 'EC2',
        detectedAt: new Date().toISOString()
    };

    const alertData = {
        alertId: 'test-alert-1',
        severity: 'HIGH',
        title: 'High Cost Alert',
        timestamp: new Date().toISOString()
    };

    describe('GET /api/anomalies', () => {
        test('should return empty list initially', async () => {
            const res = await request(app).get('/api/anomalies');
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
            expect(Array.isArray(res.body.data.anomalies)).toBe(true);
        });
    });

    describe('POST /api/anomalies', () => {
        test('should create a new anomaly', async () => {
            const res = await request(app)
                .post('/api/anomalies')
                .send(anomalyData);

            expect(res.statusCode).toBe(201);
            expect(res.body.success).toBe(true);
            expect(res.body.data.anomalyId).toBe(anomalyData.anomalyId);
        });

        test('should fail validation when required fields are missing', async () => {
            const res = await request(app)
                .post('/api/anomalies')
                .send({ anomalyId: 'incomplete' });

            expect(res.statusCode).toBe(400);
            expect(res.body.success).toBe(false);
        });

        test('should prevent duplicate anomalies', async () => {
            // First creation
            await request(app).post('/api/anomalies').send({ ...anomalyData, anomalyId: 'dup-test' });
            // Duplicate creation
            const res = await request(app)
                .post('/api/anomalies')
                .send({ ...anomalyData, anomalyId: 'dup-test' });

            expect(res.statusCode).toBe(409);
        });
    });

    describe('GET /api/anomalies/:anomalyId', () => {
        test('should retrieve an existing anomaly', async () => {
            const res = await request(app).get(`/api/anomalies/${anomalyData.anomalyId}`);
            expect(res.statusCode).toBe(200);
            expect(res.body.data.anomalyId).toBe(anomalyData.anomalyId);
        });

        test('should return 404 for non-existent anomaly', async () => {
            const res = await request(app).get('/api/anomalies/non-existent');
            expect(res.statusCode).toBe(404);
        });
    });

    describe('PUT /api/anomalies/:anomalyId/resolve', () => {
        test('should resolve an anomaly', async () => {
            const res = await request(app)
                .put(`/api/anomalies/${anomalyData.anomalyId}/resolve`)
                .send({ resolvedBy: 'tester', resolutionNotes: 'Fixed' });

            expect(res.statusCode).toBe(200);
            expect(res.body.data.resolved).toBe(true);
            expect(res.body.data.resolvedBy).toBe('tester');
        });

        test('should fail to resolve non-existent anomaly', async () => {
            const res = await request(app)
                .put('/api/anomalies/non-existent/resolve')
                .send({ resolvedBy: 'tester' });

            expect(res.statusCode).toBe(404);
        });
    });

    describe('GET /api/anomalies (filters)', () => {
        test('should filter by severity', async () => {
            const res = await request(app).get('/api/anomalies?severity=HIGH');
            expect(res.statusCode).toBe(200);
            res.body.data.anomalies.forEach(a => {
                expect(a.severity).toBe('HIGH');
            });
        });


        test('should filter by region', async () => {
            const res = await request(app).get('/api/anomalies?region=us-east-1');
            expect(res.statusCode).toBe(200);
            res.body.data.anomalies.forEach(a => {
                expect(a.region).toBe('us-east-1');
            });
        });

        test('should filter by resolved status', async () => {
            const res = await request(app).get('/api/anomalies?resolved=true');
            expect(res.statusCode).toBe(200);
            // Assuming we resolved one in previous test
            res.body.data.anomalies.forEach(a => expect(a.resolved).toBe(true));
        });

        test('should filter by boolean resolved param', async () => {
            const res = await request(app).get('/api/anomalies?resolved=false');
            expect(res.statusCode).toBe(200);
        });

        test('should filter by date range', async () => {
            const startDate = new Date(Date.now() - 86400000).toISOString();
            const res = await request(app).get(`/api/anomalies?startDate=${startDate}`);
            expect(res.statusCode).toBe(200);
        });
    });

    describe('POST /api/anomalies/batch', () => {
        test('should create multiple anomalies', async () => {
            const batchData = {
                anomalies: [
                    { ...anomalyData, anomalyId: 'batch-1' },
                    { ...anomalyData, anomalyId: 'batch-2' }
                ]
            };

            const res = await request(app)
                .post('/api/anomalies/batch')
                .send(batchData);

            expect(res.statusCode).toBe(201);
            expect(res.body.data.successCount).toBe(2);
        });

        test('should handle validation errors in batch', async () => {
            const batchData = {
                anomalies: [
                    { ...anomalyData, anomalyId: 'batch-valid' },
                    { anomalyId: 'batch-invalid' } // Missing required fields
                ]
            };

            const res = await request(app)
                .post('/api/anomalies/batch')
                .send(batchData);

            expect(res.statusCode).toBe(201);
            expect(res.body.data.successCount).toBe(1);
            expect(res.body.data.errorCount).toBe(1);
        });

        test('should fail with 400 for invalid input format', async () => {
            const res = await request(app)
                .post('/api/anomalies/batch')
                .send({ anomalies: 'not-an-array' });
            expect(res.statusCode).toBe(400);
        });
    });

    describe('POST /api/anomalies/alerts', () => {
        test('should create a new alert', async () => {
            const res = await request(app)
                .post('/api/anomalies/alerts')
                .send(alertData);
            expect(res.statusCode).toBe(201);
            expect(res.body.data.alertId).toBe(alertData.alertId);
        });
    });

    describe('GET /api/anomalies/alerts', () => {
        test('should retrieve alerts', async () => {
            const res = await request(app).get('/api/anomalies/alerts');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data.alerts)).toBe(true);
        });

        test('should filter alerts by severity', async () => {
            const res = await request(app).get('/api/anomalies/alerts?severity=HIGH');
            expect(res.statusCode).toBe(200);
            res.body.data.alerts.forEach(a => expect(a.severity).toBe('HIGH'));
        });
    });

    describe('PUT /api/anomalies/alerts/:alertId/acknowledge', () => {
        test('should acknowledge an alert', async () => {
            const res = await request(app)
                .put(`/api/anomalies/alerts/${alertData.alertId}/acknowledge`)
                .send({ acknowledgedBy: 'tester' });

            expect(res.statusCode).toBe(200);
            expect(res.body.data.acknowledged).toBe(true);
        });

        test('should fail for non-existent alert', async () => {
            const res = await request(app)
                .put('/api/anomalies/alerts/non-existent/acknowledge')
                .send({ acknowledgedBy: 'tester' });

            expect(res.statusCode).toBe(404);
        });
    });

    describe('GET /api/anomalies/stats/summary', () => {
        test('should return stats summary', async () => {
            const res = await request(app).get('/api/anomalies/stats/summary');
            expect(res.statusCode).toBe(200);
            expect(res.body.data).toHaveProperty('totalAnomalies');
            expect(res.body.data).toHaveProperty('severityDistribution');
        });
    });

});
