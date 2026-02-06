const request = require('supertest');
const app = require('../server');

describe('Budget Routes', () => {
    const budgetData = {
        budgetId: 'budget-test-1',
        budgetType: 'cost_center',
        budgetAmount: 12000,
        periodMonths: 12,
        currency: 'USD'
    };

    const forecastData = {
        forecastedAmount: 12500,
        confidenceStr: 'HIGH',
        predictedBy: 'AI'
    };

    const alertData = {
        type: 'THRESHOLD_EXCEEDED',
        message: 'Budget exceeded 80%',
        severity: 'WARNING'
    };

    const approvalData = {
        approverId: 'manager-1',
        requestType: 'budget_increase',
        requestedAmount: 5000
    };


    describe('GET /api/budgets', () => {
        test('should return empty budgets initially', async () => {
            const res = await request(app).get('/api/budgets');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data.budgets)).toBe(true);
        });

        test('should filter by budgetType', async () => {
            const res = await request(app).get('/api/budgets?budgetType=cost_center');
            expect(res.statusCode).toBe(200);
        });

        test('should filter by status', async () => {
            const res = await request(app).get('/api/budgets?status=healthy');
            expect(res.statusCode).toBe(200);
        });

        test('should filter by parentBudgetId', async () => {
            const res = await request(app).get('/api/budgets?parentBudgetId=some-id');
            expect(res.statusCode).toBe(200);
        });
    });

    describe('POST /api/budgets', () => {
        test('should create a new budget', async () => {
            const res = await request(app)
                .post('/api/budgets')
                .send(budgetData);
            expect(res.statusCode).toBe(201);
            expect(res.body.data.budgetId).toBe(budgetData.budgetId);
            expect(res.body.data.monthlyAmount).toBe(1000); // 12000 / 12
        });

        test('should fail with missing required fields', async () => {
            const res = await request(app)
                .post('/api/budgets')
                .send({ budgetId: 'incomplete' });
            expect(res.statusCode).toBe(400);
        });

        test('should prevent duplicate budgets', async () => {
            const res = await request(app)
                .post('/api/budgets')
                .send(budgetData);
            expect(res.statusCode).toBe(409);
        });
    });

    describe('GET /api/budgets/:budgetId', () => {
        test('should retrieve a specific budget', async () => {
            const res = await request(app).get(`/api/budgets/${budgetData.budgetId}`);
            expect(res.statusCode).toBe(200);
            expect(res.body.data.budgetId).toBe(budgetData.budgetId);
        });

        test('should return 404 for non-existent budget', async () => {
            const res = await request(app).get('/api/budgets/non-existent');
            expect(res.statusCode).toBe(404);
        });
    });

    describe('PUT /api/budgets/:budgetId', () => {
        test('should update a budget', async () => {
            const res = await request(app)
                .put(`/api/budgets/${budgetData.budgetId}`)
                .send({ budgetAmount: 15000 });
            expect(res.statusCode).toBe(200);
            expect(res.body.data.budgetAmount).toBe(15000);
        });

        test('should fail update for non-existent budget', async () => {
            const res = await request(app)
                .put('/api/budgets/non-existent')
                .send({ budgetAmount: 15000 });
            expect(res.statusCode).toBe(404);
        });
    });

    describe('POST /api/budgets/:budgetId/forecasts', () => {
        test('should add a forecast to a budget', async () => {
            const res = await request(app)
                .post(`/api/budgets/${budgetData.budgetId}/forecasts`)
                .send(forecastData);
            expect(res.statusCode).toBe(201);
            expect(res.body.data.budgetId).toBe(budgetData.budgetId);
        });

        test('should fail adding forecast to non-existent budget', async () => {
            const res = await request(app)
                .post('/api/budgets/non-existent/forecasts')
                .send(forecastData);
            expect(res.statusCode).toBe(404);
        });
    });

    describe('GET /api/budgets/:budgetId/forecasts', () => {
        test('should retrieve forecasts for a budget', async () => {
            const res = await request(app).get(`/api/budgets/${budgetData.budgetId}/forecasts`);
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data.forecasts)).toBe(true);
            expect(res.body.data.forecasts.length).toBeGreaterThan(0);
        });
    });

    describe('POST /api/budgets/:budgetId/alerts', () => {
        test('should create an alert for a budget', async () => {
            const res = await request(app)
                .post(`/api/budgets/${budgetData.budgetId}/alerts`)
                .send(alertData);
            expect(res.statusCode).toBe(201);
            expect(res.body.data.budgetId).toBe(budgetData.budgetId);
        });
    });

    describe('GET /api/budgets/:budgetId/alerts', () => {
        let alertId;

        test('should retrieve alerts for a budget', async () => {
            const res = await request(app).get(`/api/budgets/${budgetData.budgetId}/alerts`);
            expect(res.statusCode).toBe(200);
            expect(res.body.data.alerts.length).toBeGreaterThan(0);
            alertId = res.body.data.alerts[0].alertId;
        });

        test('should acknowledge a budget alert', async () => {
            // Need to get the alertId from previous test or create a new one, 
            // but creating a new one in this test flow is safer/easier
            const createRes = await request(app)
                .post(`/api/budgets/${budgetData.budgetId}/alerts`)
                .send(alertData);
            const newAlertId = createRes.body.data.alertId;

            const res = await request(app)
                .put(`/api/budgets/${budgetData.budgetId}/alerts/${newAlertId}/acknowledge`)
                .send({ acknowledgedBy: 'tester' });
            expect(res.statusCode).toBe(200);
            expect(res.body.data.acknowledged).toBe(true);
        });

        test('should fail to acknowledge alert for wrong budget or non-existent', async () => {
            const res = await request(app)
                .put(`/api/budgets/${budgetData.budgetId}/alerts/non-existent-alert/acknowledge`)
                .send({ acknowledgedBy: 'tester' });
            expect(res.statusCode).toBe(404);
        });
    });

    describe('POST /api/budgets/:budgetId/approvals', () => {
        test('should create approval workflow', async () => {
            const res = await request(app)
                .post(`/api/budgets/${budgetData.budgetId}/approvals`)
                .send(approvalData);
            expect(res.statusCode).toBe(201);
            expect(res.body.data.status).toBe('pending');
        });

        test('should fail creating approval for non-existent budget', async () => {
            const res = await request(app)
                .post('/api/budgets/non-existent/approvals')
                .send(approvalData);
            expect(res.statusCode).toBe(404);
        });
    });

    describe('GET /api/budgets/:budgetId/approvals', () => {
        let workflowId;
        test('should retrieve approvals for budget', async () => {
            const res = await request(app).get(`/api/budgets/${budgetData.budgetId}/approvals`);
            expect(res.statusCode).toBe(200);
            expect(res.body.data.approvals.length).toBeGreaterThan(0);
            workflowId = res.body.data.approvals[0].workflowId;
        });

        test('should update approval workflow', async () => {
            // ensure workflowId is available
            const createRes = await request(app)
                .post(`/api/budgets/${budgetData.budgetId}/approvals`)
                .send(approvalData);
            const newWorkflowId = createRes.body.data.workflowId;

            const res = await request(app)
                .put(`/api/budgets/${budgetData.budgetId}/approvals/${newWorkflowId}`)
                .send({ status: 'approved' });

            expect(res.statusCode).toBe(200);
            expect(res.body.data.status).toBe('approved');
        });

        test('should fail updating non-existent workflow', async () => {
            const res = await request(app)
                .put(`/api/budgets/${budgetData.budgetId}/approvals/non-existent`)
                .send({ status: 'approved' });
            expect(res.statusCode).toBe(404);
        });
    });

    describe('GET /api/budgets/stats/summary', () => {
        test('should return budget stats', async () => {
            const res = await request(app).get('/api/budgets/stats/summary');
            expect(res.statusCode).toBe(200);
            expect(res.body.data).toHaveProperty('totalBudgets');
        });
    });
});
