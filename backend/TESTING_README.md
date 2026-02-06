# Advanced FinOps Platform - API Testing Guide

## Overview

This directory contains comprehensive unit tests for the Advanced FinOps Platform API endpoints. The test suite validates endpoint response formats, error handling, data storage operations, and performance characteristics as required by **Requirement 9.1**.

## Quick Start

### Prerequisites
Ensure Node.js and npm are installed, then install dependencies:

```bash
npm install
```

### Running Tests

```bash
# Run all tests
npm test

# Run with coverage report
npm run test:coverage

# Run in watch mode (for development)
npm run test:watch

# Run with verbose output
npm run test:verbose

# Run specific test categories
npm run test:routes        # Main API endpoint tests
npm run test:validation    # Data validation tests
npm run test:performance   # Performance and load tests

# Run for CI/CD (no watch, with coverage)
npm run test:ci
```

## Test Structure

### Test Files

| File | Purpose | Coverage |
|------|---------|----------|
| `routes.test.js` | Main API endpoint testing | All CRUD operations, filtering, pagination |
| `validation.test.js` | Data validation and sanitization | Input validation, boundary testing, security |
| `performance.test.js` | Performance and load testing | Response times, concurrency, memory usage |
| `jest.config.js` | Jest configuration | Test environment setup |
| `jest.setup.js` | Global test utilities | Helper functions, test data generators |

### Test Categories

#### ✅ Health and Documentation Endpoints
- Server health check (`GET /health`)
- API health status (`GET /api/health`)
- API documentation (`GET /api/docs`)

#### ✅ Resource Management Endpoints
- List resources with filtering (`GET /api/resources`)
- Create/update resources (`POST /api/resources`)
- Get specific resource (`GET /api/resources/:id`)
- Delete resource (`DELETE /api/resources/:id`)
- Resource statistics (`GET /api/resources/stats/summary`)

#### ✅ Optimization Management Endpoints
- List optimizations (`GET /api/optimizations`)
- Create optimizations (`POST /api/optimizations`)
- Approve optimizations (`POST /api/optimizations/approve`)
- Get specific optimization (`GET /api/optimizations/:id`)
- Update optimization status (`PUT /api/optimizations/:id/status`)
- Optimization statistics (`GET /api/optimizations/stats/summary`)

#### ✅ Error Handling
- 404 responses for non-existent resources
- 400 responses for validation errors
- Malformed JSON handling
- Edge case scenarios

#### ✅ Data Validation
- Required field validation
- Enum value validation (resourceType, optimizationType, riskLevel)
- Numeric range validation (confidenceScore: 0-100)
- Non-negative cost validation
- Input sanitization (XSS, SQL injection attempts)

#### ✅ In-Memory Data Storage
- Data persistence across requests
- CRUD operation integrity
- Concurrent access handling
- Statistics accuracy

#### ✅ Performance Testing
- Response time validation (< 1 second for simple operations)
- Concurrent request handling (20+ simultaneous requests)
- Large dataset processing (100+ resources)
- Memory usage monitoring

## Test Data

### Resource Data Structure
```javascript
{
  resourceId: "i-1234567890abcdef0",
  resourceType: "ec2", // ec2, rds, lambda, s3, ebs, elb, cloudwatch
  region: "us-east-1",
  currentCost: 150.50,
  state: "running",
  utilizationMetrics: {
    cpu: [25.5, 30.2, 28.1],
    memory: [60.2, 65.8, 62.3]
  },
  optimizationOpportunities: ["rightsizing"],
  tags: { Environment: "prod", Team: "finops" }
}
```

### Optimization Data Structure
```javascript
{
  resourceId: "i-1234567890abcdef0",
  region: "us-east-1",
  optimizationType: "rightsizing", // rightsizing, pricing, cleanup, scheduling
  currentCost: 100,
  projectedCost: 60,
  estimatedSavings: 40,
  confidenceScore: 85, // 0-100
  riskLevel: "LOW", // LOW, MEDIUM, HIGH, CRITICAL
  description: "Right-size EC2 instance from m5.large to m5.medium"
}
```

## Expected Response Format

All API endpoints follow the standardized response format:

### Success Response
```javascript
{
  success: true,
  data: { /* response data */ },
  message: "Operation completed successfully",
  timestamp: "2024-01-15T10:30:00.000Z",
  metadata: { /* pagination, stats, etc. */ }
}
```

### Error Response
```javascript
{
  success: false,
  data: null,
  message: "Error description",
  errors: ["Detailed error messages"],
  timestamp: "2024-01-15T10:30:00.000Z"
}
```

## Test Coverage Requirements

The test suite maintains high coverage standards:

- **Lines**: 80%+
- **Functions**: 80%+
- **Branches**: 80%+
- **Statements**: 80%+

### Coverage Report
```bash
npm run test:coverage
```

View detailed coverage report in `coverage/lcov-report/index.html`

## Performance Benchmarks

### Response Time Targets
- Simple GET requests: < 1 second
- Complex queries with filtering: < 500ms
- POST operations: < 1 second
- Large dataset queries (100+ items): < 2 seconds

### Concurrency Targets
- Handle 20+ concurrent GET requests
- Handle 10+ concurrent POST requests
- Maintain data integrity under concurrent access
- Graceful error handling under load

### Memory Usage
- No significant memory leaks during repeated operations
- Memory increase < 50MB during load tests
- Efficient garbage collection

## Validation Rules

### Resource Validation
- `resourceId`: Required, non-empty string
- `resourceType`: Required, must be one of: `ec2`, `rds`, `lambda`, `s3`, `ebs`, `elb`, `cloudwatch`
- `region`: Required, non-empty string
- `currentCost`: Must be non-negative number

### Optimization Validation
- `resourceId`: Required, non-empty string
- `optimizationType`: Required, must be one of: `rightsizing`, `pricing`, `cleanup`, `scheduling`
- `riskLevel`: Must be one of: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `confidenceScore`: Must be number between 0 and 100
- `currentCost`, `projectedCost`: Must be non-negative numbers

## Security Testing

### Input Sanitization Tests
- SQL injection attempts: `'; DROP TABLE resources; --`
- XSS attempts: `<script>alert("XSS")</script>`
- Null byte injection: `test\x00malicious`
- Very long strings (10,000+ characters)

### Boundary Value Testing
- Maximum safe integer values
- Floating point precision
- Edge case confidence scores (0, 0.1, 99.9, 100)
- Unicode character handling

## Troubleshooting

### Common Issues

#### Tests Timing Out
```bash
# Increase timeout in jest.config.js
testTimeout: 15000
```

#### Memory Issues
```bash
# Run with memory monitoring
node --expose-gc --max-old-space-size=4096 node_modules/.bin/jest
```

#### Debugging Failed Tests
```bash
# Run with verbose output
npm run test:verbose

# Run specific test file
npm test -- routes.test.js --verbose

# Run with debug information
DEBUG=* npm test
```

### Test Isolation
Each test is designed to be independent and can run in any order. However, some tests create data that persists within the test session (in-memory storage).

### CI/CD Integration
```bash
# Use this command in CI/CD pipelines
npm run test:ci
```

## Development Workflow

### Adding New Tests
1. Follow existing test structure and naming conventions
2. Use provided data generators (`generateResourceData`, `generateOptimizationData`)
3. Include both positive and negative test cases
4. Add performance tests for new endpoints
5. Update test documentation

### Test-Driven Development
1. Write tests for new API endpoints before implementation
2. Run tests to ensure they fail initially
3. Implement the endpoint functionality
4. Run tests to verify implementation
5. Refactor while maintaining test coverage

### Continuous Testing
```bash
# Run tests in watch mode during development
npm run test:watch
```

## Integration with Requirements

This test suite directly validates **Requirement 9.1**:
- ✅ Test endpoint response formats
- ✅ Test error handling
- ✅ Test in-memory data storage and retrieval
- ✅ Validate API consistency and reliability
- ✅ Ensure proper HTTP status codes
- ✅ Verify data integrity and validation

## Next Steps

After completing this task, the API endpoints are thoroughly tested and ready for:
1. Python automation engine integration (Task 3+)
2. Frontend dashboard development
3. Production deployment with confidence
4. Continuous integration/deployment pipelines

For detailed test documentation, see `TEST_DOCUMENTATION.md`.