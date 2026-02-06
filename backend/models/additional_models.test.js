const { CostAnomaly, BudgetForecast } = require('./index');

describe('Additional Model Tests', () => {

    describe('CostAnomaly Methods', () => {
        let anomaly;

        beforeEach(() => {
            anomaly = new CostAnomaly({
                serviceType: 'ec2',
                anomalyType: 'spike',
                baselineCost: 100,
                actualCost: 150
            });
        });

        test('should resolve anomaly correctly', () => {
            const success = anomaly.resolve('tester', 'Fixed it');
            expect(success).toBe(true);
            expect(anomaly.resolved).toBe(true);
            expect(anomaly.resolvedBy).toBe('tester');
            expect(anomaly.resolutionNotes).toBe('Fixed it');

            // identifying line 117 check
            const success2 = anomaly.resolve('tester2');
            expect(success2).toBe(false);
        });

        test('should mark alert sent', () => {
            const success = anomaly.markAlertSent(['slack']);
            expect(success).toBe(true);
            expect(anomaly.alertSent).toBe(true);
            expect(anomaly.notificationChannels).toContain('slack');

            const success2 = anomaly.markAlertSent(['email']);
            expect(success2).toBe(false);
        });

        test('should add contributing factor', () => {
            anomaly.addContributingFactor({ reason: 'config change' });
            expect(anomaly.contributingFactors.length).toBe(1);
            expect(anomaly.contributingFactors[0].reason).toBe('config change');
        });

        test('should add affected resource', () => {
            anomaly.addAffectedResource({ resourceId: 'i-123' });
            expect(anomaly.affectedResources.length).toBe(1);
            expect(anomaly.affectedResources[0].resourceId).toBe('i-123');
        });

        test('should calculate deviation amount', () => {
            expect(anomaly.calculateDeviationAmount()).toBe(50);
        });
    });

    describe('BudgetForecast Methods', () => {
        let forecast;

        beforeEach(() => {
            forecast = new BudgetForecast({
                budgetCategory: 'team',
                budgetName: 'Test Budget',
                budgetLimit: 1000,
                currentSpend: 500,
                forecastedSpend: 800,
                alertThresholds: {
                    warning: 80,
                    critical: 95,
                    forecast_overrun: 100
                }
            });
        });

        test('should calculate variance (favorable)', () => {
            const variance = forecast.calculateVariance();
            expect(variance.type).toBe('favorable'); // 500 < 1000
            expect(variance.amount).toBe(500);
        });

        test('should calculate variance (unfavorable)', () => {
            forecast.currentSpend = 1200;
            const variance = forecast.calculateVariance();
            expect(variance.type).toBe('unfavorable');
            expect(variance.amount).toBe(200);
        });

        test('should assess budget risk - MEDIUM', () => {
            // > 80% (800) but < 95% (950)
            forecast.currentSpend = 850;
            const risk = forecast.assessBudgetRisk();
            expect(risk.riskLevel).toBe('MEDIUM');
            expect(risk.message).toContain('approaching warning threshold');
        });

        test('should assess budget risk - HIGH', () => {
            // > 95% (950)
            forecast.currentSpend = 960;
            const risk = forecast.assessBudgetRisk();
            expect(risk.riskLevel).toBe('HIGH');
        });

        test('should assess budget risk - CRITICAL', () => {
            // forecasted > 100% (1000)
            forecast.forecastedSpend = 1100;
            const risk = forecast.assessBudgetRisk();
            expect(risk.riskLevel).toBe('CRITICAL');
        });

        test('should add assumption', () => {
            forecast.addAssumption({ text: 'Prices stable' });
            expect(forecast.assumptions.length).toBe(1);
        });

        test('should add risk factor', () => {
            forecast.addRiskFactor({ text: 'Volatile market' });
            expect(forecast.riskFactors.length).toBe(1);
        });

        test('should update forecast', () => {
            forecast.updateForecast({ currentSpend: 600 });
            expect(forecast.currentSpend).toBe(600);
            expect(forecast.remainingBudget).toBe(400);
        });

        test('should create from JSON', () => {
            const json = forecast.toJSON();
            const newForecast = BudgetForecast.fromJSON(json);
            expect(newForecast.budgetName).toBe(forecast.budgetName);
        });
    });

});
