# 🚀 AWS FinOps Automation Platform

An end-to-end **AWS FinOps automation system** that detects underutilized EC2 instances using CloudWatch metrics, automatically stops wasteful resources, calculates real cost savings, and visualizes optimization insights through a modern dashboard.

This project demonstrates real-world **cloud cost optimization**, combining AWS automation, backend APIs, and a data-driven frontend UI.

---

## ✨ Key Features

- 🔍 Automatically discovers EC2 instances, RDS databases, Load Balancers, Auto Scaling Groups, and EBS volumes across regions  
- 📉 Monitors multi-dimensional metrics: CPU utilization, network I/O, memory, request volume, and capacity  
- 🛑 Auto-stops underutilized resources via a FinOps rules engine  
- 💰 Calculates real-time cost savings based on resource type, instance family, and runtime  
- 📊 Interactive dashboard with charts and optimization history  
- 🔗 Direct links to AWS Console for each resource  
- 🔄 Real-time data refresh from backend APIs  
- ✅ Approval workflows for safe resource optimization  
- 📋 Complete audit trails for compliance and accountability  
- 🌍 Multi-region cost analysis with regional pricing variations  

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│              Approval Dashboard, Metrics Visualization           │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    API Layer (Express)                           │
│  /api/approval-requests, /api/metrics, /api/audit-trail         │
│  /api/thresholds (existing endpoints maintained)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   Business Logic Layer                           │
│  Metric Analysis, Recommendations, Approvals, Audit Trail       │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                   Metric Collection Layer                        │
│                    (finops-bot - Python)                         │
│  EC2, RDS, Lambda, ECS, ElastiCache, S3, DynamoDB Collectors   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    CloudWatch API                                │
└────────────────────────────────────────────────────────────────┘
```

### Components

#### 1. FinOps Bot (Python) - Metric Collection & Cost Calculation
**Responsibility**: Discover AWS resources, collect metrics from CloudWatch, calculate costs, and send data to finops-backend

- Uses `boto3` to:
  - Discover EC2 instances, RDS databases, Load Balancers, Auto Scaling Groups, and EBS volumes across all AWS regions
  - Fetch CloudWatch metrics (CPU, network I/O, memory, request volume, capacity, disk I/O)
  - Send metrics to finops-backend via REST API (`POST /api/metrics`)
  - Calculate estimated cost savings using regional pricing data
- Supports multi-region scanning with graceful error handling
- **AWS Service Collectors** (in development):
  - EC2 instance discovery and CPU metric collection
  - RDS database discovery with engine and storage details
  - RDS metrics (CPU, connections, latency, storage)
  - Load Balancer discovery and metrics
  - Auto Scaling Group discovery and metrics
  - EBS volume discovery and metrics
  - DynamoDB, Lambda, ElastiCache, S3 collectors (planned)
- **Pricing Module** (`utils/pricing.py`):
  - Regional pricing support: us-east-1, us-west-2, eu-west-1
  - EC2 instance families: t2, t3, m5, c5 with multiple sizes
  - RDS instance classes: t2, t3, m5, r5 with storage pricing (gp2, gp3, io1, io2)
  - Load Balancer pricing: Application, Network, Classic types
  - EBS volume pricing: gp2, gp3, io1, io2, st1, sc1 types
  - Data processing and new connections rates for load balancers
  - Helper functions for cost calculations (hourly, daily, monthly, annual)
- **Rules Engine** (`core/rules_engine.py`):
  - Configurable thresholds for waste detection (replaces hardcoded CPU < 0 logic)
  - Multi-metric evaluation functions for EC2, RDS, Load Balancers, EBS, ASGs
- **Costing Data Submission**:
  - Sends current costing summary (`POST /api/costing/current`)
  - Sends regional cost breakdown (`POST /api/costing/by-region`)
  - Sends service-level cost breakdown (`POST /api/costing/by-service`)
  - Includes underutilization analysis and optimization recommendations

#### 2. Backend API (Node.js + Express + MongoDB) - Analysis, Approvals & Persistence
**Responsibility**: Receive metrics and costing data, perform analysis, manage approvals, maintain audit trails, and expose REST APIs

- Exposes REST APIs for:
  - EC2 instances (`POST /api/instances`, `GET /api/instances`, `GET /api/instances/:instanceId`)
  - Metrics collection and analysis (`POST /api/metrics`, `GET /api/metrics/:resourceId`)
  - Optimization recommendations (generated internally)
  - Approval workflows and decisions (`GET/POST /api/approval-requests`)
  - Audit trail and compliance reporting (`GET /api/audit-trail`)
  - Threshold management (`GET/POST /api/thresholds`)
  - Costing data retrieval (`GET /api/costing/current`, `/by-region`, `/by-service`)
- Implements multi-metric analysis engine
- Manages approval workflows before resource termination
- Maintains complete audit trails for all actions
- **Key Managers** (in development):
  - `MetricAnalyzer` - Evaluates metrics against thresholds
  - `RecommendationEngine` - Generates optimization recommendations
  - `ApprovalManager` - Manages approval requests and decisions
  - `AuditTrailManager` - Records all actions for compliance
  - `NotificationService` - Sends notifications via email, Slack, webhooks
  - `ThresholdManager` - Manages configurable optimization thresholds

### Backend API Endpoints

#### Costing Endpoints

**POST /api/costing/current** - Send current total costing summary
```json
Request:
{
  "total_monthly_cost": 1234.56,
  "total_daily_cost": 41.15,
  "total_annual_cost": 14814.72,
  "timestamp": "2026-02-10T12:25:50.274Z",
  "region_count": 3,
  "service_breakdown": {
    "ec2": 800.00,
    "load_balancers": 200.00,
    "ebs_volumes": 234.56
  }
}

Response (200):
{
  "status": "success",
  "data": {
    "summary": {
      "totalMonthlyCost": 1234.56,
      "totalDailyCost": 41.15,
      "totalAnnualCost": 14814.72
    },
    "breakdown": {
      "ec2Instances": { "cost": 800.00, "count": 5, "percentage": 64.8 },
      "loadBalancers": { "cost": 200.00, "count": 2, "percentage": 16.2 },
      "ebsVolumes": { "cost": 234.56, "count": 10, "percentage": 19.0 }
    },
    "timestamp": "2026-02-10T12:25:50.274Z"
  }
}
```

**GET /api/costing/current** - Retrieve current total costing summary
```json
Response (200):
{
  "status": "success",
  "data": {
    "summary": {
      "totalMonthlyCost": 1234.56,
      "totalDailyCost": 41.15,
      "totalAnnualCost": 14814.72
    },
    "breakdown": { ... }
  }
}
```

**POST /api/costing/by-region** - Send regional cost breakdown
```json
Request:
{
  "regions": [
    {
      "region": "us-east-1",
      "monthly": 600.00,
      "ec2": 400.00,
      "lb": 100.00,
      "ebs": 100.00
    }
  ],
  "total_monthly": 1234.56,
  "timestamp": "2026-02-10T12:25:50.274Z"
}

Response (200):
{
  "status": "success",
  "data": {
    "us-east-1": {
      "ec2": 400.00,
      "loadBalancers": 100.00,
      "asg": 0.00,
      "ebs": 100.00,
      "rds": 0.00,
      "total": 600.00
    }
  }
}
```

**GET /api/costing/by-region** - Retrieve regional cost breakdown
```json
Response (200):
{
  "status": "success",
  "data": {
    "us-east-1": { "ec2": 400.00, "loadBalancers": 100.00, ... },
    "us-west-2": { "ec2": 300.00, "loadBalancers": 50.00, ... }
  }
}
```

**POST /api/costing/by-service** - Send service-level cost breakdown
```json
Request:
{
  "services": {
    "ec2": 800.00,
    "load_balancers": 200.00,
    "ebs_volumes": 234.56
  },
  "total_monthly": 1234.56,
  "timestamp": "2026-02-10T12:25:50.274Z",
  "service_percentages": {
    "ec2": 64.8,
    "load_balancers": 16.2,
    "ebs_volumes": 19.0
  }
}

Response (200):
{
  "status": "success",
  "data": {
    "EC2 Instances": { "monthlyCost": 800.00, "count": 5, "percentage": 64.8 },
    "Load Balancers": { "monthlyCost": 200.00, "count": 2, "percentage": 16.2 },
    "EBS Volumes": { "monthlyCost": 234.56, "count": 10, "percentage": 19.0 }
  }
}
```

**GET /api/costing/by-service** - Retrieve service-level cost breakdown
```json
Response (200):
{
  "status": "success",
  "data": {
    "EC2 Instances": { "monthlyCost": 800.00, "count": 5, "percentage": 64.8 },
    "Load Balancers": { "monthlyCost": 200.00, "count": 2, "percentage": 16.2 },
    "EBS Volumes": { "monthlyCost": 234.56, "count": 10, "percentage": 19.0 }
  },
  "totalMonthlyCost": 1234.56
}
```

#### EC2 Instances

**POST /api/instances** - Save EC2 instance data
```json
Request:
{
  "instance_id": "i-1234567890abcdef0",
  "state": "running",
  "region": "us-east-1",
  "cpu": 2.5,
  "instance_type": "t2.medium",
  "hourly_cost": 0.0464,
  "monthly_cost": 33.41,
  "annual_cost": 400.92
}

Response (201):
{
  "status": "success",
  "message": "Instance data saved",
  "data": {
    "instance_id": "i-1234567890abcdef0",
    "region": "us-east-1",
    "instance_type": "t2.medium"
  }
}
```

**GET /api/instances** - Retrieve all EC2 instances
```json
Response (200):
{
  "status": "success",
  "data": [
    {
      "instance_id": "i-1234567890abcdef0",
      "state": "running",
      "region": "us-east-1",
      "cpu": 2.5,
      "instance_type": "t2.medium",
      "hourly_cost": 0.0464,
      "monthly_cost": 33.41,
      "annual_cost": 400.92
    }
  ],
  "total": 1
}
```

**GET /api/instances/:instanceId** - Retrieve specific EC2 instance
```json
Response (200):
{
  "status": "success",
  "data": {
    "instance_id": "i-1234567890abcdef0",
    "state": "running",
    "region": "us-east-1",
    "cpu": 2.5,
    "instance_type": "t2.medium",
    "hourly_cost": 0.0464,
    "monthly_cost": 33.41,
    "annual_cost": 400.92
  }
}
```

#### 3. Frontend Dashboard (React) - User Interface & Visualization
**Responsibility**: Display metrics, recommendations, approval workflows, and cost analysis

**Architecture**:
- **App.js** - Root component with navigation state management
  - Manages page navigation between Dashboard and ResourceDetail views
  - Handles resource selection and detail view transitions
  - Maintains selected resource state for detail view
- **Dashboard.js** - Main dashboard component
  - Displays cost savings over time
  - Shows optimization actions and recommendations
  - Lists pending approval requests
  - Displays audit trail and compliance reports
  - Provides navigation to resource details via `onViewDetails` callback
- **ResourceDetail.js** - Resource detail view component
  - Displays detailed metrics for selected resource
  - Shows resource-specific optimization recommendations
  - Provides navigation back to dashboard via `onBack` callback

**Features**:
- Cost savings visualization over time
- Optimization actions and recommendations
- Pending approval requests management
- Audit trail and compliance reports
- Resource details and metrics
- Built with Recharts for interactive visualizations
- Real-time updates via WebSocket for approval notifications
- Multi-page navigation between Dashboard and Resource Details

**Navigation Pattern**:
```javascript
// In App.js
const [currentPage, setCurrentPage] = useState("dashboard");
const [selectedResource, setSelectedResource] = useState(null);

// Navigate to resource details
const handleViewDetails = (resourceId, resourceType) => {
  setSelectedResource({ id: resourceId, type: resourceType });
  setCurrentPage("detail");
};

// Navigate back to dashboard
const handleBackToDashboard = () => {
  setCurrentPage("dashboard");
  setSelectedResource(null);
};
```

**Frontend API Functions** (`src/data.js`):
- `fetchSavingsData()` - Retrieve savings records from backend
- `fetchCostingData()` - Get current total costing summary
- `fetchCostingByRegion()` - Get regional cost breakdown
- `fetchCostingByService()` - Get service-level cost breakdown
- `fetchResizeOptions(instanceId)` - Get available resize options for an EC2 instance

---

## 💰 Costing Data Flow

The finops-bot now sends comprehensive costing data to the backend after calculating infrastructure costs:

### Bot Costing Calculation Process

1. **Resource Discovery**: Bot discovers EC2 instances, RDS databases, Load Balancers, Auto Scaling Groups, and EBS volumes
2. **Metric Collection**: Bot collects CloudWatch metrics for each resource (CPU, network I/O, connections, storage, etc.)
3. **Cost Calculation**: For each resource, bot calculates hourly, monthly, and annual costs using regional pricing
4. **Underutilization Analysis**: Bot identifies underutilized resources based on metric thresholds
5. **Aggregation**: Bot aggregates costs by region and service type
6. **Backend Submission**: Bot sends three types of costing summaries to backend:
   - **Current Costing**: Total monthly/daily/annual costs with service breakdown
   - **Regional Breakdown**: Costs aggregated by AWS region with service-level detail
   - **Service Breakdown**: Costs aggregated by service type with percentages

### Costing Data Sent to Backend

**Current Costing Summary** (`POST /api/costing/current`)
```json
{
  "total_monthly_cost": 1234.56,
  "total_daily_cost": 41.15,
  "total_annual_cost": 14814.72,
  "timestamp": "2026-02-10T12:25:50.274Z",
  "region_count": 3,
  "service_breakdown": {
    "ec2": 800.00,
    "load_balancers": 200.00,
    "ebs_volumes": 234.56
  }
}
```

**Regional Cost Breakdown** (`POST /api/costing/by-region`)
- Costs per region with service-level detail (EC2, Load Balancers, EBS, RDS, ASGs)
- Total regional costs
- Sorted by highest cost first

**Service Cost Breakdown** (`POST /api/costing/by-service`)
- Costs per service type
- Percentage of total cost per service
- Resource count per service

### Example Bot Output

```
================================================================================
💰 COST SUMMARY & REPORTING
================================================================================

💰 TOTAL INFRASTRUCTURE COSTS:
  💰 Monthly: $1,234.56
  💰 Daily:   $41.15
  💰 Annual:  $14,814.72

================================================================================
📍 COST BREAKDOWN BY REGION
================================================================================

🌍 us-east-1:
   EC2 Instances:  $600.00/month
   Load Balancers: $100.00/month
   EBS Volumes:    $100.00/month
   ─────────────────────────────
   Total:          $800.00/month

🌍 us-west-2:
   EC2 Instances:  $300.00/month
   Load Balancers: $50.00/month
   EBS Volumes:    $84.56/month
   ─────────────────────────────
   Total:          $434.56/month

================================================================================
📤 SENDING COSTING DATA TO BACKEND
================================================================================

✅ Current costing data saved
✅ Regional costing data saved
✅ Service costing data saved

================================================================================
✅ AWS FinOps Bot Execution Complete
================================================================================
```

### Backend Costing Endpoints

The backend provides three endpoints to retrieve costing data:

- `GET /api/costing/current` - Current total costs with service breakdown
- `GET /api/costing/by-region` - Regional cost breakdown with service detail
- `GET /api/costing/by-service` - Service-level cost breakdown with percentages

These endpoints are used by the frontend dashboard to visualize cost trends and optimization opportunities.

### Bot Workflow Phases

The bot executes in the following phases:

1. **Resize & Recommendations Phase**: Identifies optimization opportunities
2. **Savings & Cost Tracking Phase**: Processes EC2 instances and calculates savings
3. **Resource Management Phase**: Processes Load Balancers, Auto Scaling Groups, EBS volumes, and RDS instances
4. **Cost Summary & Reporting**: Aggregates costs by region and service
5. **Backend Submission**: Sends all costing data to backend APIs

## 🧰 Tech Stack

**Cloud**
- AWS EC2
- AWS CloudWatch
- AWS IAM

**Automation**
- Python 3.x
- boto3 (v1.42.30)

**Backend**
- Node.js with Express.js (v5.2.1)
- MongoDB (v6.3.0) with Mongoose ODM (v9.1.4)
- AWS SDK v2 (v2.1500.0)

**Frontend**
- React (v19.2.3)
- Recharts (v3.6.0)
- Axios (v1.13.2)

**Infrastructure as Code (Optional)**
- Terraform

**Security**
- AWS credentials managed via AWS CLI  
- No credentials stored in the repository

---

## 🚀 Quick Start

### Backend Setup
```bash
cd finops-backend

# Install dependencies
npm install

# Start server (runs on port 5000)
npm start

# Development mode
npm run dev

# Run tests
npm test
```

### Bot Setup

#### Option 1: Real AWS Data (Requires AWS Credentials)
```bash
cd finops-bot

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure

# Run bot with real AWS data
python main.py
```

#### Option 2: Mock Data (No AWS Credentials Required)
```bash
cd finops-bot

# Install dependencies
pip install -r requirements.txt

# Run bot with mock data (great for testing and demos)
python main_mock.py
```

**Bot Output**:
The bot generates comprehensive cost reports including:
- Total infrastructure costs (monthly, daily, annual)
- Cost breakdown by region (sorted by highest cost first)
- Cost breakdown by service (EC2, RDS, Load Balancers, EBS, etc.)
- Resource utilization analysis with optimization recommendations
- Estimated savings from optimization actions

**Mock Bot Features** (`main_mock.py`):
- Demonstrates bot functionality without requiring AWS credentials
- Includes mock data for:
  - 4 EC2 instances across 3 regions
  - 2 Load Balancers
  - 2 Auto Scaling Groups
  - 2 EBS volumes
  - 2 RDS instances
- Sends all data to backend via REST API (same as real bot)
- Perfect for development, testing, and learning

### Frontend Setup
```bash
cd finops-frontend

# Install dependencies
npm install

# Start development server (runs on port 3000)
npm start

# Build for production
npm run build

# Run tests
npm test
```

**Development Setup Notes**:
- The frontend uses `setupProxy.js` to proxy API requests to the backend during development
- All `/api/*` requests are automatically forwarded to `http://localhost:5000`
- Ensure the backend server is running on port 5000 before starting the frontend
- No need to configure CORS headers for development - the proxy handles this transparently

---

## 🚀 Development Workflow

To run the complete finops system locally for development:

### Terminal 1: Start the Backend
```bash
cd finops-backend
npm install
npm start
# Backend runs on http://localhost:5000
```

### Terminal 2: Start the Frontend
```bash
cd finops-frontend
npm install
npm start
# Frontend runs on http://localhost:3000
# API requests are automatically proxied to http://localhost:5000
```

### Terminal 3: Run the Bot (Optional)
```bash
cd finops-bot
pip install -r requirements.txt

# Option A: Real AWS data (requires AWS credentials)
python main.py

# Option B: Mock data (no AWS credentials needed)
python main_mock.py
```

**Development Notes**:
- The frontend's `setupProxy.js` automatically proxies `/api/*` requests to the backend
- No CORS configuration needed during development
- Backend must be running before starting the frontend
- Bot can be run independently to send data to the backend APIs

---

1. FinOps Bot scans EC2 instances, RDS databases, Load Balancers, Auto Scaling Groups, and EBS volumes across configured regions  
2. CloudWatch metrics are collected and sent to finops-backend via REST API
3. Backend analyzes metrics against configurable thresholds (replacing hardcoded CPU < 0 logic)
4. Underutilized resources are identified using multi-metric analysis (CPU, network I/O, connections, request volume, etc.)
5. Recommendations are generated with cost savings estimates and confidence levels
6. Approval requests are created and require manager review before execution  
7. Backend stores metrics, recommendations, approvals, and audit trails in MongoDB
8. Frontend dashboard visualizes savings, optimization history, and pending approvals  
9. Approved actions are executed with full audit trail recording
10. Bot generates comprehensive cost reports sorted by region and service for easy analysis
11. Bot sends costing summaries to backend via REST API for dashboard visualization:
    - Current total costs (monthly, daily, annual)
    - Regional cost breakdown
    - Service-level cost breakdown with percentages

---

## Frontend Component Structure

The finops-frontend is organized with a component-based architecture:

```
finops-frontend/src/
├── App.js                   # Root component with navigation state
├── Dashboard.js             # Main dashboard view
├── ResourceDetail.js        # Resource detail view (new)
├── data.js                  # API data fetching functions
├── App.css                  # Global styles
└── index.css                # Base styles
```

### Component Hierarchy

```
App (Navigation & State Management)
├── Dashboard (Main View)
│   ├── Cost Summary Cards
│   ├── Charts & Visualizations
│   ├── Resource Tables
│   └── Approval Requests List
└── ResourceDetail (Detail View)
    ├── Resource Metrics
    ├── Optimization Recommendations
    ├── Resize Options
    └── Back to Dashboard Button
```

### Key Components

**App.js** - Root component managing navigation
- Maintains `currentPage` state ("dashboard" or "detail")
- Maintains `selectedResource` state for detail view
- Provides navigation callbacks to child components
- Renders either Dashboard or ResourceDetail based on current page

**Dashboard.js** - Main dashboard view
- Displays KPI cards with cost summaries
- Shows charts for cost trends and breakdowns
- Lists resources with optimization opportunities
- Provides "View Details" buttons that trigger navigation
- Calls `onViewDetails(resourceId, resourceType)` callback

**ResourceDetail.js** - Resource detail view (new)
- Displays detailed metrics for selected resource
- Shows resource-specific optimization recommendations
- Lists available resize options
- Provides "Back to Dashboard" button
- Calls `onBack()` callback to return to dashboard

---

## Frontend API Functions

The frontend communicates with the backend through a set of data fetching functions defined in `finops-frontend/src/data.js`. These functions handle API calls with error handling and provide data to React components.

### Available Functions

#### `fetchSavingsData()`
Retrieves all savings records from the backend.

```javascript
import { fetchSavingsData } from './data.js';

const savingsData = await fetchSavingsData();
// Returns: Array of savings records
// Example: [
//   {
//     resource_id: 'i-1234567890abcdef0',
//     cloud: 'AWS',
//     money_saved: 33.41,
//     region: 'us-east-1',
//     state: 'stopped',
//     instance_type: 't2.large',
//     pricing_model: 'on-demand',
//     estimated_hours_saved: 1,
//     date: '2026-02-10T12:25:50.274Z'
//   },
//   ...
// ]
```

**Backend Response Structure**:
```json
{
  "status": "success",
  "data": [...],
  "total": 5,
  "totalSavings": 250.50
}
```

The frontend function extracts the `data` array automatically, returning just the savings records array.

#### `fetchCostingData()`
Retrieves current total costing summary across all resources.

```javascript
import { fetchCostingData } from './data.js';

const costingData = await fetchCostingData();
// Returns: {
//   status: 'success',
//   data: {
//     summary: { totalMonthlyCost, totalDailyCost, totalAnnualCost },
//     breakdown: { ec2Instances, loadBalancers, ebsVolumes, rdsInstances, ... }
//   }
// }
```

#### `fetchCostingByRegion()`
Retrieves cost breakdown aggregated by AWS region.

```javascript
import { fetchCostingByRegion } from './data.js';

const regionCosts = await fetchCostingByRegion();
// Returns: {
//   status: 'success',
//   data: {
//     'us-east-1': { ec2: $, loadBalancers: $, ebs: $, rds: $, total: $ },
//     'us-west-2': { ec2: $, loadBalancers: $, ebs: $, rds: $, total: $ },
//     ...
//   }
// }
```

#### `fetchCostingByService()`
Retrieves cost breakdown aggregated by service type (EC2, RDS, Load Balancers, etc.).

```javascript
import { fetchCostingByService } from './data.js';

const serviceCosts = await fetchCostingByService();
// Returns: {
//   status: 'success',
//   data: {
//     'EC2 Instances': { monthlyCost: $, count: N, percentage: % },
//     'Load Balancers': { monthlyCost: $, count: N, percentage: % },
//     'EBS Volumes': { monthlyCost: $, count: N, percentage: % },
//     'RDS Instances': { monthlyCost: $, count: N, percentage: % },
//     ...
//   },
//   totalMonthlyCost: $
// }
```

#### `fetchResizeOptions(instanceId)`
Retrieves available resize options for a specific EC2 instance.

```javascript
import { fetchResizeOptions } from './data.js';

const options = await fetchResizeOptions('i-1234567890abcdef0');
// Returns: {
//   status: 'success',
//   data: {
//     instance_id: 'i-1234567890abcdef0',
//     current_instance_type: 't2.large',
//     current_monthly_cost: 66.82,
//     current_annual_cost: 801.84,
//     resize_available: true,
//     resize_options: [
//       {
//         target_instance_type: 't2.medium',
//         current_monthly_cost: 66.82,
//         target_monthly_cost: 46.77,
//         estimated_monthly_savings: 20.05,
//         estimated_annual_savings: 240.55,
//         savings_percentage: 30,
//         downtime_estimate: '2-5 minutes'
//       },
//       ...
//     ],
//     total_options: 3
//   }
// }
```

### Error Handling

All functions include built-in error handling:
- Errors are logged to the browser console with a ❌ prefix
- Functions return sensible defaults on error:
  - `fetchCostingData()` returns `null`
  - `fetchCostingByRegion()` returns `[]`
  - `fetchCostingByService()` returns `null`
  - `fetchResizeOptions()` returns `[]`
  - `fetchSavingsData()` returns `[]`

### API Response Structure

The backend uses a consistent response structure for all endpoints:

**Success Response**:
```json
{
  "status": "success",
  "data": { /* actual data */ },
  "total": 5,
  "totalSavings": 250.50
}
```

**Error Response**:
```json
{
  "error": "Error message",
  "message": "Detailed error description"
}
```

**Frontend Data Functions**:
- `fetchSavingsData()` - Extracts `data` array from response
- `fetchCostingData()` - Returns full response object
- `fetchCostingByRegion()` - Returns full response object
- `fetchCostingByService()` - Returns full response object
- `fetchResizeOptions()` - Returns full response object

### Usage in Components

Example usage in a React component:

```javascript
import { useEffect, useState } from 'react';
import { fetchCostingData, fetchCostingByService } from './data.js';

function CostingDashboard() {
  const [totalCost, setTotalCost] = useState(null);
  const [serviceCosts, setServiceCosts] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      const costData = await fetchCostingData();
      const serviceData = await fetchCostingByService();
      
      if (costData) setTotalCost(costData.data.summary);
      if (serviceData) setServiceCosts(serviceData.data);
    };

    loadData();
  }, []);

  return (
    <div>
      {totalCost && (
        <div>
          <h2>Total Monthly Cost: ${totalCost.totalMonthlyCost}</h2>
          <p>Daily: ${totalCost.totalDailyCost}</p>
          <p>Annual: ${totalCost.totalAnnualCost}</p>
        </div>
      )}
      {serviceCosts && (
        <div>
          {Object.entries(serviceCosts).map(([service, data]) => (
            <div key={service}>
              <h3>{service}</h3>
              <p>Cost: ${data.monthlyCost}/month ({data.percentage}%)</p>
              <p>Count: {data.count}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default CostingDashboard;
```

---



**finops-bot (Python)** - Metric Collection & Cost Calculation Layer
- Discovers AWS resources via boto3
- Collects metrics from CloudWatch
- Calculates costs using regional pricing data
- Sends metrics and costing data to backend via REST API
- Does NOT make optimization decisions or manage approvals
- Does NOT store data (backend handles persistence)

**finops-backend (Node.js)** - Analysis & Approval Layer
- Receives metrics and costing data from bot
- Analyzes metrics against thresholds
- Generates recommendations
- Manages approval workflows
- Records audit trails
- Exposes REST APIs for frontend
- Persists all data in MongoDB

**finops-frontend (React)** - User Interface Layer
- Displays metrics and recommendations
- Manages approval workflows
- Shows audit trails and compliance reports
- Visualizes cost breakdowns and trends
- Communicates with backend APIs only

---

## 💰 Pricing Module

The `finops-bot/utils/pricing.py` module provides comprehensive pricing calculations for AWS resources:

### Supported Services & Pricing Data

**EC2 Instances**
- Instance families: t2, t3, m5, c5, g4dn (GPU - NVIDIA T4), g5 (GPU - NVIDIA A10G), g6 (GPU - NVIDIA L4)
- Sizes: micro, small, medium, large, xlarge, 2xlarge (and GPU-specific sizes)
- Regions: us-east-1, us-west-2, eu-west-1
- On-demand hourly rates with regional variations
- GPU instance pricing for ML/AI workloads

**RDS Instances**
- Instance classes: t2, t3, m5, r5
- Engines: MySQL, PostgreSQL, MariaDB, Oracle, SQL Server
- Storage types: gp2, gp3, io1, io2
- Multi-AZ support with pricing adjustments
- Backup retention and read replica tracking

**Load Balancers**
- Types: Application (ALB), Network (NLB), Classic (ELB)
- Hourly base costs
- Data processing rates (per GB)
- New connections rates (per million)

**EBS Volumes**
- Volume types: gp2, gp3, io1, io2, st1, sc1
- Pricing per GB-month with regional variations
- Support for IOPS and throughput pricing (io1, io2, gp3)

**Auto Scaling Groups**
- Aggregated pricing from constituent EC2 instances
- Per-instance cost tracking

### Available Functions

```python
# EC2 pricing
calculate_savings(instance_type, hours_saved=1, region="us-east-1")
get_instance_hourly_cost(instance_type, region="us-east-1")

# RDS pricing
get_rds_instance_hourly_cost(db_instance_class, region="us-east-1")
get_rds_storage_monthly_cost(storage_type, allocated_storage_gb, region="us-east-1")
get_rds_total_cost(db_instance_class, storage_type, allocated_storage_gb, region="us-east-1", multi_az=False)

# Load Balancer pricing
get_load_balancer_hourly_cost(lb_type, region="us-east-1")

# EBS volume pricing
get_ebs_volume_monthly_cost(volume_type, size_gb, region="us-east-1")

# Rate lookups
get_data_processing_rate(region="us-east-1")
get_new_connections_rate(region="us-east-1")

# Cost conversions
calculate_monthly_cost(hourly_cost)
calculate_annual_cost(hourly_cost)
```

## EC2 Instance Management

The `finops-bot/aws/stop_ec2.py` module provides functions to manage EC2 instances based on optimization recommendations:

### Available Functions

```python
# Stop an EC2 instance
stop_instance(instance_id, region, require_approval=True, approval_request_id=None)
# Returns: {"status": "success|already_stopped|approval_required|not_approved", "message": "...", "instance_id": "..."}

# Resize an EC2 instance to a different instance type
resize_instance(instance_id, region, new_instance_type, require_approval=True, approval_request_id=None)
# Returns: {"status": "success|invalid_state|not_found|approval_required|not_approved", "message": "...", "instance_id": "...", "new_instance_type": "..."}

# Alias for resize_instance (backward compatibility)
change_instance_type(instance_id, region, new_instance_type, require_approval=True, approval_request_id=None)
```

### Example Usage

```python
from aws.stop_ec2 import stop_instance, resize_instance

# Stop an underutilized EC2 instance (requires approval)
result = stop_instance("i-1234567890abcdef0", "us-east-1")
if result["status"] == "success":
    print(f"EC2 instance stopped: {result['message']}")

# Resize an EC2 instance to a smaller type (requires approval)
result = resize_instance("i-1234567890abcdef0", "us-east-1", "t2.small",
                        require_approval=True,
                        approval_request_id="approval-456")
if result["status"] == "success":
    print(f"EC2 instance resized to {result['new_instance_type']}")
```

### Resize Operation Details

The `resize_instance()` function performs the following steps:
1. Stops the EC2 instance (required for instance type changes)
2. Waits for the instance to reach stopped state
3. Modifies the instance type to the new type
4. Restarts the instance
5. Returns status with the new instance type

**Note**: Resizing causes brief downtime during the stop/restart cycle.

### Error Handling

All EC2 management functions handle common error scenarios:
- **IncorrectInstanceState**: Instance is already stopped or in an invalid state for the operation
- **InvalidInstanceID.NotFound**: Instance does not exist in the specified region
- **ApprovalRequired**: Approval request must be created and approved before executing action
- **NotApproved**: Approval request exists but has not been approved yet
- **Other errors**: Logged and re-raised for caller handling

The functions return structured responses with status codes and messages for integration with approval workflows and audit trails.

## RDS Instance Management

The `finops-bot/aws/stop_rds.py` module provides functions to manage RDS instances based on optimization recommendations:

### Available Functions

```python
# Stop an RDS instance
stop_rds_instance(db_instance_id, region, require_approval=True, approval_request_id=None)
# Returns: {"status": "success|already_stopped|not_found|approval_required", "message": "...", "db_instance_id": "..."}

# Delete an RDS instance (for severely underutilized resources)
delete_rds_instance(db_instance_id, region, skip_final_snapshot=False, require_approval=True, approval_request_id=None)
# Returns: {"status": "success|invalid_state|not_found|approval_required", "message": "...", "db_instance_id": "..."}

# Downsize an RDS instance to a smaller instance class
modify_rds_instance(db_instance_id, region, db_instance_class, require_approval=True, approval_request_id=None)
# Returns: {"status": "success|invalid_state|not_found|approval_required", "message": "...", "db_instance_id": "...", "new_instance_class": "..."}
```

### Example Usage

```python
from aws.stop_ec2 import stop_instance, terminate_instance

# Stop an underutilized EC2 instance (requires approval)
result = stop_instance("i-1234567890abcdef0", "us-east-1")
if result["status"] == "success":
    print(f"EC2 instance stopped: {result['message']}")

# Terminate an EC2 instance after approval
result = terminate_instance("i-1234567890abcdef0", "us-east-1", 
                           require_approval=True, 
                           approval_request_id="approval-123")
if result["status"] == "success":
    print(f"EC2 instance terminated: {result['message']}")
```

### Error Handling

All EC2 management functions handle common error scenarios:
- **IncorrectInstanceState**: Instance is already stopped/terminated or in an invalid state
- **ApprovalRequired**: Approval request must be created and approved before executing action
- **NotApproved**: Approval request exists but has not been approved yet
- **Other errors**: Logged and re-raised for caller handling

The functions return structured responses with status codes and messages for integration with approval workflows and audit trails.

## RDS Instance Management

The `finops-bot/aws/stop_rds.py` module provides functions to manage RDS instances based on optimization recommendations:

### Available Functions

```python
# Stop an RDS instance
stop_rds_instance(db_instance_id, region, require_approval=True, approval_request_id=None)
# Returns: {"status": "success|already_stopped|not_found|approval_required", "message": "...", "db_instance_id": "..."}

# Delete an RDS instance (for severely underutilized resources)
delete_rds_instance(db_instance_id, region, skip_final_snapshot=False, require_approval=True, approval_request_id=None)
# Returns: {"status": "success|invalid_state|not_found|approval_required", "message": "...", "db_instance_id": "..."}

# Downsize an RDS instance to a smaller instance class
modify_rds_instance(db_instance_id, region, db_instance_class, require_approval=True, approval_request_id=None)
# Returns: {"status": "success|invalid_state|not_found|approval_required", "message": "...", "db_instance_id": "...", "new_instance_class": "..."}
```

### Example Usage

```python
from aws.stop_rds import stop_rds_instance, modify_rds_instance

# Stop an underutilized RDS instance (requires approval)
result = stop_rds_instance("mydb-instance", "us-east-1")
if result["status"] == "success":
    print(f"RDS instance stopped: {result['message']}")

# Downsize an RDS instance to reduce costs (requires approval)
result = modify_rds_instance("mydb-instance", "us-east-1", "db.t3.small")
if result["status"] == "success":
    print(f"RDS instance downsized: {result['message']}")

# Execute action after approval
result = stop_rds_instance("mydb-instance", "us-east-1", 
                          require_approval=True, 
                          approval_request_id="approval-123")
```

### Error Handling

All RDS management functions handle common error scenarios:
- **InvalidDBInstanceState**: Instance is already stopped or in an invalid state for the operation
- **DBInstanceNotFound**: Instance does not exist in the specified region
- **ApprovalRequired**: Approval request must be created and approved before executing action
- **NotApproved**: Approval request exists but has not been approved yet
- **Other errors**: Logged and re-raised for caller handling

The functions return structured responses with status codes and messages for integration with approval workflows and audit trails.

## Recommendation Engine

The `finops-bot/core/recommendation_engine.py` module provides intelligent optimization recommendations for RDS and EC2 instances:

### RDS Recommendations

```python
from core.recommendation_engine import RDSRecommendation

# Analyze RDS metrics and generate recommendations
recommendation = RDSRecommendation.analyze_rds_metrics(
    db_instance_id="mydb-instance",
    db_instance_class="db.t3.large",
    storage_type="gp2",
    allocated_storage_gb=100,
    region="us-east-1",
    cpu=2.5,
    connections=3,
    multi_az=False
)

# Format recommendation as human-readable text
text = RDSRecommendation.format_recommendation(recommendation)
print(text)
```

### EC2 Recommendations

```python
from core.recommendation_engine import EC2Recommendation

# Analyze EC2 metrics and generate recommendations
recommendation = EC2Recommendation.analyze_ec2_metrics(
    instance_id="i-1234567890abcdef0",
    instance_type="t2.large",
    region="us-east-1",
    cpu=3.5,
    network_in_bytes=500,
    network_out_bytes=300
)

# Access recommendation details
print(f"Action: {recommendation['action']}")
print(f"Confidence: {recommendation['confidence']}%")
print(f"Monthly Savings: ${recommendation['estimated_monthly_savings']:.2f}")
```

### Recommendation Structure

Each recommendation includes:
- **action**: Recommended action (delete, resize, stop, monitor, none)
- **confidence**: Confidence level (0-100) based on metric consistency
- **reasoning**: Explanation of why the resource is flagged
- **estimated_monthly_savings**: Projected monthly cost savings
- **estimated_annual_savings**: Projected annual cost savings
- **risk_level**: Risk assessment (low, medium, high, none)
- **risk_description**: Detailed risk explanation
- **alternative_actions**: List of alternative optimization actions with savings estimates
- **metrics**: Current metric values (CPU, connections, etc.)

### Recommendation Logic

**RDS Instances**:
- **Delete** (95% confidence): CPU < 2% AND connections < 2 (severely underutilized)
- **Resize** (85% confidence): CPU < 5% AND connections < 5 (moderately underutilized)
- **Stop** (80% confidence): CPU < 5% AND already at smallest instance class
- **Monitor** (60% confidence): CPU < 10% AND connections < 10 (slightly underutilized)
- **None** (100% confidence): Well-utilized resources

**EC2 Instances**:
- **Stop** (90% confidence): CPU < 2% AND network activity < 1000 bytes (severely underutilized)
- **Resize** (80% confidence): CPU < 5% AND can downsize to smaller instance type (moderately underutilized)
- **Stop** (75% confidence): CPU < 5% AND already at smallest instance type (no resize option)
- **Monitor or Resize** (60% confidence): CPU < 30% AND can downsize (moderately utilized, monitor before resizing)
- **None** (100% confidence): CPU >= 30% OR already at smallest instance type (well-utilized)

### Example Output

```
╔════════════════════════════════════════════════════════════════╗
║                  RDS OPTIMIZATION RECOMMENDATION               ║
╚════════════════════════════════════════════════════════════════╝

📊 RECOMMENDATION: RESIZE
   Confidence: 85%
   Risk Level: LOW

💡 REASONING:
   RDS instance is underutilized (CPU: 3.5%, Connections: 2). Can be downsized.

💰 ESTIMATED SAVINGS:
   Monthly: $45.60
   Annual: $547.20

⚠️  RISK DESCRIPTION:
   Brief downtime during maintenance window. No data loss.

🔄 ALTERNATIVE ACTIONS:
   • STOP: Stop the instance if not needed
     Estimated Savings: $136.80/month
   • DELETE: Delete if instance is no longer needed
     Estimated Savings: $152.00/month
```

### Example Usage

```python
from utils.pricing import calculate_savings, get_instance_hourly_cost, get_rds_total_cost

# Calculate savings from stopping an instance for 1 hour
savings = calculate_savings("t2.medium", hours_saved=1, region="us-east-1")
# Returns: 0.0464

# Get hourly cost for an EC2 instance
hourly = get_instance_hourly_cost("m5.large", region="eu-west-1")
# Returns: 0.1056

# Get total cost for an RDS instance (instance + storage)
rds_cost = get_rds_total_cost("db.t3.medium", "gp2", 100, region="us-east-1", multi_az=False)
# Returns: {"instance_hourly": 0.060, "storage_hourly": 0.0767, "total_hourly": 0.1367, ...}
```

---

## 🎯 Rules Engine

The FinOps Bot uses a configurable rules engine to identify underutilized resources. The rules engine has been updated to replace hardcoded logic with flexible, threshold-based evaluation.

### Configurable Thresholds

```python
DEFAULT_CPU_THRESHOLD = 5.0              # CPU utilization below 5% is waste
DEFAULT_CONNECTION_THRESHOLD = 5         # Database connections below 5 is waste
DEFAULT_REQUEST_THRESHOLD = 100          # Requests per hour below 100 is waste
DEFAULT_IOPS_THRESHOLD = 10              # IOPS below 10 is waste
```

### Available Rules

**EC2 Instances**
```python
is_waste(cpu, threshold=5.0)
# Returns True if CPU utilization is below threshold
```

**RDS Databases**
```python
is_rds_waste(cpu, connections, threshold_cpu=5.0, threshold_connections=5)
# Returns True if BOTH CPU and connections are below thresholds
```

**Load Balancers**
```python
is_load_balancer_waste(request_count, healthy_hosts, threshold=100)
# Returns True if request count is below threshold AND has healthy hosts
```

**EBS Volumes**
```python
is_ebs_waste(read_ops, write_ops, is_attached=True)
# Returns True if volume has no I/O activity OR is unattached
```

**Auto Scaling Groups**
```python
is_asg_waste(utilization_percent, threshold=20)
# Returns True if utilization is below threshold (default 20%)
```

### Example Usage

```python
from core.rules_engine import is_waste, is_rds_waste, is_load_balancer_waste

# Check if EC2 instance is wasting resources
if is_waste(cpu=2.5):  # CPU is 2.5%, below 5% threshold
    print("Instance is underutilized - candidate for optimization")

# Check if RDS instance is wasting resources
if is_rds_waste(cpu=3.0, connections=2):  # Both below thresholds
    print("RDS instance is underutilized - candidate for downsizing")

# Check if load balancer is wasting resources
if is_load_balancer_waste(request_count=50, healthy_hosts=3):  # Requests below 100
    print("Load balancer is underutilized - candidate for removal")
```

### Key Improvements

- **Fixed Logic**: Replaced incorrect `cpu < 0` logic with realistic thresholds
- **Multi-Metric Support**: Rules now evaluate multiple metrics per resource type
- **Configurable Thresholds**: All thresholds are customizable via function parameters
- **Service-Specific Rules**: Different rules for EC2, RDS, Load Balancers, EBS, and ASGs
- **Clear Documentation**: Each rule includes docstrings explaining parameters and return values

---

---

## 📊 Use Case

This project simulates how real organizations apply **FinOps principles** to:

- Reduce unnecessary cloud spend through data-driven optimization
- Improve cost visibility across multiple AWS services and regions
- Enforce governance through automation and approval workflows
- Track cost savings with accurate regional pricing models

It is ideal for:
- Cloud Engineers  
- DevOps Engineers  
- FinOps Practitioners  
- AWS learners building portfolio projects  

---

## ⚠️ Disclaimer

> This project is intended for **learning and demonstration purposes only**.  
> Always review automation rules and test in non-production environments before applying cost-optimization actions in production AWS accounts.

---

## 📌 Future Enhancements

- Persistent database (DynamoDB / PostgreSQL)
- Multi-metric optimization (Network I/O, Memory, Disk I/O)
- Approval workflows before stopping instances
- Scheduled optimization windows
- Slack / Email notifications
- AWS Pricing API integration for real-time pricing data
- Reserved Instance and Savings Plans recommendations
- Cost anomaly detection

---

## 📄 License

MIT License

---

⭐ If you find this project helpful, consider starring the repository!
