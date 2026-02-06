#!/usr/bin/env python3
"""
Anomaly Detector for Advanced FinOps Platform

Core anomaly detection engine that:
- Establishes baseline cost patterns using historical data
- Detects anomalies exceeding configurable thresholds
- Performs root cause analysis for detected anomalies
- Sends immediate alerts with detailed analysis
- Updates baseline models and improves detection accuracy

Requirements: 4.1, 4.2, 4.3
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of cost anomalies."""
    COST_SPIKE = "cost_spike"
    COST_TREND = "cost_trend"
    USAGE_PATTERN = "usage_pattern"
    SERVICE_ANOMALY = "service_anomaly"
    REGIONAL_ANOMALY = "regional_anomaly"


class AnomalySeverity(Enum):
    """Severity levels for anomalies."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BaselineModel(Enum):
    """Types of baseline models."""
    MOVING_AVERAGE = "moving_average"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    LINEAR_TREND = "linear_trend"
    PERCENTILE_BASED = "percentile_based"


class AnomalyDetector:
    """
    Cost anomaly detection engine that identifies unusual spending patterns
    and cost spikes using statistical analysis and machine learning techniques.
    
    This detector establishes baseline patterns from historical data and uses
    configurable thresholds to identify anomalies with root cause analysis.
    """
    
    def __init__(self, aws_config, region: str = 'us-east-1'):
        """
        Initialize anomaly detector.
        
        Args:
            aws_config: AWSConfig instance for client management
            region: AWS region for analysis
        """
        self.aws_config = aws_config
        self.region = region
        self.detection_thresholds = self._initialize_detection_thresholds()
        self.baseline_models = {}
        self.historical_baselines = {}
        
        logger.info(f"Anomaly Detector initialized for region {region}")
    
    def _initialize_detection_thresholds(self) -> Dict[str, Any]:
        """
        Initialize anomaly detection thresholds and parameters.
        
        Returns:
            Dictionary of detection thresholds and parameters
        """
        return {
            'baseline_requirements': {
                'min_historical_days': 14,      # Minimum days of historical data
                'optimal_historical_days': 30,  # Optimal days for baseline
                'min_data_points': 24,          # Minimum hourly data points
                'data_quality_threshold': 0.8   # Minimum data completeness ratio
            },
            'anomaly_thresholds': {
                'cost_spike_threshold': 2.0,        # Standard deviations above baseline
                'cost_trend_threshold': 1.5,        # Standard deviations for trend changes
                'percentage_increase_threshold': 50.0, # % increase to trigger alert
                'absolute_cost_threshold': 100.0,   # $ absolute increase threshold
                'consecutive_anomaly_threshold': 3   # Consecutive anomalies to confirm trend
            },
            'severity_mapping': {
                'low_threshold': 1.5,      # Standard deviations for LOW severity
                'medium_threshold': 2.0,   # Standard deviations for MEDIUM severity
                'high_threshold': 3.0,     # Standard deviations for HIGH severity
                'critical_threshold': 4.0  # Standard deviations for CRITICAL severity
            },
            'root_cause_analysis': {
                'service_contribution_threshold': 20.0,  # % contribution to consider significant
                'resource_contribution_threshold': 10.0, # % contribution for resource analysis
                'time_window_hours': 24,                 # Hours to analyze for root cause
                'correlation_threshold': 0.7             # Correlation coefficient threshold
            }
        }
    
    def detect_anomalies(self, cost_data: List[Dict[str, Any]], 
                        resources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect cost anomalies using established baselines and configurable thresholds.
        
        Args:
            cost_data: Historical cost data with timestamps
            resources: Optional resource data for root cause analysis
            
        Returns:
            Comprehensive anomaly detection results
            
        Requirements: 4.1, 4.2, 4.3
        """
        logger.info(f"Starting anomaly detection for {len(cost_data)} cost data points")
        
        # Establish baseline patterns
        baseline_analysis = self._establish_baseline_patterns(cost_data)
        
        if not baseline_analysis['baseline_established']:
            return {
                'anomalies_detected': [],
                'baseline_analysis': baseline_analysis,
                'error': 'Insufficient data to establish baseline patterns',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Detect anomalies against baseline
        detected_anomalies = self._detect_anomalies_against_baseline(
            cost_data, baseline_analysis, resources
        )
        
        # Perform root cause analysis for each anomaly
        analyzed_anomalies = []
        for anomaly in detected_anomalies:
            root_cause_analysis = self._perform_root_cause_analysis(
                anomaly, cost_data, resources
            )
            anomaly['rootCauseAnalysis'] = root_cause_analysis
            analyzed_anomalies.append(anomaly)
        
        # Update baseline models with new data
        self._update_baseline_models(cost_data, baseline_analysis)
        
        # Generate alerts for significant anomalies
        alerts = self._generate_anomaly_alerts(analyzed_anomalies)
        
        logger.info(f"Detected {len(analyzed_anomalies)} anomalies, generated {len(alerts)} alerts")
        
        return {
            'anomalies_detected': analyzed_anomalies,
            'baseline_analysis': baseline_analysis,
            'alerts_generated': alerts,
            'detection_summary': self._generate_detection_summary(analyzed_anomalies),
            'timestamp': datetime.utcnow().isoformat(),
            'region': self.region
        }
    
    def _establish_baseline_patterns(self, cost_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Establish baseline cost patterns using historical data.
        
        Requirements: 4.1 - Establish baseline cost patterns using historical data
        """
        if not cost_data:
            return {'baseline_established': False, 'reason': 'No cost data provided'}
        
        thresholds = self.detection_thresholds['baseline_requirements']
        
        # Sort cost data by timestamp
        sorted_data = sorted(cost_data, key=lambda x: x.get('timestamp', ''))
        
        # Validate data quality and completeness
        data_quality = self._validate_baseline_data_quality(sorted_data)
        
        if not data_quality['sufficient_data']:
            return {
                'baseline_established': False,
                'reason': data_quality['reason'],
                'data_quality': data_quality
            }
        
        # Extract cost values and timestamps
        costs = [float(item.get('cost', 0)) for item in sorted_data]
        timestamps = [item.get('timestamp') for item in sorted_data]
        
        # Calculate baseline statistics
        baseline_stats = self._calculate_baseline_statistics(costs)
        
        # Apply multiple baseline models
        baseline_models = {}
        
        # Moving average baseline
        baseline_models['moving_average'] = self._calculate_moving_average_baseline(costs)
        
        # Seasonal decomposition baseline (if enough data)
        if len(costs) >= 168:  # At least 1 week of hourly data
            baseline_models['seasonal'] = self._calculate_seasonal_baseline(costs, timestamps)
        
        # Linear trend baseline
        baseline_models['linear_trend'] = self._calculate_linear_trend_baseline(costs, timestamps)
        
        # Percentile-based baseline
        baseline_models['percentile'] = self._calculate_percentile_baseline(costs)
        
        # Select best baseline model
        best_model = self._select_best_baseline_model(baseline_models, costs)
        
        baseline_analysis = {
            'baseline_established': True,
            'data_quality': data_quality,
            'baseline_statistics': baseline_stats,
            'baseline_models': baseline_models,
            'selected_model': best_model,
            'baseline_period': {
                'start_date': timestamps[0] if timestamps else None,
                'end_date': timestamps[-1] if timestamps else None,
                'data_points': len(costs)
            }
        }
        
        # Store baseline for future use
        self.historical_baselines[self.region] = baseline_analysis
        
        return baseline_analysis
    
    def _detect_anomalies_against_baseline(self, cost_data: List[Dict[str, Any]], 
                                         baseline_analysis: Dict[str, Any],
                                         resources: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Detect anomalies exceeding configurable thresholds.
        
        Requirements: 4.2 - Detect anomalies exceeding configurable thresholds
        """
        anomalies = []
        thresholds = self.detection_thresholds['anomaly_thresholds']
        severity_mapping = self.detection_thresholds['severity_mapping']
        
        baseline_model = baseline_analysis['selected_model']
        baseline_stats = baseline_analysis['baseline_statistics']
        
        # Sort data by timestamp for sequential analysis
        sorted_data = sorted(cost_data, key=lambda x: x.get('timestamp', ''))
        
        for i, data_point in enumerate(sorted_data):
            current_cost = float(data_point.get('cost', 0))
            timestamp = data_point.get('timestamp')
            
            # Calculate expected cost based on baseline model
            expected_cost = self._get_expected_cost(baseline_model, i, len(sorted_data))
            
            # Calculate deviation from baseline
            if expected_cost > 0:
                deviation_percentage = ((current_cost - expected_cost) / expected_cost) * 100
                deviation_std = (current_cost - baseline_stats['mean']) / baseline_stats['std_dev']
            else:
                deviation_percentage = 0
                deviation_std = 0
            
            # Check for anomaly conditions
            is_anomaly = False
            anomaly_type = None
            severity = AnomalySeverity.LOW
            
            # Cost spike detection
            if (abs(deviation_std) >= thresholds['cost_spike_threshold'] or
                deviation_percentage >= thresholds['percentage_increase_threshold'] or
                (current_cost - expected_cost) >= thresholds['absolute_cost_threshold']):
                
                is_anomaly = True
                anomaly_type = AnomalyType.COST_SPIKE
                
                # Determine severity based on deviation
                if abs(deviation_std) >= severity_mapping['critical_threshold']:
                    severity = AnomalySeverity.CRITICAL
                elif abs(deviation_std) >= severity_mapping['high_threshold']:
                    severity = AnomalySeverity.HIGH
                elif abs(deviation_std) >= severity_mapping['medium_threshold']:
                    severity = AnomalySeverity.MEDIUM
                else:
                    severity = AnomalySeverity.LOW
            
            # Trend anomaly detection (check consecutive points)
            if i >= thresholds['consecutive_anomaly_threshold'] - 1:
                recent_points = sorted_data[i - thresholds['consecutive_anomaly_threshold'] + 1:i + 1]
                trend_anomaly = self._detect_trend_anomaly(recent_points, baseline_stats)
                
                if trend_anomaly['is_anomaly']:
                    is_anomaly = True
                    anomaly_type = AnomalyType.COST_TREND
                    severity = trend_anomaly['severity']
            
            if is_anomaly:
                anomaly_record = {
                    'anomalyId': f"anomaly-{self.region}-{int(datetime.utcnow().timestamp())}-{len(anomalies)}",
                    'timestamp': timestamp,
                    'anomalyType': anomaly_type.value,
                    'severity': severity.value,
                    'actualCost': current_cost,
                    'expectedCost': expected_cost,
                    'deviationPercentage': deviation_percentage,
                    'deviationStandardDeviations': deviation_std,
                    'baselineModel': baseline_model['model_type'],
                    'region': self.region,
                    'detectedAt': datetime.utcnow().isoformat(),
                    'dataPoint': data_point
                }
                
                anomalies.append(anomaly_record)
        
        return anomalies
    
    def _perform_root_cause_analysis(self, anomaly: Dict[str, Any], 
                                   cost_data: List[Dict[str, Any]],
                                   resources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform root cause analysis for detected anomalies.
        
        Requirements: 4.3 - Perform root cause analysis to identify contributing resources
        """
        thresholds = self.detection_thresholds['root_cause_analysis']
        anomaly_timestamp = anomaly.get('timestamp')
        
        root_cause_analysis = {
            'analysisTimestamp': datetime.utcnow().isoformat(),
            'anomalyId': anomaly.get('anomalyId'),
            'contributingFactors': [],
            'serviceBreakdown': {},
            'resourceBreakdown': {},
            'timeWindowAnalysis': {},
            'recommendations': []
        }
        
        # Analyze service-level contributions
        if resources:
            service_analysis = self._analyze_service_contributions(
                anomaly_timestamp, resources, thresholds
            )
            root_cause_analysis['serviceBreakdown'] = service_analysis
            
            # Identify significant service contributors
            for service, data in service_analysis.items():
                if data.get('contribution_percentage', 0) >= thresholds['service_contribution_threshold']:
                    root_cause_analysis['contributingFactors'].append({
                        'type': 'service',
                        'name': service,
                        'contribution': data['contribution_percentage'],
                        'cost_increase': data.get('cost_increase', 0),
                        'description': f"Service {service} contributed {data['contribution_percentage']:.1f}% to the anomaly"
                    })
        
        # Analyze resource-level contributions
        if resources:
            resource_analysis = self._analyze_resource_contributions(
                anomaly_timestamp, resources, thresholds
            )
            root_cause_analysis['resourceBreakdown'] = resource_analysis
            
            # Identify significant resource contributors
            for resource_id, data in resource_analysis.items():
                if data.get('contribution_percentage', 0) >= thresholds['resource_contribution_threshold']:
                    root_cause_analysis['contributingFactors'].append({
                        'type': 'resource',
                        'resourceId': resource_id,
                        'resourceType': data.get('resource_type', 'unknown'),
                        'contribution': data['contribution_percentage'],
                        'cost_increase': data.get('cost_increase', 0),
                        'description': f"Resource {resource_id} contributed {data['contribution_percentage']:.1f}% to the anomaly"
                    })
        
        # Time window analysis
        time_window_analysis = self._analyze_time_window_patterns(
            anomaly_timestamp, cost_data, thresholds['time_window_hours']
        )
        root_cause_analysis['timeWindowAnalysis'] = time_window_analysis
        
        # Generate recommendations based on root cause
        recommendations = self._generate_root_cause_recommendations(root_cause_analysis)
        root_cause_analysis['recommendations'] = recommendations
        
        return root_cause_analysis
    
    def _validate_baseline_data_quality(self, cost_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data quality for baseline establishment."""
        thresholds = self.detection_thresholds['baseline_requirements']
        
        if not cost_data:
            return {
                'sufficient_data': False,
                'reason': 'No cost data provided',
                'data_points': 0,
                'completeness_ratio': 0.0
            }
        
        # Check minimum data points
        data_points = len(cost_data)
        if data_points < thresholds['min_data_points']:
            return {
                'sufficient_data': False,
                'reason': f'Insufficient data points: {data_points} < {thresholds["min_data_points"]}',
                'data_points': data_points,
                'completeness_ratio': 0.0
            }
        
        # Check data recency and span
        timestamps = [item.get('timestamp') for item in cost_data if item.get('timestamp')]
        if not timestamps:
            return {
                'sufficient_data': False,
                'reason': 'No valid timestamps in data',
                'data_points': data_points,
                'completeness_ratio': 0.0
            }
        
        # Calculate data span
        try:
            earliest = min(timestamps)
            latest = max(timestamps)
            if isinstance(earliest, str):
                earliest = datetime.fromisoformat(earliest.replace('Z', '+00:00'))
            if isinstance(latest, str):
                latest = datetime.fromisoformat(latest.replace('Z', '+00:00'))
            
            data_span_days = (latest - earliest).days
            
            if data_span_days < thresholds['min_historical_days']:
                return {
                    'sufficient_data': False,
                    'reason': f'Insufficient historical span: {data_span_days} days < {thresholds["min_historical_days"]} days',
                    'data_points': data_points,
                    'data_span_days': data_span_days,
                    'completeness_ratio': 0.0
                }
        except Exception as e:
            return {
                'sufficient_data': False,
                'reason': f'Invalid timestamp format: {e}',
                'data_points': data_points,
                'completeness_ratio': 0.0
            }
        
        # Calculate completeness ratio
        valid_cost_points = len([item for item in cost_data if item.get('cost') is not None])
        completeness_ratio = valid_cost_points / data_points
        
        if completeness_ratio < thresholds['data_quality_threshold']:
            return {
                'sufficient_data': False,
                'reason': f'Poor data quality: {completeness_ratio:.2f} < {thresholds["data_quality_threshold"]}',
                'data_points': data_points,
                'valid_points': valid_cost_points,
                'completeness_ratio': completeness_ratio
            }
        
        return {
            'sufficient_data': True,
            'data_points': data_points,
            'valid_points': valid_cost_points,
            'completeness_ratio': completeness_ratio,
            'data_span_days': data_span_days,
            'earliest_timestamp': earliest.isoformat() if isinstance(earliest, datetime) else earliest,
            'latest_timestamp': latest.isoformat() if isinstance(latest, datetime) else latest
        }
    
    def _calculate_baseline_statistics(self, costs: List[float]) -> Dict[str, Any]:
        """Calculate basic statistical measures for baseline."""
        if not costs:
            return {}
        
        return {
            'mean': statistics.mean(costs),
            'median': statistics.median(costs),
            'std_dev': statistics.stdev(costs) if len(costs) > 1 else 0,
            'min': min(costs),
            'max': max(costs),
            'q25': statistics.quantiles(costs, n=4)[0] if len(costs) >= 4 else min(costs),
            'q75': statistics.quantiles(costs, n=4)[2] if len(costs) >= 4 else max(costs),
            'variance': statistics.variance(costs) if len(costs) > 1 else 0,
            'data_points': len(costs)
        }
    
    def _calculate_moving_average_baseline(self, costs: List[float], window: int = 24) -> Dict[str, Any]:
        """Calculate moving average baseline model."""
        if len(costs) < window:
            window = len(costs)
        
        moving_averages = []
        for i in range(len(costs)):
            start_idx = max(0, i - window + 1)
            window_data = costs[start_idx:i + 1]
            moving_averages.append(statistics.mean(window_data))
        
        return {
            'model_type': BaselineModel.MOVING_AVERAGE.value,
            'window_size': window,
            'predictions': moving_averages,
            'accuracy': self._calculate_model_accuracy(costs, moving_averages),
            'confidence': self._calculate_model_confidence(costs, moving_averages)
        }
    
    def _calculate_seasonal_baseline(self, costs: List[float], timestamps: List[str]) -> Dict[str, Any]:
        """Calculate seasonal decomposition baseline model."""
        # Simplified seasonal analysis - in production, use more sophisticated methods
        try:
            # Group by hour of day to detect daily patterns
            hourly_patterns = {}
            for i, timestamp in enumerate(timestamps):
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                
                hour = dt.hour
                if hour not in hourly_patterns:
                    hourly_patterns[hour] = []
                hourly_patterns[hour].append(costs[i])
            
            # Calculate average cost for each hour
            hourly_averages = {}
            for hour, hour_costs in hourly_patterns.items():
                hourly_averages[hour] = statistics.mean(hour_costs)
            
            # Generate predictions based on hourly patterns
            predictions = []
            for i, timestamp in enumerate(timestamps):
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                
                hour = dt.hour
                predictions.append(hourly_averages.get(hour, statistics.mean(costs)))
            
            return {
                'model_type': BaselineModel.SEASONAL_DECOMPOSITION.value,
                'hourly_patterns': hourly_averages,
                'predictions': predictions,
                'accuracy': self._calculate_model_accuracy(costs, predictions),
                'confidence': self._calculate_model_confidence(costs, predictions)
            }
        
        except Exception as e:
            logger.debug(f"Seasonal baseline calculation failed: {e}")
            return {
                'model_type': BaselineModel.SEASONAL_DECOMPOSITION.value,
                'error': str(e),
                'predictions': [statistics.mean(costs)] * len(costs),
                'accuracy': 0.0,
                'confidence': 0.0
            }
    
    def _calculate_linear_trend_baseline(self, costs: List[float], timestamps: List[str]) -> Dict[str, Any]:
        """Calculate linear trend baseline model."""
        if len(costs) < 2:
            return {
                'model_type': BaselineModel.LINEAR_TREND.value,
                'predictions': costs,
                'accuracy': 0.0,
                'confidence': 0.0
            }
        
        # Simple linear regression
        n = len(costs)
        x_values = list(range(n))
        
        # Calculate slope and intercept
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(costs)
        
        numerator = sum((x_values[i] - x_mean) * (costs[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = y_mean - slope * x_mean
        
        # Generate predictions
        predictions = [intercept + slope * x for x in x_values]
        
        return {
            'model_type': BaselineModel.LINEAR_TREND.value,
            'slope': slope,
            'intercept': intercept,
            'predictions': predictions,
            'accuracy': self._calculate_model_accuracy(costs, predictions),
            'confidence': self._calculate_model_confidence(costs, predictions)
        }
    
    def _calculate_percentile_baseline(self, costs: List[float]) -> Dict[str, Any]:
        """Calculate percentile-based baseline model."""
        if not costs:
            return {
                'model_type': BaselineModel.PERCENTILE_BASED.value,
                'predictions': [],
                'accuracy': 0.0,
                'confidence': 0.0
            }
        
        # Use median as baseline prediction
        median_cost = statistics.median(costs)
        predictions = [median_cost] * len(costs)
        
        # Calculate percentile ranges
        percentiles = {
            'p10': statistics.quantiles(costs, n=10)[0] if len(costs) >= 10 else min(costs),
            'p25': statistics.quantiles(costs, n=4)[0] if len(costs) >= 4 else min(costs),
            'p50': median_cost,
            'p75': statistics.quantiles(costs, n=4)[2] if len(costs) >= 4 else max(costs),
            'p90': statistics.quantiles(costs, n=10)[8] if len(costs) >= 10 else max(costs)
        }
        
        return {
            'model_type': BaselineModel.PERCENTILE_BASED.value,
            'percentiles': percentiles,
            'predictions': predictions,
            'accuracy': self._calculate_model_accuracy(costs, predictions),
            'confidence': self._calculate_model_confidence(costs, predictions)
        }
    
    def _select_best_baseline_model(self, baseline_models: Dict[str, Dict[str, Any]], 
                                  costs: List[float]) -> Dict[str, Any]:
        """Select the best baseline model based on accuracy and confidence."""
        if not baseline_models:
            return {}
        
        # Score each model based on accuracy and confidence
        model_scores = {}
        for model_name, model_data in baseline_models.items():
            accuracy = model_data.get('accuracy', 0.0)
            confidence = model_data.get('confidence', 0.0)
            
            # Combined score (weighted average)
            score = (accuracy * 0.6) + (confidence * 0.4)
            model_scores[model_name] = score
        
        # Select model with highest score
        best_model_name = max(model_scores, key=model_scores.get)
        best_model = baseline_models[best_model_name].copy()
        best_model['model_name'] = best_model_name
        best_model['score'] = model_scores[best_model_name]
        
        return best_model
    
    def _calculate_model_accuracy(self, actual: List[float], predicted: List[float]) -> float:
        """Calculate model accuracy using Mean Absolute Percentage Error (MAPE)."""
        if not actual or not predicted or len(actual) != len(predicted):
            return 0.0
        
        try:
            mape = statistics.mean(
                abs((actual[i] - predicted[i]) / actual[i]) * 100 
                for i in range(len(actual)) 
                if actual[i] != 0
            )
            # Convert MAPE to accuracy (0-100 scale)
            accuracy = max(0, 100 - mape)
            return accuracy
        except (ZeroDivisionError, statistics.StatisticsError):
            return 0.0
    
    def _calculate_model_confidence(self, actual: List[float], predicted: List[float]) -> float:
        """Calculate model confidence based on prediction consistency."""
        if not actual or not predicted or len(actual) != len(predicted):
            return 0.0
        
        try:
            # Calculate correlation coefficient
            n = len(actual)
            if n < 2:
                return 0.0
            
            actual_mean = statistics.mean(actual)
            predicted_mean = statistics.mean(predicted)
            
            numerator = sum((actual[i] - actual_mean) * (predicted[i] - predicted_mean) for i in range(n))
            
            actual_var = sum((actual[i] - actual_mean) ** 2 for i in range(n))
            predicted_var = sum((predicted[i] - predicted_mean) ** 2 for i in range(n))
            
            denominator = (actual_var * predicted_var) ** 0.5
            
            if denominator == 0:
                return 0.0
            
            correlation = numerator / denominator
            
            # Convert correlation to confidence (0-100 scale)
            confidence = abs(correlation) * 100
            return min(100, confidence)
        
        except (ZeroDivisionError, statistics.StatisticsError):
            return 0.0
    
    def _get_expected_cost(self, baseline_model: Dict[str, Any], index: int, total_points: int) -> float:
        """Get expected cost from baseline model for given index."""
        predictions = baseline_model.get('predictions', [])
        
        if not predictions:
            return 0.0
        
        if index < len(predictions):
            return predictions[index]
        
        # If index is beyond predictions, use the last prediction or model-specific logic
        model_type = baseline_model.get('model_type')
        
        if model_type == BaselineModel.LINEAR_TREND.value:
            # Extrapolate using linear trend
            slope = baseline_model.get('slope', 0)
            intercept = baseline_model.get('intercept', 0)
            return intercept + slope * index
        
        # Default to last prediction
        return predictions[-1] if predictions else 0.0
    
    def _detect_trend_anomaly(self, recent_points: List[Dict[str, Any]], 
                            baseline_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Detect trend anomalies in consecutive data points."""
        if len(recent_points) < 3:
            return {'is_anomaly': False}
        
        costs = [float(point.get('cost', 0)) for point in recent_points]
        
        # Calculate trend
        n = len(costs)
        x_values = list(range(n))
        
        # Simple linear regression for trend
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(costs)
        
        numerator = sum((x_values[i] - x_mean) * (costs[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return {'is_anomaly': False}
        
        slope = numerator / denominator
        
        # Check if trend is significantly different from baseline
        baseline_mean = baseline_stats.get('mean', 0)
        baseline_std = baseline_stats.get('std_dev', 1)
        
        # Normalize slope by baseline statistics
        normalized_slope = abs(slope) / baseline_std if baseline_std > 0 else 0
        
        thresholds = self.detection_thresholds['anomaly_thresholds']
        severity_mapping = self.detection_thresholds['severity_mapping']
        
        if normalized_slope >= thresholds['cost_trend_threshold']:
            # Determine severity
            if normalized_slope >= severity_mapping['critical_threshold']:
                severity = AnomalySeverity.CRITICAL
            elif normalized_slope >= severity_mapping['high_threshold']:
                severity = AnomalySeverity.HIGH
            elif normalized_slope >= severity_mapping['medium_threshold']:
                severity = AnomalySeverity.MEDIUM
            else:
                severity = AnomalySeverity.LOW
            
            return {
                'is_anomaly': True,
                'severity': severity,
                'trend_slope': slope,
                'normalized_slope': normalized_slope,
                'trend_direction': 'increasing' if slope > 0 else 'decreasing'
            }
        
        return {'is_anomaly': False}
    
    def _analyze_service_contributions(self, anomaly_timestamp: str, 
                                     resources: List[Dict[str, Any]],
                                     thresholds: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze service-level contributions to the anomaly."""
        service_analysis = {}
        
        # Group resources by service type
        services = {}
        for resource in resources:
            service_type = resource.get('resourceType', 'unknown')
            if service_type not in services:
                services[service_type] = []
            services[service_type].append(resource)
        
        # Calculate cost contributions for each service
        total_cost_increase = 0
        for service_type, service_resources in services.items():
            service_cost_increase = 0
            resource_count = len(service_resources)
            
            for resource in service_resources:
                # Calculate cost increase around anomaly timestamp
                current_cost = resource.get('currentCost', 0)
                historical_cost = resource.get('historicalAverageCost', current_cost)
                cost_increase = max(0, current_cost - historical_cost)
                service_cost_increase += cost_increase
            
            total_cost_increase += service_cost_increase
            
            service_analysis[service_type] = {
                'cost_increase': service_cost_increase,
                'resource_count': resource_count,
                'avg_cost_per_resource': service_cost_increase / resource_count if resource_count > 0 else 0
            }
        
        # Calculate contribution percentages
        for service_type, data in service_analysis.items():
            if total_cost_increase > 0:
                data['contribution_percentage'] = (data['cost_increase'] / total_cost_increase) * 100
            else:
                data['contribution_percentage'] = 0
        
        return service_analysis
    
    def _analyze_resource_contributions(self, anomaly_timestamp: str,
                                      resources: List[Dict[str, Any]],
                                      thresholds: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resource-level contributions to the anomaly."""
        resource_analysis = {}
        total_cost_increase = 0
        
        # Calculate cost increase for each resource
        for resource in resources:
            resource_id = resource.get('resourceId', 'unknown')
            current_cost = resource.get('currentCost', 0)
            historical_cost = resource.get('historicalAverageCost', current_cost)
            cost_increase = max(0, current_cost - historical_cost)
            
            total_cost_increase += cost_increase
            
            resource_analysis[resource_id] = {
                'resource_type': resource.get('resourceType', 'unknown'),
                'current_cost': current_cost,
                'historical_cost': historical_cost,
                'cost_increase': cost_increase,
                'region': resource.get('region', self.region)
            }
        
        # Calculate contribution percentages
        for resource_id, data in resource_analysis.items():
            if total_cost_increase > 0:
                data['contribution_percentage'] = (data['cost_increase'] / total_cost_increase) * 100
            else:
                data['contribution_percentage'] = 0
        
        return resource_analysis
    
    def _analyze_time_window_patterns(self, anomaly_timestamp: str,
                                    cost_data: List[Dict[str, Any]],
                                    window_hours: int) -> Dict[str, Any]:
        """Analyze cost patterns in time window around anomaly."""
        try:
            if isinstance(anomaly_timestamp, str):
                anomaly_dt = datetime.fromisoformat(anomaly_timestamp.replace('Z', '+00:00'))
            else:
                anomaly_dt = anomaly_timestamp
            
            window_start = anomaly_dt - timedelta(hours=window_hours)
            window_end = anomaly_dt + timedelta(hours=window_hours)
            
            # Filter cost data to time window
            window_data = []
            for data_point in cost_data:
                timestamp = data_point.get('timestamp')
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                
                if window_start <= dt <= window_end:
                    window_data.append(data_point)
            
            if not window_data:
                return {'error': 'No data in time window'}
            
            # Analyze patterns in window
            costs = [float(point.get('cost', 0)) for point in window_data]
            
            return {
                'window_start': window_start.isoformat(),
                'window_end': window_end.isoformat(),
                'data_points': len(window_data),
                'cost_statistics': {
                    'min': min(costs),
                    'max': max(costs),
                    'mean': statistics.mean(costs),
                    'median': statistics.median(costs),
                    'std_dev': statistics.stdev(costs) if len(costs) > 1 else 0
                },
                'cost_trend': self._calculate_window_trend(costs),
                'volatility': statistics.stdev(costs) / statistics.mean(costs) if statistics.mean(costs) > 0 and len(costs) > 1 else 0
            }
        
        except Exception as e:
            return {'error': f'Time window analysis failed: {e}'}
    
    def _calculate_window_trend(self, costs: List[float]) -> Dict[str, Any]:
        """Calculate trend within time window."""
        if len(costs) < 2:
            return {'trend': 'insufficient_data'}
        
        n = len(costs)
        x_values = list(range(n))
        
        # Linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(costs)
        
        numerator = sum((x_values[i] - x_mean) * (costs[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return {'trend': 'no_trend', 'slope': 0}
        
        slope = numerator / denominator
        
        if slope > 0.1:
            trend = 'increasing'
        elif slope < -0.1:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'slope': slope,
            'start_cost': costs[0],
            'end_cost': costs[-1],
            'total_change': costs[-1] - costs[0],
            'percentage_change': ((costs[-1] - costs[0]) / costs[0] * 100) if costs[0] > 0 else 0
        }
    
    def _generate_root_cause_recommendations(self, root_cause_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on root cause analysis."""
        recommendations = []
        
        contributing_factors = root_cause_analysis.get('contributingFactors', [])
        
        for factor in contributing_factors:
            if factor['type'] == 'service':
                service_name = factor['name']
                contribution = factor['contribution']
                
                recommendations.append({
                    'type': 'service_investigation',
                    'priority': 'HIGH' if contribution > 50 else 'MEDIUM',
                    'title': f"Investigate {service_name} service cost increase",
                    'description': f"Service {service_name} contributed {contribution:.1f}% to the cost anomaly",
                    'action': f"Review {service_name} resource usage and configuration changes",
                    'target': service_name
                })
            
            elif factor['type'] == 'resource':
                resource_id = factor['resourceId']
                resource_type = factor['resourceType']
                contribution = factor['contribution']
                
                recommendations.append({
                    'type': 'resource_investigation',
                    'priority': 'HIGH' if contribution > 30 else 'MEDIUM',
                    'title': f"Investigate resource {resource_id}",
                    'description': f"Resource {resource_id} ({resource_type}) contributed {contribution:.1f}% to the cost anomaly",
                    'action': f"Review resource {resource_id} configuration and usage patterns",
                    'target': resource_id,
                    'resourceType': resource_type
                })
        
        # Add general recommendations
        recommendations.append({
            'type': 'monitoring',
            'priority': 'MEDIUM',
            'title': 'Enhance cost monitoring',
            'description': 'Set up more granular cost monitoring to detect similar anomalies earlier',
            'action': 'Configure CloudWatch alarms and budget alerts for affected services'
        })
        
        return recommendations
    
    def _update_baseline_models(self, cost_data: List[Dict[str, Any]], 
                              baseline_analysis: Dict[str, Any]) -> None:
        """
        Update baseline models with new data and improve detection accuracy.
        
        Requirements: 4.5 - Update baseline models and improve detection accuracy
        """
        # Store updated baseline models for future use
        self.baseline_models[self.region] = baseline_analysis
        
        # Log baseline update
        logger.info(f"Updated baseline models for region {self.region} with {len(cost_data)} data points")
    
    def _generate_anomaly_alerts(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate immediate alerts with detailed analysis.
        
        Requirements: 4.4 - Send immediate alerts with detailed analysis
        """
        alerts = []
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'LOW')
            
            # Only generate alerts for MEDIUM and above severity
            if severity in ['MEDIUM', 'HIGH', 'CRITICAL']:
                alert = {
                    'alertId': f"alert-{anomaly.get('anomalyId')}",
                    'timestamp': datetime.utcnow().isoformat(),
                    'severity': severity,
                    'title': f"Cost Anomaly Detected: {anomaly.get('anomalyType', 'Unknown')}",
                    'description': self._generate_alert_description(anomaly),
                    'anomaly': anomaly,
                    'rootCause': anomaly.get('rootCauseAnalysis', {}),
                    'recommendations': anomaly.get('rootCauseAnalysis', {}).get('recommendations', []),
                    'region': self.region,
                    'alertType': 'COST_ANOMALY'
                }
                
                alerts.append(alert)
        
        return alerts
    
    def _generate_alert_description(self, anomaly: Dict[str, Any]) -> str:
        """Generate human-readable alert description."""
        anomaly_type = anomaly.get('anomalyType', 'Unknown')
        actual_cost = anomaly.get('actualCost', 0)
        expected_cost = anomaly.get('expectedCost', 0)
        deviation_pct = anomaly.get('deviationPercentage', 0)
        
        if anomaly_type == 'cost_spike':
            return (f"Cost spike detected: ${actual_cost:.2f} vs expected ${expected_cost:.2f} "
                   f"({deviation_pct:+.1f}% deviation)")
        elif anomaly_type == 'cost_trend':
            return f"Unusual cost trend detected with {deviation_pct:+.1f}% deviation from baseline"
        else:
            return f"Cost anomaly detected: {deviation_pct:+.1f}% deviation from expected patterns"
    
    def _generate_detection_summary(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of anomaly detection results."""
        if not anomalies:
            return {
                'total_anomalies': 0,
                'severity_breakdown': {},
                'type_breakdown': {},
                'total_cost_impact': 0.0
            }
        
        # Count by severity
        severity_counts = {}
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'LOW')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by type
        type_counts = {}
        for anomaly in anomalies:
            anomaly_type = anomaly.get('anomalyType', 'unknown')
            type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
        
        # Calculate total cost impact
        total_cost_impact = sum(
            anomaly.get('actualCost', 0) - anomaly.get('expectedCost', 0)
            for anomaly in anomalies
        )
        
        return {
            'total_anomalies': len(anomalies),
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'total_cost_impact': total_cost_impact,
            'most_severe': max(anomalies, key=lambda x: {
                'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4
            }.get(x.get('severity', 'LOW'), 1)) if anomalies else None
        }