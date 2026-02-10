# Backend Architecture - Node.js Express

## Overview

The finops-backend is a Node.js/Express REST API built with TypeScript that serves as the central business logic layer for the FinOps automation platform. It receives metrics from the Python bot, performs analysis, generates recommendations, and manages approval workflows.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Express Routes                            │
│  /api/metrics, /api/thresholds, /api/approvals, etc.        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Services Layer                             │
│  MetricsService, ThresholdService, AnalysisService, etc.    │
│  - Business logic                                            │
│  - Validation                                                │
│  - Orchestration                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 Repositories Layer                           │
│  MetricsRepository, ThresholdRepository, etc.               │
│  - Data access abstraction                                   │
│  - Query building                                            │
│  - Error handling                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  MongoDB Database                            │
│  Collections: metrics, thresholds, approvals, audit_trail   │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
finops-backend/
├── src/
│   ├── app.ts                          # Express app factory
│   ├── index.ts                        # Entry point & server startup
│   ├── config.ts                       # Configuration management
│   │
│   ├── types/
│   │   └── index.ts                    # TypeScript interfaces
│   │
│   ├── db/
│   │   ├── connection.ts               # MongoDB connection
│   │   ├── schemas.ts                  # Collection schemas
│   │   └── repositories/
│   │       ├── base.repository.ts      # Abstract CRUD class
│   │       ├── metrics.repository.ts   # Metrics data access
│   │       ├── threshold.repository.ts # Thresholds data access
│   │       ├── approval.repository.ts  # Approvals data access
│   │       ├── audit.repository.ts     # Audit trail data access
│   │       ├── analysis.repository.ts  # Analysis results data access
│   │       ├── recommendation.repository.ts # Recommendations data access
│   │       └── index.ts                # Repository exports
│   │
│   ├── services/
│   │   ├── metrics.service.ts          # Metrics business logic
│   │   ├── threshold.service.ts        # Threshold business logic
│   │   └── index.ts                    # Service exports
│   │
│   ├── routes/
│   │   ├── metrics.routes.ts           # Metrics endpoints
│   │   ├── thresholds.routes.ts        # Thresholds endpoints
│   │   └── index.ts                    # Route exports
│   │
│   ├── middleware/
│   │   ├── error.middleware.ts         # Error handling
│   │   └── index.ts                    # Middleware exports
│   │
│   └── utils/
│       ├── logger.ts                   # Structured logging
│       ├── errors.ts                   # Custom error classes
│       └── index.ts                    # Utility exports
│
├── dist/                               # Compiled JavaScript
├── tsconfig.json                       # TypeScript configuration
├── jest.config.js                      # Jest testing configuration
├── package.json                        # Dependencies & scripts
├── .env.example                        # Environment template
├── README.md                           # Backend documentation
├── IMPLEMENTATION_SUMMARY.md           # What was built
└── BACKEND_ARCHITECTURE.md             # This file
```

## Core Components

### 1. Express Application (`src/app.ts`)

```typescript
// Creates Express app with:
- CORS middleware for frontend communication
- JSON body parsing
- Route registration
- Error handling middleware
- Health check endpoint
```

**Endpoints**:
- `GET /health` - Health check
- `POST /api/metrics` - Store metrics
- `GET /api/metrics` - Query metrics
- `GET /api/metrics/:resourceId` - Get resource metrics
- `GET /api/thresholds` - List thresholds
- `POST /api/thresholds` - Create threshold
- `PUT /api/thresholds/:id` - Update threshold

### 2. Database Layer

**Connection** (`src/db/connection.ts`):
- Establishes MongoDB connection
- Initializes collections with schemas
- Creates indexes automatically
- Handles connection pooling

**Schemas** (`src/db/schemas.ts`):
- Metrics collection - CloudWatch metric data
- Thresholds collection - Optimization thresholds
- Approval requests collection - Approval workflow
- Approval decisions collection - Approval decisions
- Audit trail collection - Compliance audit log
- Analysis results collection - Analysis data
- Recommendations collection - Generated recommendations

**Repositories** (`src/db/repositories/`):
- `BaseRepository` - Abstract CRUD operations with lazy collection initialization
  - Uses `getCollection()` method for lazy-loaded MongoDB collection references
  - Prevents premature database connection attempts during instantiation
  - All repository methods call `getCollection()` to ensure collection is available
- `MetricsRepository` - Metric queries and storage
- `ThresholdRepository` - Threshold management
- `ApprovalRepository` - Approval lifecycle
- `AuditRepository` - Audit trail recording
- `AnalysisRepository` - Analysis results
- `RecommendationRepository` - Recommendations

### 3. Service Layer

**MetricsService** (`src/services/metrics.service.ts`):
```typescript
- storeMetric(metric) - Store single metric
- storeMetrics(metrics) - Store batch metrics
- getMetricsByResource(resourceId) - Query by resource
- getMetricsByServiceType(serviceType) - Query by service
- getMetricsByTimeRange(start, end) - Query by time
- getMetricsByResourceAndTimeRange(...) - Combined query
- validateMetric(metric) - Input validation
```

**ThresholdService** (`src/services/threshold.service.ts`):
```typescript
- getActiveThresholds(serviceType?) - Get current thresholds
- getThresholdByServiceAndMetric(...) - Get specific threshold
- createThreshold(threshold) - Create new threshold
- updateThreshold(id, updates) - Update threshold
- getThresholdHistory(...) - Get version history
- validateThreshold(threshold) - Input validation
```

### 4. API Routes

**Metrics Routes** (`src/routes/metrics.routes.ts`):
```
POST /api/metrics
  - Body: { metrics: Metric[] }
  - Response: { success, message, count }

GET /api/metrics
  - Query: resourceId, serviceType, startTime, endTime, limit, offset
  - Response: { success, count, metrics }

GET /api/metrics/:resourceId
  - Query: limit, offset
  - Response: { success, resourceId, count, metrics }
```

**Thresholds Routes** (`src/routes/thresholds.routes.ts`):
```
GET /api/thresholds
  - Query: serviceType
  - Response: { success, count, thresholds }

GET /api/thresholds/:serviceType/:metricName
  - Response: { success, threshold }

GET /api/thresholds/:serviceType/:metricName/history
  - Response: { success, count, history }

POST /api/thresholds
  - Body: { serviceType, metricName, thresholdValue, operator, timeWindow, effectiveFrom, effectiveTo }
  - Response: { success, message, threshold }

PUT /api/thresholds/:id
  - Body: { updates }
  - Response: { success, message, threshold }
```

### 5. Error Handling

**Custom Errors** (`src/utils/errors.ts`):
- `OptimizationError` - Base error (500)
- `ValidationError` - Input validation (400)
- `NotFoundError` - Resource not found (404)
- `DatabaseError` - Database operations (500)
- `MetricCollectionError` - Metric collection (500)
- `AnalysisError` - Analysis operations (500)
- `RecommendationError` - Recommendation generation (500)
- `ApprovalError` - Approval workflow (400/500)

**Error Middleware** (`src/middleware/error.middleware.ts`):
- Catches all errors
- Returns proper HTTP status codes
- Logs errors with context
- Hides sensitive info in production

### 6. Logging

**Logger** (`src/utils/logger.ts`):
```typescript
createLogger(context: string) -> Logger
- logger.debug(message, data?)
- logger.info(message, data?)
- logger.warn(message, data?)
- logger.error(message, data?)
```

Output format:
```
[2024-01-15T10:30:00.000Z] [INFO] [MetricsService] Storing metric: CPUUtilization for resource: i-1234567890abcdef0
```

### 7. Configuration

**Config** (`src/config.ts`):
```typescript
{
  mongodb: {
    uri: process.env.MONGODB_URI || 'mongodb://localhost:27017'
  },
  aws: {
    region: process.env.AWS_REGION || 'us-east-1'
  },
  optimization: {
    metricRetentionDays: 30,
    auditRetentionDays: 90,
    defaultThresholds: { ... }
  },
  notifications: {
    email: { enabled, from },
    slack: { enabled, webhookUrl }
  }
}
```

## Data Flow

### Metric Storage Flow
```
finops-bot
    ↓
POST /api/metrics
    ↓
MetricsService.storeMetrics()
    ↓
MetricsRepository.createBatch()
    ↓
MongoDB metrics collection
```

### Threshold Query Flow
```
Frontend/Bot
    ↓
GET /api/thresholds?serviceType=EC2
    ↓
ThresholdService.getActiveThresholds()
    ↓
ThresholdRepository.findByServiceType()
    ↓
MongoDB thresholds collection
    ↓
Response: { success, count, thresholds }
```

## Database Indexes

**Lazy Collection Initialization**

The `BaseRepository` class uses lazy initialization for MongoDB collections:
- Collections are not instantiated until first use via `getCollection()`
- This prevents connection errors during repository instantiation
- Improves startup time and reduces unnecessary database connections
- All repository methods call `getCollection()` to ensure collection is available

```javascript
// In BaseRepository
getCollection() {
  if (!this.collection) {
    const db = getDatabase();
    this.collection = db.collection(this.collectionName);
  }
  return this.collection;
}

// Usage in repository methods
async findById(id) {
  return await this.getCollection().findOne({ _id: new ObjectId(id) });
}
```

**Metrics Collection**:
- `{ resourceId: 1, metricName: 1, timestamp: -1 }` - Query by resource and metric
- `{ serviceType: 1, timestamp: -1 }` - Query by service
- `{ timestamp: 1 }` with TTL 30 days - Auto-delete old metrics

**Thresholds Collection**:
- `{ serviceType: 1, metricName: 1, effectiveFrom: -1 }` - Unique index for active thresholds

**Approval Requests Collection**:
- `{ status: 1, createdAt: -1 }` - Query by status
- `{ resourceId: 1 }` - Query by resource
- `{ serviceType: 1 }` - Query by service

**Audit Trail Collection**:
- `{ resourceId: 1, timestamp: -1 }` - Query by resource
- `{ actionType: 1, timestamp: -1 }` - Query by action
- `{ actorId: 1, timestamp: -1 }` - Query by actor
- `{ timestamp: 1 }` with TTL 90 days - Auto-delete old entries

## Running the Backend

### Development
```bash
npm install
npm run dev
```

### Production
```bash
npm install
npm run build
npm start
```

### Testing
```bash
npm test
npm test:watch
npm test -- --coverage
```

## Environment Setup

Create `.env` file:
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

## Integration Points

### With finops-bot (Python)
- Bot sends metrics via `POST /api/metrics`
- Bot queries thresholds via `GET /api/thresholds`

### With finops-frontend (React)
- Frontend queries metrics via `GET /api/metrics`
- Frontend manages thresholds via `GET/POST /api/thresholds`
- Frontend manages approvals via approval endpoints (to be implemented)

## Next Steps

1. **Analysis Engine** - Implement MetricAnalyzer service
2. **Recommendation Engine** - Implement RecommendationEngine service
3. **Approval Workflows** - Implement ApprovalManager service
4. **Audit Trail** - Implement AuditTrailManager service
5. **Notifications** - Implement NotificationService
6. **Bot Integration** - Extend finops-bot with multi-metric collectors
7. **Frontend Integration** - Create React components for approval dashboard

## Key Features

✅ Clean architecture with separation of concerns
✅ Repository pattern for data access
✅ Service layer for business logic
✅ TypeScript strict mode for type safety
✅ Centralized error handling
✅ Structured logging
✅ MongoDB with automatic schema validation
✅ Express REST API with proper HTTP status codes
✅ Input validation and error responses
✅ Unit tests with Jest
✅ Environment configuration management
✅ CORS support for frontend
✅ Health check endpoint
✅ Automatic database initialization
