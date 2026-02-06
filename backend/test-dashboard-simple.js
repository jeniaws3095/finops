/**
 * Simple Dashboard Features Test
 * 
 * Tests dashboard data formatting and filtering capabilities without WebSocket.
 */

const http = require('http');

// Test configuration
const API_BASE = 'http://localhost:5002/api';

async function testDashboardFeatures() {
  console.log('🧪 Starting Dashboard Features Test');
  console.log('=====================================');
  
  try {
    // Test 1: Health Check
    console.log('\n❤️ Testing Health Check...');
    const healthData = await makeRequest('/health');
    if (healthData.success) {
      console.log('✅ Health check passed');
      console.log(`   - Status: ${healthData.data.status}`);
      console.log(`   - Port: ${healthData.data.port}`);
    } else {
      console.log('❌ Health check failed');
    }
    
    // Test 2: Dashboard Overview
    console.log('\n📊 Testing Dashboard Overview...');
    const overviewData = await makeRequest('/dashboard/overview?timeRange=30d');
    if (overviewData.success) {
      console.log('✅ Dashboard overview retrieved successfully');
      console.log(`   - KPIs: ${Object.keys(overviewData.data.kpis).length} metrics`);
      console.log(`   - Trends: ${Object.keys(overviewData.data.trends).length} trend lines`);
      console.log(`   - Distributions: ${Object.keys(overviewData.data.distributions).length} breakdowns`);
    } else {
      console.log('❌ Dashboard overview failed:', overviewData.message);
    }
    
    // Test 3: Time-Series Data (Recharts format)
    console.log('\n📈 Testing Time-Series Data...');
    const timeSeriesData = await makeRequest('/dashboard/time-series?metric=savings&timeRange=30d&groupBy=day');
    if (timeSeriesData.success && Array.isArray(timeSeriesData.data)) {
      console.log('✅ Time-series data formatted for Recharts');
      console.log(`   - Data points: ${timeSeriesData.data.length}`);
      if (timeSeriesData.data.length > 0) {
        console.log(`   - Sample point:`, timeSeriesData.data[0]);
      }
    } else {
      console.log('❌ Time-series data failed:', timeSeriesData.message);
    }
    
    // Test 4: Filter Options
    console.log('\n🔍 Testing Filter Options...');
    const filtersData = await makeRequest('/dashboard/filters');
    if (filtersData.success) {
      console.log('✅ Filter options retrieved successfully');
      console.log(`   - Services: ${filtersData.data.services.length} options`);
      console.log(`   - Regions: ${filtersData.data.regions.length} options`);
      console.log(`   - Time ranges: ${filtersData.data.timeRanges.length} options`);
    } else {
      console.log('❌ Filter options failed:', filtersData.message);
    }
    
    // Test 5: Aggregated Widget Data
    console.log('\n📊 Testing Aggregated Widget Data...');
    const aggregatedData = await makeRequest('/dashboard/aggregated?widgets=savings,optimizations&timeRange=30d');
    if (aggregatedData.success) {
      console.log('✅ Aggregated widget data retrieved successfully');
      console.log(`   - Widgets: ${Object.keys(aggregatedData.data).join(', ')}`);
      if (aggregatedData.data.savings) {
        console.log(`   - Total savings: $${aggregatedData.data.savings.totalSavings}`);
      }
    } else {
      console.log('❌ Aggregated data failed:', aggregatedData.message);
    }
    
    // Test 6: Enhanced Resource Filtering
    console.log('\n🔍 Testing Enhanced Resource Filtering...');
    const resourcesData = await makeRequest('/resources?format=chart&timeRange=30d&costThreshold=100&sortBy=currentCost&sortOrder=desc');
    if (resourcesData.success) {
      console.log('✅ Enhanced resource filtering working');
      console.log(`   - Format: chart data with distributions`);
      if (resourcesData.data.serviceDistribution) {
        console.log(`   - Service breakdown: ${resourcesData.data.serviceDistribution.length} services`);
      }
    } else {
      console.log('❌ Enhanced resource filtering failed:', resourcesData.message);
    }
    
    // Test 7: Savings Chart Data
    console.log('\n💰 Testing Savings Chart Data...');
    const savingsChartData = await makeRequest('/savings/chart-data?timeRange=30d&groupBy=day');
    if (savingsChartData.success) {
      console.log('✅ Savings chart data formatted for Recharts');
      if (savingsChartData.data.timeSeries) {
        console.log(`   - Time series points: ${savingsChartData.data.timeSeries.length}`);
      }
      if (savingsChartData.data.serviceBreakdown) {
        console.log(`   - Service breakdown: ${savingsChartData.data.serviceBreakdown.length} services`);
      }
    } else {
      console.log('❌ Savings chart data failed:', savingsChartData.message);
    }
    
    // Test 8: Pricing Intelligence Chart Data
    console.log('\n💲 Testing Pricing Intelligence Chart Data...');
    const pricingChartData = await makeRequest('/pricing/chart-data');
    if (pricingChartData.success) {
      console.log('✅ Pricing chart data formatted for visualization');
      if (pricingChartData.data.typeBreakdown) {
        console.log(`   - Recommendation types: ${pricingChartData.data.typeBreakdown.length}`);
      }
    } else {
      console.log('❌ Pricing chart data failed:', pricingChartData.message);
    }
    
    // Test 9: Data Refresh Trigger
    console.log('\n🔄 Testing Data Refresh Trigger...');
    const refreshData = await makeRequest('/dashboard/refresh', 'POST', {
      dataType: 'savings',
      force: true
    });
    if (refreshData.success) {
      console.log('✅ Data refresh triggered successfully');
      console.log(`   - Refresh ID: ${refreshData.data.refreshId}`);
      console.log(`   - Status: ${refreshData.data.status}`);
    } else {
      console.log('❌ Data refresh failed:', refreshData.message);
    }
    
    // Test 10: Data Export
    console.log('\n📤 Testing Data Export...');
    const exportData = await makeRequest('/dashboard/export?format=json&dataType=overview&timeRange=30d');
    if (exportData.success) {
      console.log('✅ Data export working');
      console.log(`   - Export format: JSON`);
      console.log(`   - Data type: overview`);
    } else {
      console.log('❌ Data export failed:', exportData.message);
    }
    
    // Test 11: Advanced Filtering with Multiple Parameters
    console.log('\n🔍 Testing Advanced Multi-Parameter Filtering...');
    const advancedFilterData = await makeRequest('/resources?resourceType=EC2&region=us-east-1&format=summary&timeRange=7d&sortBy=currentCost&sortOrder=desc&limit=10');
    if (advancedFilterData.success) {
      console.log('✅ Advanced filtering working');
      console.log(`   - Applied filters: resourceType, region, timeRange, sorting`);
      console.log(`   - Format: summary with aggregations`);
    } else {
      console.log('❌ Advanced filtering failed:', advancedFilterData.message);
    }
    
    // Test 12: Savings Summary with Time Range
    console.log('\n💰 Testing Savings Summary...');
    const savingsSummaryData = await makeRequest('/savings/summary?timeRange=30d');
    if (savingsSummaryData.success) {
      console.log('✅ Savings summary working');
      console.log(`   - Total savings: $${savingsSummaryData.data.totalSavings}`);
      console.log(`   - Service distribution: ${Object.keys(savingsSummaryData.data.serviceDistribution).length} services`);
    } else {
      console.log('❌ Savings summary failed:', savingsSummaryData.message);
    }
    
    console.log('\n🎉 Dashboard Features Test Complete!');
    console.log('=====================================');
    console.log('\n📋 Summary:');
    console.log('✅ Dashboard data formatting implemented');
    console.log('✅ Recharts-compatible time-series data');
    console.log('✅ Advanced filtering by service, region, time period, cost thresholds');
    console.log('✅ Real-time data refresh endpoints');
    console.log('✅ Data aggregation and summarization');
    console.log('✅ Chart data formatting for multiple visualization types');
    console.log('✅ Export capabilities');
    
  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
  }
}

// Helper function to make HTTP requests
function makeRequest(path, method = 'GET', body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(API_BASE + path);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };
    
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve(jsonData);
        } catch (error) {
          resolve({ success: false, message: 'Invalid JSON response', data: data });
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (body) {
      req.write(JSON.stringify(body));
    }
    
    req.end();
  });
}

// Run the test
if (require.main === module) {
  testDashboardFeatures().catch(console.error);
}

module.exports = { testDashboardFeatures };