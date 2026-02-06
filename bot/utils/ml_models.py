#!/usr/bin/env python3
"""
Machine Learning Model Utilities for Advanced FinOps Platform

Provides comprehensive machine learning operations including:
- Model training, validation, and inference utilities
- Feature engineering and data preprocessing functions
- Model performance monitoring and drift detection
- Support for right-sizing, anomaly detection, and cost forecasting models

Requirements: 3.2, 3.5, 4.5
"""

import logging
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import warnings
from pathlib import Path

# Suppress sklearn warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)

try:
    from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.cluster import KMeans
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available. ML functionality will be limited.")

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Supported machine learning model types."""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    TIME_SERIES = "time_series"


class ModelStatus(Enum):
    """Model lifecycle status."""
    TRAINING = "training"
    TRAINED = "trained"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class ModelMetrics:
    """Model performance metrics."""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    mse: float = 0.0
    mae: float = 0.0
    r2_score: float = 0.0
    cross_val_score: float = 0.0
    training_time: float = 0.0
    inference_time: float = 0.0
    model_size_mb: float = 0.0


@dataclass
class DriftMetrics:
    """Model drift detection metrics."""
    feature_drift_score: float = 0.0
    prediction_drift_score: float = 0.0
    data_quality_score: float = 0.0
    drift_detected: bool = False
    drift_severity: str = "none"  # none, low, medium, high
    affected_features: List[str] = None
    
    def __post_init__(self):
        if self.affected_features is None:
            self.affected_features = []


@dataclass
class ModelConfig:
    """Model configuration parameters."""
    model_type: ModelType
    model_name: str
    version: str = "1.0.0"
    hyperparameters: Dict[str, Any] = None
    feature_columns: List[str] = None
    target_column: str = ""
    validation_split: float = 0.2
    test_split: float = 0.1
    cross_validation_folds: int = 5
    random_state: int = 42
    
    def __post_init__(self):
        if self.hyperparameters is None:
            self.hyperparameters = {}
        if self.feature_columns is None:
            self.feature_columns = []


class MLModelManager:
    """
    Comprehensive machine learning model management system.
    
    Provides model training, validation, inference, and monitoring capabilities
    for the Advanced FinOps Platform's ML-powered optimization features.
    """
    
    def __init__(self, model_storage_path: str = "ml_models"):
        """
        Initialize ML model manager.
        
        Args:
            model_storage_path: Directory path for storing trained models
        """
        self.model_storage_path = Path(model_storage_path)
        self.model_storage_path.mkdir(exist_ok=True)
        
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.model_metadata = {}
        
        # Performance monitoring
        self.performance_history = {}
        self.drift_history = {}
        
        logger.info(f"ML Model Manager initialized with storage path: {self.model_storage_path}")
        
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available. Using fallback implementations.")
    
    def create_model(self, config: ModelConfig) -> Any:
        """
        Create a machine learning model based on configuration.
        
        Args:
            config: Model configuration parameters
            
        Returns:
            Initialized ML model
            
        Requirements: 3.2 - ML model training and validation utilities
        """
        logger.info(f"Creating {config.model_type.value} model: {config.model_name}")
        
        if not SKLEARN_AVAILABLE:
            return self._create_fallback_model(config)
        
        try:
            # Create model based on type
            if config.model_type == ModelType.REGRESSION:
                if config.hyperparameters.get('algorithm', 'random_forest') == 'random_forest':
                    model = RandomForestRegressor(
                        n_estimators=config.hyperparameters.get('n_estimators', 100),
                        max_depth=config.hyperparameters.get('max_depth', None),
                        min_samples_split=config.hyperparameters.get('min_samples_split', 2),
                        min_samples_leaf=config.hyperparameters.get('min_samples_leaf', 1),
                        random_state=config.random_state
                    )
                else:
                    model = LinearRegression()
                    
            elif config.model_type == ModelType.ANOMALY_DETECTION:
                model = IsolationForest(
                    n_estimators=config.hyperparameters.get('n_estimators', 100),
                    contamination=config.hyperparameters.get('contamination', 0.1),
                    random_state=config.random_state
                )
                
            elif config.model_type == ModelType.CLUSTERING:
                model = KMeans(
                    n_clusters=config.hyperparameters.get('n_clusters', 3),
                    random_state=config.random_state
                )
                
            else:
                # Default to linear regression
                model = LinearRegression()
            
            # Store model configuration
            self.model_metadata[config.model_name] = {
                'config': config,
                'status': ModelStatus.TRAINING,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'metrics': ModelMetrics(),
                'drift_metrics': DriftMetrics()
            }
            
            logger.info(f"Created {config.model_type.value} model: {config.model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create model {config.model_name}: {e}")
            return self._create_fallback_model(config)
    
    def train_model(self, model_name: str, training_data: pd.DataFrame, 
                   target_data: pd.Series = None, config: ModelConfig = None) -> Dict[str, Any]:
        """
        Train a machine learning model with comprehensive validation.
        
        Args:
            model_name: Name of the model to train
            training_data: Training dataset
            target_data: Target values (for supervised learning)
            config: Model configuration (if not already stored)
            
        Returns:
            Training results and metrics
            
        Requirements: 3.2 - ML model training utilities
        """
        logger.info(f"Training model: {model_name}")
        start_time = datetime.now()
        
        try:
            # Get or create model configuration
            if config:
                model = self.create_model(config)
                self.models[model_name] = model
            elif model_name not in self.models:
                raise ValueError(f"Model {model_name} not found and no config provided")
            else:
                model = self.models[model_name]
                config = self.model_metadata[model_name]['config']
            
            # Preprocess data
            processed_data, processed_target = self._preprocess_data(
                training_data, target_data, model_name, config
            )
            
            # Split data for validation
            if target_data is not None:
                X_train, X_val, y_train, y_val = train_test_split(
                    processed_data, processed_target,
                    test_size=config.validation_split,
                    random_state=config.random_state
                )
            else:
                # Unsupervised learning
                X_train = processed_data
                X_val = None
                y_train = None
                y_val = None
            
            # Train the model
            if target_data is not None:
                model.fit(X_train, y_train)
            else:
                model.fit(X_train)
            
            # Calculate training time
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Validate model performance
            metrics = self._validate_model(model, X_train, y_train, X_val, y_val, config)
            metrics.training_time = training_time
            
            # Update model metadata
            self.model_metadata[model_name].update({
                'status': ModelStatus.TRAINED,
                'trained_at': datetime.now(timezone.utc).isoformat(),
                'metrics': metrics,
                'training_samples': len(training_data),
                'feature_count': len(config.feature_columns) if config.feature_columns else processed_data.shape[1]
            })
            
            # Save model
            self._save_model(model_name, model)
            
            logger.info(f"Model {model_name} trained successfully in {training_time:.2f}s")
            
            return {
                'model_name': model_name,
                'status': 'success',
                'training_time': training_time,
                'metrics': asdict(metrics),
                'training_samples': len(training_data),
                'validation_samples': len(X_val) if X_val is not None else 0,
                'feature_count': processed_data.shape[1],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to train model {model_name}: {e}")
            
            # Update status to failed
            if model_name in self.model_metadata:
                self.model_metadata[model_name]['status'] = ModelStatus.FAILED
            
            return {
                'model_name': model_name,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def predict(self, model_name: str, input_data: pd.DataFrame, 
               return_confidence: bool = False) -> Dict[str, Any]:
        """
        Make predictions using a trained model.
        
        Args:
            model_name: Name of the trained model
            input_data: Input data for prediction
            return_confidence: Whether to return confidence intervals
            
        Returns:
            Prediction results with optional confidence intervals
            
        Requirements: 3.2 - ML model inference utilities
        """
        logger.debug(f"Making predictions with model: {model_name}")
        start_time = datetime.now()
        
        try:
            if model_name not in self.models:
                # Try to load model from storage
                self._load_model(model_name)
            
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not found")
            
            model = self.models[model_name]
            config = self.model_metadata[model_name]['config']
            
            # Preprocess input data
            processed_data, _ = self._preprocess_data(input_data, None, model_name, config, is_training=False)
            
            # Make predictions
            if hasattr(model, 'predict_proba') and return_confidence:
                predictions = model.predict(processed_data)
                probabilities = model.predict_proba(processed_data)
                confidence_scores = np.max(probabilities, axis=1)
            else:
                predictions = model.predict(processed_data)
                confidence_scores = None
            
            # Calculate inference time
            inference_time = (datetime.now() - start_time).total_seconds()
            
            # Update performance metrics
            if model_name in self.model_metadata:
                self.model_metadata[model_name]['metrics'].inference_time = inference_time
            
            result = {
                'model_name': model_name,
                'predictions': predictions.tolist() if hasattr(predictions, 'tolist') else predictions,
                'prediction_count': len(predictions),
                'inference_time': inference_time,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            if confidence_scores is not None:
                result['confidence_scores'] = confidence_scores.tolist()
                result['average_confidence'] = float(np.mean(confidence_scores))
            
            logger.debug(f"Generated {len(predictions)} predictions in {inference_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to make predictions with model {model_name}: {e}")
            return {
                'model_name': model_name,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def detect_drift(self, model_name: str, new_data: pd.DataFrame, 
                    reference_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Detect model drift by comparing new data with reference data.
        
        Args:
            model_name: Name of the model to check for drift
            new_data: New data to compare
            reference_data: Reference data (training data if not provided)
            
        Returns:
            Drift detection results and metrics
            
        Requirements: 4.5 - Model drift detection
        """
        logger.info(f"Detecting drift for model: {model_name}")
        
        try:
            if model_name not in self.model_metadata:
                raise ValueError(f"Model {model_name} not found")
            
            config = self.model_metadata[model_name]['config']
            
            # Use stored reference data if not provided
            if reference_data is None:
                reference_data = self._get_reference_data(model_name)
                if reference_data is None:
                    logger.warning(f"No reference data available for model {model_name}")
                    return self._create_drift_result(model_name, DriftMetrics(), "no_reference_data")
            
            # Calculate drift metrics
            drift_metrics = self._calculate_drift_metrics(new_data, reference_data, config)
            
            # Determine drift severity
            drift_severity = self._assess_drift_severity(drift_metrics)
            drift_metrics.drift_severity = drift_severity
            drift_metrics.drift_detected = drift_severity != "none"
            
            # Update model metadata
            self.model_metadata[model_name]['drift_metrics'] = drift_metrics
            
            # Store drift history
            if model_name not in self.drift_history:
                self.drift_history[model_name] = []
            
            self.drift_history[model_name].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'drift_metrics': asdict(drift_metrics),
                'data_samples': len(new_data)
            })
            
            # Keep only last 100 drift measurements
            if len(self.drift_history[model_name]) > 100:
                self.drift_history[model_name] = self.drift_history[model_name][-100:]
            
            logger.info(f"Drift detection completed for {model_name}: {drift_severity} drift detected")
            
            return self._create_drift_result(model_name, drift_metrics, "success")
            
        except Exception as e:
            logger.error(f"Failed to detect drift for model {model_name}: {e}")
            return self._create_drift_result(model_name, DriftMetrics(), "failed", str(e))
    
    def monitor_performance(self, model_name: str, actual_values: List[float], 
                          predicted_values: List[float]) -> Dict[str, Any]:
        """
        Monitor model performance over time.
        
        Args:
            model_name: Name of the model to monitor
            actual_values: Actual observed values
            predicted_values: Model predictions
            
        Returns:
            Performance monitoring results
            
        Requirements: 3.5 - Model performance monitoring
        """
        logger.info(f"Monitoring performance for model: {model_name}")
        
        try:
            if len(actual_values) != len(predicted_values):
                raise ValueError("Actual and predicted values must have the same length")
            
            # Calculate performance metrics
            mse = mean_squared_error(actual_values, predicted_values) if SKLEARN_AVAILABLE else self._calculate_mse(actual_values, predicted_values)
            mae = mean_absolute_error(actual_values, predicted_values) if SKLEARN_AVAILABLE else self._calculate_mae(actual_values, predicted_values)
            r2 = r2_score(actual_values, predicted_values) if SKLEARN_AVAILABLE else self._calculate_r2(actual_values, predicted_values)
            
            # Calculate additional metrics
            rmse = np.sqrt(mse)
            mape = self._calculate_mape(actual_values, predicted_values)
            
            performance_metrics = {
                'mse': float(mse),
                'mae': float(mae),
                'rmse': float(rmse),
                'r2_score': float(r2),
                'mape': float(mape),
                'sample_count': len(actual_values),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Store performance history
            if model_name not in self.performance_history:
                self.performance_history[model_name] = []
            
            self.performance_history[model_name].append(performance_metrics)
            
            # Keep only last 100 performance measurements
            if len(self.performance_history[model_name]) > 100:
                self.performance_history[model_name] = self.performance_history[model_name][-100:]
            
            # Update model metadata
            if model_name in self.model_metadata:
                current_metrics = self.model_metadata[model_name]['metrics']
                current_metrics.mse = mse
                current_metrics.mae = mae
                current_metrics.r2_score = r2
            
            # Assess performance degradation
            performance_trend = self._assess_performance_trend(model_name)
            
            logger.info(f"Performance monitoring completed for {model_name}: R² = {r2:.3f}, RMSE = {rmse:.3f}")
            
            return {
                'model_name': model_name,
                'status': 'success',
                'current_metrics': performance_metrics,
                'performance_trend': performance_trend,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor performance for model {model_name}: {e}")
            return {
                'model_name': model_name,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def engineer_features(self, data: pd.DataFrame, feature_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Perform feature engineering on input data.
        
        Args:
            data: Input dataset
            feature_config: Feature engineering configuration
            
        Returns:
            Dataset with engineered features
            
        Requirements: 3.2 - Feature engineering functions
        """
        logger.info("Performing feature engineering")
        
        try:
            engineered_data = data.copy()
            
            # Time-based features
            if feature_config.get('time_features', False):
                engineered_data = self._create_time_features(engineered_data)
            
            # Statistical features
            if feature_config.get('statistical_features', False):
                engineered_data = self._create_statistical_features(engineered_data, feature_config)
            
            # Interaction features
            if feature_config.get('interaction_features', False):
                engineered_data = self._create_interaction_features(engineered_data, feature_config)
            
            # Polynomial features
            if feature_config.get('polynomial_features', False):
                engineered_data = self._create_polynomial_features(engineered_data, feature_config)
            
            # Domain-specific features for FinOps
            if feature_config.get('finops_features', False):
                engineered_data = self._create_finops_features(engineered_data)
            
            logger.info(f"Feature engineering completed: {len(data.columns)} -> {len(engineered_data.columns)} features")
            
            return engineered_data
            
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            return data  # Return original data if engineering fails
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model information and metadata
        """
        if model_name not in self.model_metadata:
            return {'error': f'Model {model_name} not found'}
        
        metadata = self.model_metadata[model_name].copy()
        
        # Convert dataclass objects to dictionaries
        if isinstance(metadata.get('metrics'), ModelMetrics):
            metadata['metrics'] = asdict(metadata['metrics'])
        if isinstance(metadata.get('drift_metrics'), DriftMetrics):
            metadata['drift_metrics'] = asdict(metadata['drift_metrics'])
        if isinstance(metadata.get('config'), ModelConfig):
            metadata['config'] = asdict(metadata['config'])
            # Convert enum to string
            if 'model_type' in metadata['config']:
                metadata['config']['model_type'] = metadata['config']['model_type'].value
        
        # Add performance history summary
        if model_name in self.performance_history:
            recent_performance = self.performance_history[model_name][-10:]  # Last 10 measurements
            metadata['recent_performance'] = recent_performance
        
        # Add drift history summary
        if model_name in self.drift_history:
            recent_drift = self.drift_history[model_name][-10:]  # Last 10 measurements
            metadata['recent_drift'] = recent_drift
        
        return metadata
    
    def list_models(self) -> Dict[str, Any]:
        """
        List all available models with their status.
        
        Returns:
            Dictionary of model names and their basic information
        """
        models_info = {}
        
        for model_name, metadata in self.model_metadata.items():
            models_info[model_name] = {
                'status': metadata['status'].value if isinstance(metadata['status'], ModelStatus) else metadata['status'],
                'model_type': metadata['config'].model_type.value if isinstance(metadata['config'], ModelConfig) else 'unknown',
                'created_at': metadata.get('created_at'),
                'trained_at': metadata.get('trained_at'),
                'training_samples': metadata.get('training_samples', 0),
                'feature_count': metadata.get('feature_count', 0)
            }
        
        return {
            'models': models_info,
            'total_models': len(models_info),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def delete_model(self, model_name: str) -> Dict[str, Any]:
        """
        Delete a model and its associated data.
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            Deletion result
        """
        try:
            # Remove from memory
            if model_name in self.models:
                del self.models[model_name]
            if model_name in self.scalers:
                del self.scalers[model_name]
            if model_name in self.encoders:
                del self.encoders[model_name]
            if model_name in self.model_metadata:
                del self.model_metadata[model_name]
            if model_name in self.performance_history:
                del self.performance_history[model_name]
            if model_name in self.drift_history:
                del self.drift_history[model_name]
            
            # Remove from storage
            model_file = self.model_storage_path / f"{model_name}.joblib"
            if model_file.exists():
                model_file.unlink()
            
            metadata_file = self.model_storage_path / f"{model_name}_metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            logger.info(f"Model {model_name} deleted successfully")
            
            return {
                'model_name': model_name,
                'status': 'deleted',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            return {
                'model_name': model_name,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    # Private helper methods
    
    def _create_fallback_model(self, config: ModelConfig) -> Any:
        """Create a simple fallback model when sklearn is not available."""
        logger.warning(f"Creating fallback model for {config.model_name}")
        
        class FallbackModel:
            def __init__(self, model_type):
                self.model_type = model_type
                self.is_fitted = False
                self.mean_value = 0.0
                
            def fit(self, X, y=None):
                if y is not None:
                    self.mean_value = np.mean(y) if hasattr(np, 'mean') else sum(y) / len(y)
                else:
                    self.mean_value = 0.0
                self.is_fitted = True
                return self
                
            def predict(self, X):
                if not self.is_fitted:
                    raise ValueError("Model not fitted")
                n_samples = len(X) if hasattr(X, '__len__') else 1
                return [self.mean_value] * n_samples
        
        return FallbackModel(config.model_type)
    
    def _preprocess_data(self, data: pd.DataFrame, target: pd.Series = None, 
                        model_name: str = "", config: ModelConfig = None, 
                        is_training: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess data for model training or inference."""
        try:
            # Handle missing values
            processed_data = data.fillna(data.mean() if data.select_dtypes(include=[np.number]).shape[1] > 0 else 0)
            
            # Select feature columns if specified
            if config and config.feature_columns:
                available_columns = [col for col in config.feature_columns if col in processed_data.columns]
                if available_columns:
                    processed_data = processed_data[available_columns]
            
            # Encode categorical variables
            categorical_columns = processed_data.select_dtypes(include=['object']).columns
            if len(categorical_columns) > 0:
                if is_training:
                    # Create and store encoders during training
                    if model_name not in self.encoders:
                        self.encoders[model_name] = {}
                    
                    for col in categorical_columns:
                        if SKLEARN_AVAILABLE:
                            encoder = LabelEncoder()
                            processed_data[col] = encoder.fit_transform(processed_data[col].astype(str))
                            self.encoders[model_name][col] = encoder
                        else:
                            # Simple fallback encoding
                            unique_values = processed_data[col].unique()
                            encoding_map = {val: idx for idx, val in enumerate(unique_values)}
                            processed_data[col] = processed_data[col].map(encoding_map)
                            self.encoders[model_name][col] = encoding_map
                else:
                    # Use stored encoders during inference
                    if model_name in self.encoders:
                        for col in categorical_columns:
                            if col in self.encoders[model_name]:
                                encoder = self.encoders[model_name][col]
                                if SKLEARN_AVAILABLE and hasattr(encoder, 'transform'):
                                    processed_data[col] = encoder.transform(processed_data[col].astype(str))
                                elif isinstance(encoder, dict):
                                    processed_data[col] = processed_data[col].map(encoder).fillna(0)
            
            # Scale numerical features
            numerical_columns = processed_data.select_dtypes(include=[np.number]).columns
            if len(numerical_columns) > 0:
                if is_training:
                    # Create and store scaler during training
                    if SKLEARN_AVAILABLE:
                        scaler = StandardScaler()
                        processed_data[numerical_columns] = scaler.fit_transform(processed_data[numerical_columns])
                        self.scalers[model_name] = scaler
                    else:
                        # Simple fallback scaling (z-score normalization)
                        means = processed_data[numerical_columns].mean()
                        stds = processed_data[numerical_columns].std()
                        processed_data[numerical_columns] = (processed_data[numerical_columns] - means) / stds
                        self.scalers[model_name] = {'means': means, 'stds': stds}
                else:
                    # Use stored scaler during inference
                    if model_name in self.scalers:
                        scaler = self.scalers[model_name]
                        if SKLEARN_AVAILABLE and hasattr(scaler, 'transform'):
                            processed_data[numerical_columns] = scaler.transform(processed_data[numerical_columns])
                        elif isinstance(scaler, dict):
                            means = scaler['means']
                            stds = scaler['stds']
                            processed_data[numerical_columns] = (processed_data[numerical_columns] - means) / stds
            
            # Convert to numpy array
            X = processed_data.values
            y = target.values if target is not None else None
            
            return X, y
            
        except Exception as e:
            logger.error(f"Data preprocessing failed: {e}")
            # Return original data as fallback
            return data.values, target.values if target is not None else None
    
    def _validate_model(self, model: Any, X_train: np.ndarray, y_train: np.ndarray,
                       X_val: np.ndarray, y_val: np.ndarray, config: ModelConfig) -> ModelMetrics:
        """Validate model performance."""
        metrics = ModelMetrics()
        
        try:
            if y_train is not None and y_val is not None:
                # Supervised learning validation
                train_predictions = model.predict(X_train)
                val_predictions = model.predict(X_val)
                
                # Calculate metrics
                if SKLEARN_AVAILABLE:
                    metrics.mse = mean_squared_error(y_val, val_predictions)
                    metrics.mae = mean_absolute_error(y_val, val_predictions)
                    metrics.r2_score = r2_score(y_val, val_predictions)
                    
                    # Cross-validation score
                    if len(X_train) > config.cross_validation_folds:
                        cv_scores = cross_val_score(model, X_train, y_train, 
                                                  cv=config.cross_validation_folds, 
                                                  scoring='r2')
                        metrics.cross_val_score = np.mean(cv_scores)
                else:
                    # Fallback metric calculations
                    metrics.mse = self._calculate_mse(y_val, val_predictions)
                    metrics.mae = self._calculate_mae(y_val, val_predictions)
                    metrics.r2_score = self._calculate_r2(y_val, val_predictions)
                    metrics.cross_val_score = metrics.r2_score  # Approximate
            
            # Calculate model size
            try:
                import sys
                if hasattr(model, '__sizeof__'):
                    metrics.model_size_mb = model.__sizeof__() / (1024 * 1024)
                else:
                    metrics.model_size_mb = sys.getsizeof(model) / (1024 * 1024)
            except:
                metrics.model_size_mb = 1.0  # Default estimate
            
        except Exception as e:
            logger.warning(f"Model validation failed: {e}")
        
        return metrics
    
    def _calculate_mse(self, y_true: List[float], y_pred: List[float]) -> float:
        """Calculate Mean Squared Error."""
        if len(y_true) != len(y_pred):
            return float('inf')
        return sum((true - pred) ** 2 for true, pred in zip(y_true, y_pred)) / len(y_true)
    
    def _calculate_mae(self, y_true: List[float], y_pred: List[float]) -> float:
        """Calculate Mean Absolute Error."""
        if len(y_true) != len(y_pred):
            return float('inf')
        return sum(abs(true - pred) for true, pred in zip(y_true, y_pred)) / len(y_true)
    
    def _calculate_r2(self, y_true: List[float], y_pred: List[float]) -> float:
        """Calculate R-squared score."""
        if len(y_true) != len(y_pred) or len(y_true) == 0:
            return 0.0
        
        y_mean = sum(y_true) / len(y_true)
        ss_tot = sum((y - y_mean) ** 2 for y in y_true)
        ss_res = sum((y_true[i] - y_pred[i]) ** 2 for i in range(len(y_true)))
        
        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0
        
        return 1 - (ss_res / ss_tot)
    
    def _calculate_mape(self, y_true: List[float], y_pred: List[float]) -> float:
        """Calculate Mean Absolute Percentage Error."""
        if len(y_true) != len(y_pred) or len(y_true) == 0:
            return float('inf')
        
        ape_sum = 0
        valid_count = 0
        
        for true, pred in zip(y_true, y_pred):
            if true != 0:
                ape_sum += abs((true - pred) / true)
                valid_count += 1
        
        return (ape_sum / valid_count * 100) if valid_count > 0 else float('inf')
    
    def _calculate_drift_metrics(self, new_data: pd.DataFrame, reference_data: pd.DataFrame, 
                                config: ModelConfig) -> DriftMetrics:
        """Calculate drift metrics between new and reference data."""
        drift_metrics = DriftMetrics()
        
        try:
            # Align columns
            common_columns = list(set(new_data.columns) & set(reference_data.columns))
            if not common_columns:
                return drift_metrics
            
            new_subset = new_data[common_columns]
            ref_subset = reference_data[common_columns]
            
            # Calculate feature drift (statistical distance)
            feature_drifts = []
            affected_features = []
            
            for col in common_columns:
                if new_subset[col].dtype in ['int64', 'float64']:
                    # Numerical feature drift (using mean and std comparison)
                    new_mean = new_subset[col].mean()
                    ref_mean = ref_subset[col].mean()
                    new_std = new_subset[col].std()
                    ref_std = ref_subset[col].std()
                    
                    # Normalized difference
                    mean_diff = abs(new_mean - ref_mean) / (ref_std + 1e-8)
                    std_diff = abs(new_std - ref_std) / (ref_std + 1e-8)
                    
                    feature_drift = (mean_diff + std_diff) / 2
                    feature_drifts.append(feature_drift)
                    
                    if feature_drift > 0.5:  # Threshold for significant drift
                        affected_features.append(col)
                else:
                    # Categorical feature drift (distribution comparison)
                    new_dist = new_subset[col].value_counts(normalize=True)
                    ref_dist = ref_subset[col].value_counts(normalize=True)
                    
                    # Calculate distribution difference
                    all_categories = set(new_dist.index) | set(ref_dist.index)
                    drift_sum = 0
                    
                    for cat in all_categories:
                        new_prob = new_dist.get(cat, 0)
                        ref_prob = ref_dist.get(cat, 0)
                        drift_sum += abs(new_prob - ref_prob)
                    
                    feature_drift = drift_sum / 2  # Jensen-Shannon divergence approximation
                    feature_drifts.append(feature_drift)
                    
                    if feature_drift > 0.3:  # Threshold for categorical drift
                        affected_features.append(col)
            
            # Overall feature drift score
            drift_metrics.feature_drift_score = np.mean(feature_drifts) if feature_drifts else 0.0
            drift_metrics.affected_features = affected_features
            
            # Data quality score (completeness and consistency)
            new_completeness = 1 - (new_subset.isnull().sum().sum() / (len(new_subset) * len(common_columns)))
            ref_completeness = 1 - (ref_subset.isnull().sum().sum() / (len(ref_subset) * len(common_columns)))
            
            drift_metrics.data_quality_score = min(new_completeness, ref_completeness)
            
            # Prediction drift score (placeholder - would need actual predictions)
            drift_metrics.prediction_drift_score = drift_metrics.feature_drift_score * 0.8
            
        except Exception as e:
            logger.error(f"Failed to calculate drift metrics: {e}")
        
        return drift_metrics
    
    def _assess_drift_severity(self, drift_metrics: DriftMetrics) -> str:
        """Assess the severity of detected drift."""
        feature_drift = drift_metrics.feature_drift_score
        prediction_drift = drift_metrics.prediction_drift_score
        data_quality = drift_metrics.data_quality_score
        
        # Combine drift scores
        overall_drift = (feature_drift + prediction_drift) / 2
        
        # Adjust for data quality
        if data_quality < 0.8:
            overall_drift *= 1.5  # Amplify drift if data quality is poor
        
        # Determine severity
        if overall_drift < 0.1:
            return "none"
        elif overall_drift < 0.3:
            return "low"
        elif overall_drift < 0.6:
            return "medium"
        else:
            return "high"
    
    def _assess_performance_trend(self, model_name: str) -> Dict[str, Any]:
        """Assess performance trend over time."""
        if model_name not in self.performance_history or len(self.performance_history[model_name]) < 3:
            return {'trend': 'insufficient_data', 'confidence': 'low'}
        
        history = self.performance_history[model_name]
        recent_scores = [entry['r2_score'] for entry in history[-10:]]  # Last 10 measurements
        
        # Simple trend analysis
        if len(recent_scores) >= 3:
            # Linear trend
            x = list(range(len(recent_scores)))
            y = recent_scores
            
            # Calculate slope
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
            
            # Determine trend
            if abs(slope) < 0.01:
                trend = 'stable'
            elif slope > 0:
                trend = 'improving'
            else:
                trend = 'degrading'
            
            # Calculate confidence based on variance
            variance = np.var(recent_scores) if len(recent_scores) > 1 else 0
            confidence = 'high' if variance < 0.01 else 'medium' if variance < 0.05 else 'low'
            
            return {
                'trend': trend,
                'slope': slope,
                'confidence': confidence,
                'recent_average': np.mean(recent_scores),
                'variance': variance
            }
        
        return {'trend': 'insufficient_data', 'confidence': 'low'}
    
    def _create_drift_result(self, model_name: str, drift_metrics: DriftMetrics, 
                           status: str, error: str = None) -> Dict[str, Any]:
        """Create standardized drift detection result."""
        result = {
            'model_name': model_name,
            'status': status,
            'drift_metrics': asdict(drift_metrics),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if error:
            result['error'] = error
        
        return result
    
    def _get_reference_data(self, model_name: str) -> pd.DataFrame:
        """Get reference data for drift detection (placeholder)."""
        # In a real implementation, this would load stored reference data
        logger.warning(f"No reference data implementation for model {model_name}")
        return None
    
    def _create_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features."""
        # Look for datetime columns
        datetime_columns = data.select_dtypes(include=['datetime64']).columns
        
        for col in datetime_columns:
            data[f'{col}_hour'] = data[col].dt.hour
            data[f'{col}_day_of_week'] = data[col].dt.dayofweek
            data[f'{col}_month'] = data[col].dt.month
            data[f'{col}_quarter'] = data[col].dt.quarter
            data[f'{col}_is_weekend'] = (data[col].dt.dayofweek >= 5).astype(int)
        
        return data
    
    def _create_statistical_features(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Create statistical features."""
        numerical_columns = data.select_dtypes(include=[np.number]).columns
        
        if len(numerical_columns) > 1:
            # Rolling statistics if window size is specified
            window_size = config.get('rolling_window', 7)
            
            for col in numerical_columns:
                if len(data) >= window_size:
                    data[f'{col}_rolling_mean'] = data[col].rolling(window=window_size).mean()
                    data[f'{col}_rolling_std'] = data[col].rolling(window=window_size).std()
                    data[f'{col}_rolling_min'] = data[col].rolling(window=window_size).min()
                    data[f'{col}_rolling_max'] = data[col].rolling(window=window_size).max()
        
        return data
    
    def _create_interaction_features(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Create interaction features between numerical columns."""
        numerical_columns = data.select_dtypes(include=[np.number]).columns
        max_interactions = config.get('max_interactions', 5)
        
        interaction_count = 0
        for i, col1 in enumerate(numerical_columns):
            for col2 in numerical_columns[i+1:]:
                if interaction_count >= max_interactions:
                    break
                
                data[f'{col1}_x_{col2}'] = data[col1] * data[col2]
                data[f'{col1}_div_{col2}'] = data[col1] / (data[col2] + 1e-8)  # Avoid division by zero
                interaction_count += 2
        
        return data
    
    def _create_polynomial_features(self, data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Create polynomial features."""
        numerical_columns = data.select_dtypes(include=[np.number]).columns
        degree = config.get('polynomial_degree', 2)
        
        for col in numerical_columns:
            for d in range(2, degree + 1):
                data[f'{col}_pow_{d}'] = data[col] ** d
        
        return data
    
    def _create_finops_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create FinOps-specific features."""
        # Cost efficiency ratios
        if 'cost' in data.columns and 'utilization' in data.columns:
            data['cost_per_utilization'] = data['cost'] / (data['utilization'] + 1e-8)
            data['efficiency_score'] = data['utilization'] / (data['cost'] + 1e-8)
        
        # Usage patterns
        if 'cpu_utilization' in data.columns:
            data['cpu_utilization_category'] = pd.cut(data['cpu_utilization'], 
                                                    bins=[0, 5, 20, 50, 100], 
                                                    labels=['very_low', 'low', 'medium', 'high'])
        
        # Time-based cost patterns
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data['is_business_hours'] = ((data['timestamp'].dt.hour >= 9) & 
                                       (data['timestamp'].dt.hour <= 17) & 
                                       (data['timestamp'].dt.dayofweek < 5)).astype(int)
        
        return data
    
    def _save_model(self, model_name: str, model: Any) -> None:
        """Save model to storage."""
        try:
            if SKLEARN_AVAILABLE:
                model_file = self.model_storage_path / f"{model_name}.joblib"
                joblib.dump(model, model_file)
            else:
                # Fallback: save as pickle
                model_file = self.model_storage_path / f"{model_name}.pkl"
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)
            
            # Save metadata
            metadata_file = self.model_storage_path / f"{model_name}_metadata.json"
            metadata = self.model_metadata[model_name].copy()
            
            # Convert non-serializable objects
            if isinstance(metadata.get('config'), ModelConfig):
                metadata['config'] = asdict(metadata['config'])
                metadata['config']['model_type'] = metadata['config']['model_type'].value
            if isinstance(metadata.get('status'), ModelStatus):
                metadata['status'] = metadata['status'].value
            if isinstance(metadata.get('metrics'), ModelMetrics):
                metadata['metrics'] = asdict(metadata['metrics'])
            if isinstance(metadata.get('drift_metrics'), DriftMetrics):
                metadata['drift_metrics'] = asdict(metadata['drift_metrics'])
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug(f"Model {model_name} saved to {model_file}")
            
        except Exception as e:
            logger.error(f"Failed to save model {model_name}: {e}")
    
    def _load_model(self, model_name: str) -> None:
        """Load model from storage."""
        try:
            # Try joblib first
            model_file = self.model_storage_path / f"{model_name}.joblib"
            if model_file.exists() and SKLEARN_AVAILABLE:
                model = joblib.load(model_file)
            else:
                # Try pickle fallback
                model_file = self.model_storage_path / f"{model_name}.pkl"
                if model_file.exists():
                    with open(model_file, 'rb') as f:
                        model = pickle.load(f)
                else:
                    raise FileNotFoundError(f"Model file not found: {model_name}")
            
            self.models[model_name] = model
            
            # Load metadata
            metadata_file = self.model_storage_path / f"{model_name}_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Convert back to proper types
                if 'config' in metadata and isinstance(metadata['config'], dict):
                    config_dict = metadata['config']
                    config_dict['model_type'] = ModelType(config_dict['model_type'])
                    metadata['config'] = ModelConfig(**config_dict)
                if 'status' in metadata and isinstance(metadata['status'], str):
                    metadata['status'] = ModelStatus(metadata['status'])
                if 'metrics' in metadata and isinstance(metadata['metrics'], dict):
                    metadata['metrics'] = ModelMetrics(**metadata['metrics'])
                if 'drift_metrics' in metadata and isinstance(metadata['drift_metrics'], dict):
                    metadata['drift_metrics'] = DriftMetrics(**metadata['drift_metrics'])
                
                self.model_metadata[model_name] = metadata
            
            logger.debug(f"Model {model_name} loaded from {model_file}")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise


# Convenience functions for easy usage

def create_rightsizing_model(model_name: str = "rightsizing_model") -> Tuple[MLModelManager, ModelConfig]:
    """
    Create a pre-configured model for right-sizing recommendations.
    
    Args:
        model_name: Name for the right-sizing model
        
    Returns:
        Tuple of (MLModelManager instance, ModelConfig)
        
    Requirements: 3.2 - ML-powered right-sizing recommendations
    """
    manager = MLModelManager()
    
    config = ModelConfig(
        model_type=ModelType.REGRESSION,
        model_name=model_name,
        hyperparameters={
            'algorithm': 'random_forest',
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 5
        },
        feature_columns=[
            'cpu_utilization', 'memory_utilization', 'network_utilization',
            'instance_type', 'region', 'cost_per_hour', 'uptime_hours'
        ],
        target_column='optimal_instance_type'
    )
    
    return manager, config


def create_anomaly_detection_model(model_name: str = "cost_anomaly_model") -> Tuple[MLModelManager, ModelConfig]:
    """
    Create a pre-configured model for cost anomaly detection.
    
    Args:
        model_name: Name for the anomaly detection model
        
    Returns:
        Tuple of (MLModelManager instance, ModelConfig)
        
    Requirements: 4.5 - Anomaly detection model drift detection
    """
    manager = MLModelManager()
    
    config = ModelConfig(
        model_type=ModelType.ANOMALY_DETECTION,
        model_name=model_name,
        hyperparameters={
            'n_estimators': 100,
            'contamination': 0.1,
            'max_samples': 'auto'
        },
        feature_columns=[
            'daily_cost', 'service_type', 'region', 'resource_count',
            'utilization_avg', 'cost_per_resource'
        ]
    )
    
    return manager, config


def create_forecasting_model(model_name: str = "cost_forecast_model") -> Tuple[MLModelManager, ModelConfig]:
    """
    Create a pre-configured model for cost forecasting.
    
    Args:
        model_name: Name for the forecasting model
        
    Returns:
        Tuple of (MLModelManager instance, ModelConfig)
        
    Requirements: 3.5 - Cost forecasting with ML models
    """
    manager = MLModelManager()
    
    config = ModelConfig(
        model_type=ModelType.TIME_SERIES,
        model_name=model_name,
        hyperparameters={
            'algorithm': 'random_forest',
            'n_estimators': 150,
            'max_depth': 15
        },
        feature_columns=[
            'historical_cost', 'trend', 'seasonality', 'day_of_week',
            'month', 'resource_changes', 'utilization_trend'
        ],
        target_column='future_cost'
    )
    
    return manager, config


# Example usage and testing functions

def demo_ml_models():
    """Demonstrate ML model utilities functionality."""
    logger.info("Starting ML Models demonstration")
    
    try:
        # Create sample data
        sample_data = pd.DataFrame({
            'cpu_utilization': np.random.uniform(0, 100, 100),
            'memory_utilization': np.random.uniform(0, 100, 100),
            'cost_per_hour': np.random.uniform(0.01, 2.0, 100),
            'instance_type': np.random.choice(['t3.micro', 't3.small', 't3.medium'], 100),
            'region': np.random.choice(['us-east-1', 'us-west-2', 'eu-west-1'], 100)
        })
        
        # Create target variable (optimal instance size based on utilization)
        target = pd.Series(np.where(
            sample_data['cpu_utilization'] < 20, 0,  # Downsize
            np.where(sample_data['cpu_utilization'] > 80, 2, 1)  # Upsize or keep
        ))
        
        # Create and train right-sizing model
        manager, config = create_rightsizing_model()
        
        training_result = manager.train_model(
            model_name=config.model_name,
            training_data=sample_data,
            target_data=target,
            config=config
        )
        
        logger.info(f"Training result: {training_result}")
        
        # Make predictions
        prediction_result = manager.predict(
            model_name=config.model_name,
            input_data=sample_data.head(10)
        )
        
        logger.info(f"Prediction result: {prediction_result}")
        
        # Monitor performance
        actual_values = [0, 1, 2, 1, 0, 1, 2, 0, 1, 2]
        predicted_values = prediction_result['predictions'][:10]
        
        performance_result = manager.monitor_performance(
            model_name=config.model_name,
            actual_values=actual_values,
            predicted_values=predicted_values
        )
        
        logger.info(f"Performance monitoring: {performance_result}")
        
        # Feature engineering demo
        feature_config = {
            'time_features': True,
            'statistical_features': True,
            'finops_features': True,
            'rolling_window': 5
        }
        
        # Add timestamp for time features
        sample_data['timestamp'] = pd.date_range('2024-01-01', periods=100, freq='H')
        
        engineered_data = manager.engineer_features(sample_data, feature_config)
        logger.info(f"Feature engineering: {len(sample_data.columns)} -> {len(engineered_data.columns)} features")
        
        # List models
        models_list = manager.list_models()
        logger.info(f"Available models: {models_list}")
        
        logger.info("ML Models demonstration completed successfully")
        
    except Exception as e:
        logger.error(f"ML Models demonstration failed: {e}")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demonstration
    demo_ml_models()