# FinOps Backend - Multi-Metric Optimization API

Node.js/Express backend for the FinOps automation platform. Provides REST APIs for metric collection, threshold management, analysis, recommendations, and approval workflows.

## Architecture

- **Framework**: Express.js with TypeScript
- **Database**: MongoDB
- **Pattern**: Repository pattern for data access
- **Error Handling**: Custom error classes with structured logging

## Project Structure

```
src/
├── app.ts                    # Express application setup
├── index.ts                  # Entry point
├── config.ts                 # Configuration management
├── types/                    # TypeScript interfaces
├── db/                       # Database layer
│   ├── connection.ts         # MongoDB connection
│   ├── schemas.ts            # Collection schemas
│   └── repositories/         # Data access layer
├── services/                 # Business logic layer
├── routes/                   # API endpoints
├── middleware/               # Express middleware
└── utils/                    # Utilities (logging, errors)
```

## Getting Started

### Prerequisites

- Node.js 18+
- MongoDB 6.0+
- AWS credentials configured

### Installation

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Running

**Development**:
```bash
npm run dev
```

**Production**:
```bash
npm run build
npm start
```

## API Endpoints

### Metrics

- `POST /api/metrics` - Store metrics from finops-bot
- `GET /api/metrics` - List metrics with filtering
- `GET /api/metrics/:resourceId` - Get metrics for specific resource

### Thresholds

- `GET /api/thresholds` - List active thresholds
- `GET /api/thresholds/:serviceType/:metricName` - Get specific threshold
- `GET /api/thresholds/:serviceType/:metricName/history` - Get threshold history
- `POST /api/thresholds` - Create new threshold
- `PUT /api/thresholds/:id` - Update threshold

## Environment Variables

```
MONGODB_URI=mongodb://localhost:27017
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
METRIC_RETENTION_DAYS=30
AUDIT_RETENTION_DAYS=90
PORT=3000
NODE_ENV=development
```

## Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm test:watch

# Run tests with coverage
npm test -- --coverage
```

## Development

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Database

### Collections

- `metrics` - CloudWatch metric data
- `thresholds` - Optimization thresholds
- `recommendations` - Generated recommendations
- `approval_requests` - Approval workflow requests
- `approval_decisions` - Approval decisions
- `audit_trail` - Audit trail entries
- `analysis_results` - Analysis results

### Indexes

Indexes are automatically created on application startup for:
- Metrics: resourceId, metricName, timestamp, serviceType
- Thresholds: serviceType, metricName, effectiveFrom
- Approval requests: status, createdAt, resourceId, serviceType
- Audit trail: resourceId, actionType, timestamp, actorId

## Error Handling

Custom error classes:
- `OptimizationError` - Base error class
- `ValidationError` - Input validation errors (400)
- `NotFoundError` - Resource not found (404)
- `DatabaseError` - Database operation errors (500)

All errors are logged with context and returned as JSON responses.

## Logging

Structured logging via `createLogger(context)`:
- DEBUG - Detailed debugging information
- INFO - General information
- WARN - Warning messages
- ERROR - Error messages

## Contributing

1. Follow TypeScript strict mode
2. Add tests for new features
3. Update documentation
4. Follow naming conventions (kebab-case for files, PascalCase for classes)

## License

ISC
