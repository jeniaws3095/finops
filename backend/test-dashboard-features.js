/**
 * Test Dashboard Features
 * 
 * Comprehensive test for dashboard data formatting and real-time capabilities.
 * Tests all the new features implemented in task 14.2.
 */

const WebSocket = require('ws');
const http = require('http');

// Test configuration
const API_BASE = 'http://localhost:5002/api';
const WS_URL = 'ws://localhost:5002';

async function testDashboardFeatures() {
  console.log('🧪 Starting Dashboard Features Test');
  console.log('=====================================');
  
  try {
    // Test 1: Dashboard Overview
    console.log('\n📊 Testing Dashboard Overview...');
    const overviewResponse = await fetch(`${API_BASE}/dashboard/overview?timeRange=30d`);
    const overviewData = await overviewResponse.json();
    
    if (overviewData.success) {
      console.log('✅ Dashboard overview retrieved successfully');
      console.log(`   - KPIs: ${Object.keys(overviewData.data.kpis).length} metrics`);
      console.log(`   - Trends: ${Object.keys(overviewData.data.trends).length} trend lines`);
      console.log(`   - Distributions: ${Object.keys(overviewData.data.distributions).length} breakdowns`);
    } else {
      console.log('❌ Dashboard overview failed:', overviewData.message);
    }
    
    // Test 2: Time-Series Data (Recharts format)
    console.log('\n📈 Testing Time-Series Data...');
    const timeSeriesResponse = await fetch(`${API_BASE}/dashboard/time-series?metric=savings&timeRange=30d&groupBy=day`);
    const timeSeriesData = await timeSeriesResponse.json();
    
    if (timeSeriesData.success && Array.isArray(timeSeriesData.data)) {
      console.log('✅ Time-series data formatted for Recharts');
      console.log(`   - Data points: ${timeSeriesData.data.length}`);
      console.log(`   - Sample point:`, timeSeriesData.data[0]);
    } else {
      console.log('❌ Time-series data failed:', timeSeriesData.message);
    }
    
    // Test 3: Filter Options
    console.log('\n🔍 Testing Filter Options...');
    const filtersResponse = await fetch(`${API_BASE}/dashboard/filters`);
    const filtersData = await filtersResponse.json();
    
    if (filtersData.success) {
      console.log('✅ Filter options retrieved successfully');
      console.log(`   - Services: ${filtersData.data.services.length} options`);
      console.log(`   - Regions: ${filtersData.data.regions.length} options`);
      console.log(`   - Time ranges: ${filtersData.data.timeRanges.length} options`);
    } else {
      console.log('❌ Filter options failed:', filtersData.message);
    }
    
    // Test 4: Aggregated Widget Data
    console.log('\n📊 Testing Aggregated Widget Data...');
    const aggregatedResponse = await fetch(`${API_BASE}/dashboard/aggregated?widgets=savings,optimizations&timeRange=30d`);
    const aggregatedData = await aggregatedResponse.json();
    
    if (aggregatedData.success) {
      console.log('✅ Aggregated widget data retrieved successfully');
      console.log(`   - Widgets: ${Object.keys(aggregatedData.data).join(', ')}`);
      if (aggregatedData.data.savings) {
        console.log(`   - Total savings: $${aggregatedData.data.savings.totalSavings}`);
      }
    } else {
      console.log('❌ Aggregated data failed:', aggregatedData.message);
    }
    
    // Test 5: Enhanced Resource Filtering
    console.log('\n🔍 Testing Enhanced Resource Filtering...');
    const resourcesResponse = await fetch(`${API_BASE}/resources?format=chart&timeRange=30d&costThreshold=100&sortBy=currentCost&sortOrder=desc`);
    const resourcesData = await resourcesResponse.json();
    
    if (resourcesData.success) {
      console.log('✅ Enhanced resource filtering working');
      console.log(`   - Format: chart data with distributions`);
      if (resourcesData.data.serviceDistribution) {
        console.log(`   - Service breakdown: ${resourcesData.data.serviceDistribution.length} services`);
      }
    } else {
      console.log('❌ Enhanced resource filtering failed:', resourcesData.message);
    }
    
    // Test 6: Savings Chart Data
    console.log('\n💰 Testing Savings Chart Data...');
    const savingsChartResponse = await fetch(`${API_BASE}/savings/chart-data?timeRange=30d&groupBy=day`);
    const savingsChartData = await savingsChartResponse.json();
    
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
    
    // Test 7: Pricing Intelligence Chart Data
    console.log('\n💲 Testing Pricing Intelligence Chart Data...');
    const pricingChartResponse = await fetch(`${API_BASE}/pricing/chart-data`);
    const pricingChartData = await pricingChartResponse.json();
    
    if (pricingChartData.success) {
      console.log('✅ Pricing chart data formatted for visualization');
      if (pricingChartData.data.typeBreakdown) {
        console.log(`   - Recommendation types: ${pricingChartData.data.typeBreakdown.length}`);
      }
    } else {
      console.log('❌ Pricing chart data failed:', pricingChartData.message);
    }
    
    // Test 8: WebSocket Real-time Updates
    console.log('\n🔌 Testing WebSocket Real-time Updates...');
    await testWebSocketConnection();
    
    // Test 9: Data Refresh Trigger
    console.log('\n🔄 Testing Data Refresh Trigger...');
    const refreshResponse = await fetch(`${API_BASE}/dashboard/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        dataType: 'savings',
        force: true
      })
    });
    const refreshData = await refreshResponse.json();
    
    if (refreshData.success) {
      console.log('✅ Data refresh triggered successfully');
      console.log(`   - Refresh ID: ${refreshData.data.refreshId}`);
      console.log(`   - Status: ${refreshData.data.status}`);
    } else {
      console.log('❌ Data refresh failed:', refreshData.message);
    }
    
    // Test 10: Data Export
    console.log('\n📤 Testing Data Export...');
    const exportResponse = await fetch(`${API_BASE}/dashboard/export?format=json&dataType=overview&timeRange=30d`);
    const exportData = await exportResponse.json();
    
    if (exportData.success) {
      console.log('✅ Data export working');
      console.log(`   - Export format: JSON`);
      console.log(`   - Data type: overview`);
    } else {
      console.log('❌ Data export failed:', exportData.message);
    }
    
    console.log('\n🎉 Dashboard Features Test Complete!');
    console.log('=====================================');
    
  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
  }
}

async function testWebSocketConnection() {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(WS_URL);
    let messageCount = 0;
    
    ws.on('open', () => {
      console.log('✅ WebSocket connection established');
    });
    
    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        messageCount++;
        console.log(`   - Received message ${messageCount}: ${message.type}`);
        
        if (messageCount >= 2) { // Wait for connection + one update message
          ws.close();
          resolve();
        }
      } catch (error) {
        console.log('   - Received non-JSON message:', data.toString());
      }
    });
    
    ws.on('error', (error) => {
      console.log('❌ WebSocket error:', error.message);
      reject(error);
    });
    
    ws.on('close', () => {
      console.log('🔌 WebSocket connection closed');
      resolve();
    });
    
    // Timeout after 5 seconds
    setTimeout(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      resolve();
    }, 5000);
  });
}

// Helper function for fetch (Node.js doesn't have fetch by default in older versions)
async function fetch(url, options = {}) {
  const https = require('https');
  const http = require('http');
  const urlParsed = new URL(url);
  const client = urlParsed.protocol === 'https:' ? https : http;
  
  return new Promise((resolve, reject) => {
    const req = client.request({
      hostname: urlParsed.hostname,
      port: urlParsed.port,
      path: urlParsed.pathname + urlParsed.search,
      method: options.method || 'GET',
      headers: options.headers || {}
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({
            json: () => Promise.resolve(jsonData),
            success: res.statusCode >= 200 && res.statusCode < 300
          });
        } catch (error) {
          resolve({
            json: () => Promise.resolve({ success: false, message: 'Invalid JSON response' }),
            success: false
          });
        }
      });
    });
    
    req.on('error', reject);
    
    if (options.body) {
      req.write(options.body);
    }
    
    req.end();
  }).then(res => ({
    ...res,
    json: res.json
  }));
}

// Run the test
if (require.main === module) {
  testDashboardFeatures().catch(console.error);
}

module.exports = { testDashboardFeatures };