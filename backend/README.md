# Advanced FinOps Platform - Backend API

Enterprise-grade AWS cost optimization backend API server for the Advanced FinOps Platform.

## Overview

This Express.js API server provides comprehensive cost optimization capabilities including:

- **Multi-Service Resource Discovery**: EC2, RDS, Lambda, S3, EBS, ELB, CloudWatch
- **ML-Powered Right-Sizing**: Machine learning recommendations with confidence intervals
- **Pricing Intelligence**: Reserved Instances, Spot Instances, Savings Plans analysis
- **Cost Anomaly Detection**: Automated spike detection with root cause analysis
- **Budget Management**: Hierarchical budgets with forecasting and variance tracking
- **Approval Workflows**: Risk-based optimization approval processes

## Architecture

- **Port**: 5002 (to avoid conflicts with existing FinOps platform on 5000)
- **Storage**: In-memory arrays for demo simplicity
- **Response Format**: Standardized `{success, data, message, timestamp}` format
- **CORS**: Enabled for frontend communication
- **Error Handling**: Comprehensive error handling with detailed logging

## API Endpoints

### Core Resources
- `GET /health` - Health check endpoint
- `GET /api/docs` - API documentation
- `GET /api/resources` - Retrieve resource inventory
- `POST /api/resources` - Add/update resource data
- `GET /api/resources/:resourceId` - Get specific resource
- `DELETE /api/resources/:resourceId` - Remove resource
- `GET /api/resources/stats/summary` - Resource statistics

### Future Endpoints (to be implemented in subsequent tasks)
- `/api/optimizations` - Cost optimization recommendations
- `/api/anomalies` - Cost anomaly detection and alerts
- `/api/budgets` - Budget management and forecasting
- `/api/savings` - Savings tracking and ROI analysis
- `/api/pricing` - Pricing intelligence recommendations

## Data Models

### ResourceInventory
Represents discovered AWS resources with utilization metrics and optimization opportunities.

**Required Fields:**
- `resourceId`: AWS resource identifier
- `resourceType`: Service type ('ec2', 'rds', 'lambda', 's3', 'ebs', 'elb', 'cloudwatch')
- `region`: AWS region
- `timestamp`: ISO format creation time

### CostOptimization
Represents optimization recommendations with approval workflow and risk assessment.

**Key Features:**
- Risk-based approval requirements
- Confidence scoring (0-100)
- Rollback capabilities
- Savings projections

### CostAnomaly
Represents detected cost anomalies with root cause analysis.

**Detection Types:**
- Spike detection
- Trend analysis
- Pattern recognition
- Baseline shifts

### BudgetForecast
Represents budget forecasts with hierarchical support and variance tracking.

**Capabilities:**
- Multi-level budget hierarchies
- Confidence intervals
- Variance analysis
- Risk assessment

## Installation

```bash
cd advanced-finops-backend
npm install
```

## Running the Server

```bash
# Development mode
npm start

# With auto-reload (if nodemon is installed)
npm run dev
```

The server will start on port 5002:
- Health check: http://localhost:5002/health
- API documentation: http://localhost:5002/api/docs
- Base API URL: http://localhost:5002/api

## Dependencies

- **express**: Web framework
- **cors**: Cross-origin resource sharing
- **body-parser**: Request body parsing
- **nodemon**: Development auto-reload (dev dependency)

## Development Guidelines

### Safety Requirements
- Never hardcode AWS credentials
- Implement comprehensive error handling
- Use DRY_RUN flags for destructive operations
- Include detailed logging for all operations

### Code Standards
- Follow camelCase for JavaScript files
- Use descriptive variable names
- Implement proper input validation
- Return standardized response format

### Testing
- Unit tests for all endpoints
- Property-based tests for business logic
- AWS service mocking with `moto`
- Error scenario testing

## Integration

This backend is designed to work with:
- **Python Automation Engine** (`advanced-finops-bot/`): Sends optimization data via HTTP
- **React Dashboard** (`advanced-finops-frontend/`): Consumes API for visualization
- **AWS Services**: Integrates with Cost Explorer, CloudWatch, Billing APIs

## Next Steps

1. Implement remaining API endpoints (optimizations, anomalies, budgets, etc.)
2. Add comprehensive input validation and error handling
3. Implement property-based testing for correctness validation
4. Add authentication and authorization
5. Integrate with AWS Cost Management APIs
6. Add real-time data streaming capabilities

## Requirements Fulfilled

- **Requirement 9.1**: Real-time cost monitoring API endpoints
- **Requirement 10.1**: Integration foundation for AWS Cost Management APIs
- **Architecture**: Three-tier pattern with Express.js on port 5002
- **Data Models**: Complete model schemas for all core entities
- **API Structure**: RESTful endpoints following `/api/{resource}` pattern