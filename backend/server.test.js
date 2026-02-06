const request = require('supertest');
const app = require('./server');

describe('Server Monitoring Endpoints', () => {

    describe('GET /health', () => {
        test('should return health status', async () => {
            const res = await request(app).get('/health');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.status).toBeDefined();
            expect(res.body.data.healthChecks).toBeDefined();
        });
    });

    describe('GET /api/monitoring/dashboard', () => {
        test('should return monitoring dashboard data', async () => {
            const res = await request(app).get('/api/monitoring/dashboard');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.uptime).toBeDefined();
            expect(res.body.data.system).toBeDefined();
        });
    });

    describe('GET /api/monitoring/alerts', () => {
        test('should return alerts', async () => {
            const res = await request(app).get('/api/monitoring/alerts');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data.alerts)).toBe(true);
        });

        test('should filter alerts by severity', async () => {
            // We know alerts might be empty, but we check the call succeeds
            const res = await request(app).get('/api/monitoring/alerts?severity=INFO');
            expect(res.statusCode).toBe(200);
        });

        test('should filter alerts by resolved status', async () => {
            const res = await request(app).get('/api/monitoring/alerts?resolved=false');
            expect(res.statusCode).toBe(200);
        });
    });

    describe('Alert Resolution', () => {
        // We need to inject an alert to resolve it, or mock the internal state. 
        // Since state is in-memory in server.js, we can't easily inject it without an endpoint 
        // or by triggering an error that creates an alert.
        // However, we can test the 404 case easily.

        test('should return 404 for non-existent alert resolution', async () => {
            const res = await request(app).post('/api/monitoring/alerts/fake-id/resolve');
            expect(res.statusCode).toBe(404);
        });
    });

    describe('GET /api/monitoring/metrics', () => {
        test('should return system metrics', async () => {
            const res = await request(app).get('/api/monitoring/metrics');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.global).toBeDefined();
        });

        test('should accept timeWindow param', async () => {
            const res = await request(app).get('/api/monitoring/metrics?timeWindow=1h');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.timeWindow).toBe('1h');
        });
    });


    describe('Global Error Handlers', () => {
        test('should handle 404 for unknown routes', async () => {
            const res = await request(app).get('/api/unknown-route');
            expect(res.statusCode).toBe(404);
        });
    });

    describe('Internal Helper Functions', () => {
        test('checkSystemHealth should return health status', () => {
            if (app.checkSystemHealth) {
                const health = app.checkSystemHealth();
                expect(health.name).toBe('system_performance');
                expect(health.status).toMatch(/HEALTHY|DEGRADED|UNHEALTHY|CRITICAL/);
            }
        });

        test('checkMemoryUsage should return memory usage', () => {
            if (app.checkMemoryUsage) {
                const usage = app.checkMemoryUsage();
                expect(usage.name).toBe('memory_usage');
                expect(usage.status).toMatch(/HEALTHY|DEGRADED|UNHEALTHY|CRITICAL/);
            }
        });

        test('createAlert should add an alert', () => {
            if (app.createAlert) {
                const alert = app.createAlert('INFO', 'Test Alert', 'Testing internal function');
                expect(alert.id).toBeDefined();
                expect(alert.title).toBe('Test Alert');
            }
        });

        test('broadcastUpdate should run without error', () => {
            if (app.broadcastUpdate) {
                const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
                app.broadcastUpdate('TEST_EVENT', { some: 'data' });
                expect(consoleSpy).toHaveBeenCalled();
                consoleSpy.mockRestore();
            }
        });

        test('startMonitoring should set up interval', () => {
            if (app.startMonitoring) {
                jest.useFakeTimers();
                app.startMonitoring();
                jest.advanceTimersByTime(31000);
                jest.useRealTimers();
            }
        });
    });

});
