# API Endpoint Unit Tests Documentation

## Overview

This document describes the comprehensive unit test suite for the Advanced FinOps Platform API endpoints. The tests validate endpoint response formats, error handling, data storage operations, and performance characteristics.

## Test Structure

### Test Files

1. **`routes.test.js`** - Main API endpoint tests
2. **`validation.test.js`** - Data validation and input sanitization tests  
3. **`performance.test.js`** - Performance and load testing
4. **`jest.config.js`** - Jest configuration
5. **`jest.setup.js`** - Global test setup and utilities

### Test Categories

#### 1. Health and Documentation Endpoints
- Server health check validation
- API documentation endpoint testing
- Response format consistency

#### 2. Resource Management Endpoints
- CRUD operations for AWS resources
- Data validation and error handling
- Filtering and pagination
- Statistics generation

#### 3. Optimization Management Endpoints
- Cost optimization recommendation handling
- Approval workflow testing
- Status updates and tracking
- Complex filtering and sorting

#### 4. Error Handling
- 404 error responses
- Validation error handling
- Malformed request handling
- Edge case scenarios

#### 5. Data Validation
- Required field validation
- Enum value validation
- Numeric range validation
- Input sanitization

#### 6. Performance Testing
- Response time validation
- Concurrent request handling
- Large dataset processing
- Memory usage monitoring

## Test Coverage

### API Endpoints Tested

#### Resource Endpoints (`/api/resources`)
- `GET /api/resources` - List resources with filtering and pagination
- `POST /api/resources` - Create/update resources
- `GET /api/resources/:resourceId` - Get specific resource
- `DELETE /api/resources/:resourceId` - Remove resource
- `GET /api/resources/stats/summary` - Resource statistics

#### Optimization Endpoints (`/api/optimizations`)
- `GET /api/optimizations` - List optimizations with filtering
- `POST /api/optimizations` - Create optimization recommendations
- `POST /api/optimizations/approve` - Approve optimizations
- `GET /api/optimizations/:optimizationId` - Get specific optimization
- `PUT /api/optimizations/:optimizationId/status` - Update status
- `GET /api/optimizations/stats/summary` - Optimization statistics

#### Health Endpoints
- `GET /health` - Server health check
- `GET /api/health` - API health status
- `GET /api/docs` - API documentation

### Data Models Tested

#### ResourceInventory
- Required fields: `resourceId`, `resourceType`, `region`
- Valid resource types: `ec2`, `rds`, `lambda`, `s3`, `ebs`, `elb`, `cloudwatch`
- Cost validation: non-negative numbers
- Metadata handling: tags, configuration, state

#### CostOptimization
- Required fields: `resourceId`, `optimizationType`
- Valid optimization types: `rightsizing`, `pricing`, `cleanup`, `scheduling`
- Valid risk levels: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- Confidence score range: 0-100
- Approval workflow validation

## Test Scenarios

### Validation Tests

#### Positive Test Cases
- Valid data creation and updates
- All enum values acceptance
- Boundary value handling (0, 100 for confidence scores)
- Unicode character support
- Special character handling

#### Negative Test Cases
- Missing required fields
- Invalid enum values
- Out-of-range numeric values
- Negative cost values
- Malformed JSON handling

### Error Handling Tests

#### HTTP Status Codes
- 200: Successful operations
- 400: Validation errors
- 404: Resource not found
- 413: Request entity too large (if applicable)

#### Error Response Format
```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "errors": ["Detailed error messages"],
  "timestamp": "ISO 8601 timestamp"
}
```

### Performance Tests

#### Response Time Requirements
- Simple GET requests: < 1 second
- Complex queries: < 500ms
- POST operations: < 1 second
- Large dataset queries: < 2 seconds

#### Concurrency Tests
- 20 concurrent GET requests
- 10 concurrent POST requests
- Mixed operation scenarios
- Data integrity under concurrent access

#### Load Tests
- 100+ resource dataset handling
- Pagination efficiency
- Memory usage monitoring
- Error handling under load

## In-Memory Data Storage Tests

### Data Persistence
- Data persists across requests within test session
- Updates modify existing data correctly
- Deletions remove data from memory
- Statistics reflect current data state

### Data Integrity
- Concurrent operations don't corrupt data
- Filtering works correctly with stored data
- Pagination maintains data consistency
- Complex queries return accurate results

## Security Tests

### Input Sanitization
- SQL injection attempt handling
- XSS payload handling
- Null byte injection
- Very long string handling

### Data Validation
- Type checking for all fields
- Range validation for numeric fields
- Enum validation for categorical fields
- Required field enforcement

## Running the Tests

### Prerequisites
```bash
npm install
```

### Test Commands
```bash
# Run all tests
npm test

# Run with coverage
npm run test -- --coverage

# Run specific test file
npm test routes.test.js

# Run in watch mode
npm test -- --watch

# Run with verbose output
npm test -- --verbose
```

### Test Configuration

#### Jest Configuration (`jest.config.js`)
- Node.js test environment
- 10-second timeout for integration tests
- Coverage reporting enabled
- 80% coverage threshold

#### Global Setup (`jest.setup.js`)
- Test utilities and helpers
- Console output suppression
- Error handling setup
- Timestamp validation utilities

## Test Data Generators

### Resource Data Generator
```javascript
const generateResourceData = (overrides = {}) => ({
  resourceId: 'i-test' + Date.now(),
  resourceType: 'ec2',
  region: 'us-east-1',
  currentCost: 100.00,
  state: 'running',
  // ... additional fields
  ...overrides
});
```

### Optimization Data Generator
```javascript
const generateOptimizationData = (overrides = {}) => ({
  resourceId: 'i-opt' + Date.now(),
  region: 'us-east-1',
  optimizationType: 'rightsizing',
  currentCost: 100,
  projectedCost: 60,
  estimatedSavings: 40,
  // ... additional fields
  ...overrides
});
```

## Expected Test Results

### Coverage Targets
- **Lines**: 80%+
- **Functions**: 80%+
- **Branches**: 80%+
- **Statements**: 80%+

### Performance Benchmarks
- API response times under load
- Memory usage stability
- Concurrent request handling
- Error recovery capabilities

## Troubleshooting

### Common Issues

#### Test Timeouts
- Increase timeout in `jest.config.js`
- Check for unresolved promises
- Verify async/await usage

#### Memory Issues
- Monitor heap usage in performance tests
- Check for memory leaks in repeated operations
- Ensure proper cleanup in test teardown

#### Flaky Tests
- Use deterministic test data
- Avoid time-dependent assertions
- Implement proper test isolation

### Debug Tips
- Use `console.log` for debugging (temporarily)
- Run tests with `--verbose` flag
- Use Jest's `--detectOpenHandles` for hanging tests
- Check test isolation with `--runInBand`

## Maintenance

### Adding New Tests
1. Follow existing test structure and naming conventions
2. Use provided data generators for consistency
3. Include both positive and negative test cases
4. Add performance tests for new endpoints
5. Update this documentation

### Test Data Management
- Use unique identifiers to avoid conflicts
- Clean up test data when necessary
- Use generators for consistent test data
- Avoid hardcoded values where possible

### Continuous Integration
- Tests should run in CI/CD pipeline
- Coverage reports should be generated
- Performance benchmarks should be monitored
- Test failures should block deployments