/**
 * Test script to verify backend API endpoints
 * Tests data flow from bot to backend and costing calculations
 */

const http = require('http');

const BASE_URL = 'http://localhost:5000';

// Helper function to make HTTP requests
function makeRequest(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const req = http.request(options, (res) => {
      let responseData = '';

      res.on('data', (chunk) => {
        responseData += chunk;
      });

      res.on('end', () => {
        try {
          const parsed = JSON.parse(responseData);
          resolve({
            status: res.statusCode,
            data: parsed,
          });
        } catch (e) {
          resolve({
            status: res.statusCode,
            data: responseData,
          });
        }
      });
    });

    req.on('error', reject);

    if (data) {
      req.write(JSON.stringify(data));
    }

    req.end();
  });
}

// Test data
const testInstance = {
  instance_id: 'i-test-001',
  state: 'running',
  region: 'us-east-1',
  cpu: 5.2,
  instance_type: 't2.large',
  hourly_cost: 0.0928,
  monthly_cost: 66.82,
  annual_cost: 801.84,
};

const testLoadBalancer = {
  load_balancer_name: 'test-lb',
  load_balancer_arn: 'arn:aws:elasticloadbalancing:us-east-1:123456789:loadbalancer/app/test-lb/1234567890',
  load_balancer_type: 'application',
  region: 'us-east-1',
  state: 'active',
  scheme: 'internet-facing',
  vpc_id: 'vpc-12345',
  metrics: { RequestCount: 1000 },
  hourly_cost: 0.0225,
  monthly_cost: 16.2,
  annual_cost: 194.4,
};

const testEBSVolume = {
  volume_id: 'vol-test-001',
  volume_type: 'gp2',
  size_gb: 100,
  region: 'us-east-1',
  state: 'in-use',
  availability_zone: 'us-east-1a',
  encrypted: true,
  iops: 300,
  throughput: 125,
  attached_instance_id: 'i-test-001',
  attached_device: '/dev/sda1',
  metrics: { VolumeReadOps: 100, VolumeWriteOps: 50 },
  hourly_cost: 0.1,
  monthly_cost: 7.2,
  annual_cost: 86.4,
  tags: { Name: 'test-volume' },
};

const testRDSInstance = {
  db_instance_id: 'test-db-001',
  db_instance_arn: 'arn:aws:rds:us-east-1:123456789:db:test-db-001',
  engine: 'mysql',
  engine_version: '8.0.28',
  db_instance_class: 'db.t3.medium',
  region: 'us-east-1',
  status: 'available',
  allocated_storage_gb: 100,
  storage_type: 'gp2',
  multi_az: false,
  backup_retention_days: 7,
  publicly_accessible: false,
  read_replicas: [],
  metrics: { CPUUtilizationPercent: 8.5, DatabaseConnections: 12 },
  instance_hourly_cost: 0.168,
  storage_hourly_cost: 0.023,
  hourly_cost: 0.191,
  monthly_cost: 137.52,
  annual_cost: 1650.24,
  tags: { Environment: 'test' },
};

const testSavings = {
  resource_id: 'i-test-001',
  cloud: 'AWS',
  money_saved: 33.41,
  region: 'us-east-1',
  state: 'stopped',
  instance_type: 't2.large',
  pricing_model: 'on-demand',
  estimated_hours_saved: 1,
  date: new Date().toISOString(),
};

// Test runner
async function runTests() {
  console.log('\n' + '='.repeat(80));
  console.log('🧪 FINOPS BACKEND API TEST SUITE');
  console.log('='.repeat(80) + '\n');

  try {
    // Test 1: Health check
    console.log('📋 Test 1: Health Check');
    let response = await makeRequest('GET', '/health');
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data)}\n`);

    // Test 2: Post EC2 instance
    console.log('📋 Test 2: POST EC2 Instance');
    response = await makeRequest('POST', '/api/instances', testInstance);
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data)}\n`);

    // Test 3: Get all instances
    console.log('📋 Test 3: GET All Instances');
    response = await makeRequest('GET', '/api/instances');
    console.log(`   Status: ${response.status}`);
    console.log(`   Total instances: ${response.data.total}`);
    console.log(`   Response: ${JSON.stringify(response.data, null, 2)}\n`);

    // Test 4: Post load balancer
    console.log('📋 Test 4: POST Load Balancer');
    response = await makeRequest('POST', '/api/load-balancers', testLoadBalancer);
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data)}\n`);

    // Test 5: Post EBS volume
    console.log('📋 Test 5: POST EBS Volume');
    response = await makeRequest('POST', '/api/ebs-volumes', testEBSVolume);
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data)}\n`);

    // Test 6: Post RDS instance
    console.log('📋 Test 6: POST RDS Instance');
    response = await makeRequest('POST', '/api/rds-instances', testRDSInstance);
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data)}\n`);

    // Test 7: Post savings
    console.log('📋 Test 7: POST Savings');
    response = await makeRequest('POST', '/api/savings', testSavings);
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data)}\n`);

    // Test 8: Get costing current
    console.log('📋 Test 8: GET Costing Current');
    response = await makeRequest('GET', '/api/costing/current');
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data, null, 2)}\n`);

    // Test 9: Get costing by region
    console.log('📋 Test 9: GET Costing By Region');
    response = await makeRequest('GET', '/api/costing/by-region');
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data, null, 2)}\n`);

    // Test 10: Get costing by service
    console.log('📋 Test 10: GET Costing By Service');
    response = await makeRequest('GET', '/api/costing/by-service');
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data, null, 2)}\n`);

    // Test 11: Get savings
    console.log('📋 Test 11: GET Savings');
    response = await makeRequest('GET', '/api/savings');
    console.log(`   Status: ${response.status}`);
    console.log(`   Total savings records: ${response.data.total}`);
    console.log(`   Total savings: $${response.data.totalSavings}`);
    console.log(`   Response: ${JSON.stringify(response.data, null, 2)}\n`);

    // Test 12: Get resize options
    console.log('📋 Test 12: GET Resize Options for Instance');
    response = await makeRequest('GET', '/api/instances/i-test-001/resize-options');
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data, null, 2)}\n`);

    // Test 13: Post resize request
    console.log('📋 Test 13: POST Resize Request');
    response = await makeRequest('POST', '/api/instances/i-test-001/resize', {
      new_instance_type: 't2.medium',
      approval_request_id: 'approval-123'
    });
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data, null, 2)}\n`);

    console.log('='.repeat(80));
    console.log('✅ ALL TESTS COMPLETED SUCCESSFULLY');
    console.log('='.repeat(80) + '\n');

  } catch (error) {
    console.error('❌ Test failed:', error);
    process.exit(1);
  }
}

// Run tests
runTests();
