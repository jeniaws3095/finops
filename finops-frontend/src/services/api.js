const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';
const REQUEST_TIMEOUT = 30000; // 30 seconds

class APIService {
  constructor(baseURL = API_BASE_URL, timeout = REQUEST_TIMEOUT) {
    this.baseURL = baseURL;
    this.timeout = timeout;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    console.log(`📡 API Request: ${url}`);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = {
          status: response.status,
          message: `HTTP ${response.status}: ${response.statusText}`,
          code: `HTTP_${response.status}`,
        };

        try {
          const errorData = await response.json();
          error.message = errorData.message || error.message;
          error.code = errorData.code || error.code;
          error.details = errorData.details;
        } catch {
          // Use default error if response is not JSON
        }

        console.error(`❌ API Error: ${url}`, error);
        throw error;
      }

      const data = await response.json();
      console.log(`✅ API Response: ${url}`, data);
      return data;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          const timeoutError = {
            status: 0,
            message: 'Request timeout',
            code: 'TIMEOUT',
          };
          console.error(`❌ API Timeout: ${url}`);
          throw timeoutError;
        }

        if (error instanceof TypeError) {
          const networkError = {
            status: 0,
            message: 'Network error: Unable to connect to the server',
            code: 'NETWORK_ERROR',
          };
          console.error(`❌ Network Error: ${url}`, error);
          throw networkError;
        }
      }

      if (error instanceof Object && 'status' in error) {
        throw error;
      }

      const unknownError = {
        status: 0,
        message: error instanceof Error ? error.message : 'Unknown error',
        code: 'UNKNOWN_ERROR',
      };
      console.error(`❌ Unknown Error: ${url}`, unknownError);
      throw unknownError;
    }
  }

  async getDashboardData() {
    // Get current costing data
    const costingData = await this.request('/costing/current');
    const serviceData = await this.request('/costing/by-service');
    const regionData = await this.request('/costing/by-region');

    // Calculate cost trend (current vs previous month)
    const currentCost = costingData.total_monthly_cost || 0;
    const previousCost = currentCost * 0.95; // Mock previous month (95% of current)
    const costTrend = previousCost > 0 ? ((currentCost - previousCost) / previousCost) * 100 : 0;

    // Transform the data to match dashboard format
    return {
      currentMonthlyCost: currentCost,
      previousMonthlyCost: previousCost,
      annualProjection: costingData.total_annual_cost || 0,
      costTrend: parseFloat(costTrend.toFixed(2)),
      serviceBreakdown: Object.entries(serviceData.services || {}).map(([service, cost]) => ({
        service: service.toUpperCase().replace(/_/g, ' '),
        cost: cost,
        percentage: serviceData.service_percentages[service] || 0,
      })),
      regionalDistribution: Object.entries(regionData.data || {}).map(([region, data]) => ({
        region: region,
        cost: data.total || 0,
        percentage: ((data.total / currentCost) * 100) || 0,
      })),
      costHistory: [], // Mock cost history
      lastUpdated: new Date().toISOString(),
    };
  }

  async getSavingsData() {
    return this.request('/savings');
  }

  async getResourcesData() {
    return this.request('/instances');
  }

  async getOptimizationsData() {
    // Mock optimization data - can be extended with real backend endpoint
    return {
      optimizations: [
        {
          id: '1',
          title: 'Right-size EC2 instances',
          description: 'Downsize underutilized instances',
          impact: 'high',
          estimatedSavings: 1500,
        },
        {
          id: '2',
          title: 'Remove unused EBS volumes',
          description: 'Delete unattached volumes',
          impact: 'medium',
          estimatedSavings: 300,
        },
      ],
    };
  }

  async getBudgetsData() {
    // Mock budget data - can be extended with real backend endpoint
    return {
      budgets: [
        {
          id: '1',
          name: 'Production',
          limit: 5000,
          spent: 3200,
          percentage: 64,
        },
        {
          id: '2',
          name: 'Development',
          limit: 1000,
          spent: 450,
          percentage: 45,
        },
      ],
    };
  }

  async getAnomaliesData() {
    // Mock anomalies data - can be extended with real backend endpoint
    return {
      anomalies: [
        {
          id: '1',
          service: 'EC2',
          severity: 'warning',
          description: 'Unusual spike in instance count',
          detectedAt: new Date().toISOString(),
        },
      ],
    };
  }
}

// Export singleton instance
export const apiService = new APIService();

// Export convenience functions
export const getDashboardData = () => apiService.getDashboardData();
export const getSavingsData = () => apiService.getSavingsData();
export const getResourcesData = () => apiService.getResourcesData();
export const getOptimizationsData = () => apiService.getOptimizationsData();
export const getBudgetsData = () => apiService.getBudgetsData();
export const getAnomaliesData = () => apiService.getAnomaliesData();
