# Advanced FinOps Platform - Frontend

A comprehensive React dashboard for AWS cost optimization and financial operations management.

## Features

### 🎯 **Cost Optimization Dashboard**
- Real-time cost monitoring across all AWS services
- Interactive charts and visualizations using Recharts
- Multi-service cost breakdown (EC2, RDS, Lambda, S3, EBS, ELB, CloudWatch)
- Time-range filtering (24h, 7d, 30d, 90d)

### 📊 **Resource Management**
- Complete resource inventory across AWS services
- Utilization metrics and optimization opportunities
- Risk-level categorization (LOW, MEDIUM, HIGH, CRITICAL)
- Advanced filtering by service, region, and search terms

### 🔧 **Optimization Recommendations**
- ML-powered right-sizing recommendations
- Reserved Instance and Spot Instance opportunities
- Pricing intelligence with confidence scores
- Risk-based approval workflows

### 💰 **Budget Management**
- Hierarchical budget structures (organization/team/project)
- Cost forecasting with confidence intervals
- Budget utilization tracking and alerts
- Variance analysis and trend reporting

### 🚨 **Anomaly Detection**
- Real-time cost spike detection
- Root cause analysis with resource attribution
- Severity-based alerting (CRITICAL, HIGH, MEDIUM, LOW)
- Historical anomaly timeline visualization

### 💎 **Savings Tracking**
- Comprehensive savings reports and analytics
- Savings by service and optimization type
- ROI calculations and projections
- Top optimization achievements

### ⚙️ **Settings & Configuration**
- Customizable optimization thresholds
- Notification preferences
- Automation settings with safety controls
- AWS configuration management

## Technology Stack

- **React 18** - Modern React with hooks and functional components
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Interactive charts and data visualization
- **Lucide React** - Beautiful icon library
- **Axios** - HTTP client for API communication
- **Headless UI** - Unstyled, accessible UI components

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Advanced FinOps Backend running on port 5002

### Installation

1. **Install dependencies:**
   ```bash
   cd advanced-finops-frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## Project Structure

```
advanced-finops-frontend/
├── public/
│   ├── index.html
│   └── manifest.json
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Layout.js       # Main layout with navigation
│   │   ├── LoadingSpinner.js
│   │   ├── MetricCard.js   # Dashboard metric cards
│   │   └── StatusBadge.js  # Status indicators
│   ├── pages/              # Main application pages
│   │   ├── Dashboard.js    # Cost overview dashboard
│   │   ├── Resources.js    # Resource inventory
│   │   ├── Optimizations.js # Optimization recommendations
│   │   ├── Budgets.js      # Budget management
│   │   ├── Anomalies.js    # Cost anomaly detection
│   │   ├── Savings.js      # Savings reports
│   │   └── Settings.js     # Configuration
│   ├── services/
│   │   └── api.js          # API service layer
│   ├── App.js              # Main application component
│   ├── index.js            # Application entry point
│   └── index.css           # Global styles and Tailwind
├── tailwind.config.js      # Tailwind configuration
├── postcss.config.js       # PostCSS configuration
└── package.json
```

## API Integration

The frontend connects to the Advanced FinOps Backend API on port 5002:

### Key Endpoints
- `GET /api/dashboard` - Dashboard overview data
- `GET /api/resources` - Resource inventory
- `GET /api/optimizations` - Optimization recommendations
- `GET /api/budgets` - Budget management
- `GET /api/anomalies` - Cost anomalies
- `GET /api/savings` - Savings reports

### Configuration
The API base URL is configured via:
- Environment variable: `REACT_APP_API_URL`
- Default: `http://localhost:5002`
- Proxy in package.json for development

## Key Features

### 🎨 **Modern UI/UX**
- Clean, professional design with Tailwind CSS
- Responsive layout for desktop and mobile
- Interactive data visualizations
- Consistent color scheme and typography

### 📱 **Responsive Design**
- Mobile-first approach
- Collapsible sidebar navigation
- Adaptive grid layouts
- Touch-friendly interactions

### 🔄 **Real-time Updates**
- Auto-refresh capabilities
- Live data synchronization
- Progress indicators
- Error handling with retry options

### 🎯 **Data Visualization**
- Interactive charts with Recharts
- Cost trend analysis
- Service breakdown pie charts
- Regional cost comparisons
- Anomaly timeline visualization

### 🛡️ **Error Handling**
- Comprehensive error boundaries
- Graceful fallbacks with mock data
- User-friendly error messages
- Retry mechanisms

## Development

### Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run test suite
- `npm run eject` - Eject from Create React App

### Environment Variables

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=http://localhost:5002
REACT_APP_ENVIRONMENT=development
```

### Code Style

The project follows React best practices:
- Functional components with hooks
- Consistent naming conventions
- Modular component structure
- Proper error boundaries
- Accessible UI components

## Deployment

### Production Build

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

### Deployment Options

1. **Static Hosting** (Netlify, Vercel, S3)
2. **Docker Container**
3. **Traditional Web Server** (Nginx, Apache)

### Docker Deployment

```dockerfile
FROM node:16-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Integration with Backend

The frontend is designed to work seamlessly with the Advanced FinOps Backend:

1. **Data Flow**: Frontend → API → Python Engine → AWS Services
2. **Real-time Updates**: WebSocket support for live data
3. **Authentication**: Ready for JWT token integration
4. **Error Handling**: Comprehensive API error management

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow the established code style
2. Add tests for new features
3. Update documentation
4. Ensure responsive design
5. Test across different browsers

## License

This project is part of the Advanced FinOps Platform suite.