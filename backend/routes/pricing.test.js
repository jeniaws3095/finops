const request = require('supertest');
const app = require('../server');

describe('Pricing Routes', () => {
    const pricingData = {
        recommendationId: 'rec-1',
        recommendationType: 'reserved_instance',
        serviceType: 'EC2',
        estimatedSavings: 100,
        confidenceScore: 90
    };

    const riData = {
        serviceType: 'EC2',
        instanceType: 't3.large',
        currentOnDemandCost: 100,
        reservedInstanceCost: 60,
        monthlyCost: 5,
        estimatedSavings: 40
    };

    const spotData = {
        serviceType: 'EC2',
        instanceType: 't3.medium',
        currentOnDemandPrice: 0.05,
        currentSpotPrice: 0.02,
        averageSpotPrice: 0.025,
        potentialSavings: 0.03
    };

    const spData = {
        planType: 'compute',
        commitmentAmount: 10,
        hourlyCommitment: 1,
        currentOnDemandCost: 100,
        savingsPlansRate: 0.8,
        estimatedSavings: 20
    };

    describe('GET /api/pricing', () => {
        test('should return pricing recommendations', async () => {
            const res = await request(app).get('/api/pricing');
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
            expect(Array.isArray(res.body.data)).toBe(true);
        });


        test('should filter by minSavings', async () => {
            const res = await request(app).get('/api/pricing?minSavings=10');
            expect(res.statusCode).toBe(200);
        });

        test('should filter by maxSavings', async () => {
            const res = await request(app).get('/api/pricing?maxSavings=1000');
            expect(res.statusCode).toBe(200);
        });

        test('should filter by confidenceLevel', async () => {
            const res = await request(app).get('/api/pricing?confidenceLevel=80');
            expect(res.statusCode).toBe(200);
        });

        test('should filter by recommendationType', async () => {
            const res = await request(app).get('/api/pricing?recommendationType=reserved_instance');
            expect(res.statusCode).toBe(200);
        });

        test('should return pricing summary', async () => {
            const res = await request(app).get('/api/pricing?format=summary');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.totalRecommendations).toBeDefined();
        });

        test('should return pricing charts', async () => {
            const res = await request(app).get('/api/pricing?format=chart');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.riskSavingsScatter).toBeDefined();
        });
    });

    describe('POST /api/pricing', () => {
        test('should create pricing recommendation', async () => {
            const res = await request(app)
                .post('/api/pricing')
                .send(pricingData);
            expect(res.statusCode).toBe(200);
            expect(res.body.data.recommendationId).toBe(pricingData.recommendationId);
        });

        test('should fail validation', async () => {
            const res = await request(app)
                .post('/api/pricing')
                .send({ recommendationId: 'incomplete' });
            expect(res.statusCode).toBe(400);
        });
    });

    describe('POST /api/pricing/reserved-instances', () => {
        test('should create RI recommendation', async () => {
            const res = await request(app)
                .post('/api/pricing/reserved-instances')
                .send(riData);
            expect(res.statusCode).toBe(201);
            expect(res.body.success).toBe(true);
        });
    });

    describe('GET /api/pricing/reserved-instances', () => {
        test('should get RI recommendations', async () => {
            const res = await request(app).get('/api/pricing/reserved-instances');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data)).toBe(true);
        });
    });

    describe('POST /api/pricing/spot-instances', () => {
        test('should create spot opportunity', async () => {
            const res = await request(app)
                .post('/api/pricing/spot-instances')
                .send(spotData);
            expect(res.statusCode).toBe(201);
            expect(res.body.success).toBe(true);
        });
    });


    describe('GET /api/pricing/spot-instances', () => {
        test('should get spot opportunities', async () => {
            const res = await request(app).get('/api/pricing/spot-instances');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data)).toBe(true);
        });

        test('should filter by service', async () => {
            const res = await request(app).get('/api/pricing/spot-instances?service=EC2');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(item => expect(item.serviceType).toBe('EC2'));
        });

        test('should filter by region', async () => {
            const res = await request(app).get('/api/pricing/spot-instances?region=us-east-1');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(item => expect(item.region).toBe('us-east-1'));
        });
    });

    describe('POST /api/pricing/savings-plans', () => {
        test('should create savings plan recommendation', async () => {
            const res = await request(app)
                .post('/api/pricing/savings-plans')
                .send(spData);
            expect(res.statusCode).toBe(201);
            expect(res.body.success).toBe(true);
        });
    });



    describe('GET /api/pricing/savings-plans', () => {
        test('should get savings plans', async () => {
            const res = await request(app).get('/api/pricing/savings-plans');
            expect(res.statusCode).toBe(200);
            expect(Array.isArray(res.body.data)).toBe(true);
        });

        test('should filter by planType', async () => {
            const res = await request(app).get('/api/pricing/savings-plans?planType=compute');
            expect(res.statusCode).toBe(200);
            res.body.data.forEach(item => expect(item.planType).toBe('compute'));
        });

        test('should filter by paymentOption', async () => {
            const res = await request(app).get('/api/pricing/savings-plans?paymentOption=partial_upfront');
            expect(res.statusCode).toBe(200);
        });

        test('should filter by term', async () => {
            const res = await request(app).get('/api/pricing/savings-plans?term=1year');
            expect(res.statusCode).toBe(200);
        });
    });

    describe('GET /api/pricing/chart-data', () => {
        test('should get chart data', async () => {
            const res = await request(app).get('/api/pricing/chart-data');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.riskSavingsScatter).toBeDefined();
        });
    });

    describe('GET /api/pricing/summary', () => {
        test('should get summary', async () => {
            const res = await request(app).get('/api/pricing/summary');
            expect(res.statusCode).toBe(200);
            expect(res.body.data.totalRecommendations).toBeDefined();
        });
    });
});
