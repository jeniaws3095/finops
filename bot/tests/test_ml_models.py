#!/usr/bin/env python3
"""
Unit tests for ML Models utilities.

Tests the machine learning model management functionality including:
- Model creation and configuration
- Training and validation
- Prediction and inference
- Feature engineering
- Performance monitoring
- Drift detection
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from utils.ml_models import (
    MLModelManager, ModelConfig, ModelType, ModelStatus, ModelMetrics, DriftMetrics,
    create_rightsizing_model, create_anomaly_detection_model, create_forecasting_model
)


class TestMLModels(unittest.TestCase):
    """Test cases for ML model utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for model storage
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MLModelManager(model_storage_path=self.temp_dir)
        
        # Create sample data
        np.random.seed(42)  # For reproducible tests
        self.sample_data = pd.DataFrame({
            'cpu_utilization': np.random.uniform(0, 100, 50),
            'memory_utilization': np.random.uniform(0, 100, 50),
            'cost_per_hour': np.random.uniform(0.01, 2.0, 50),
            'instance_type': np.random.choice(['t3.micro', 't3.small', 't3.medium'], 50),
            'region': np.random.choice(['us-east-1', 'us-west-2'], 50)
        })
        
        # Create target variable
        self.target_data = pd.Series(np.where(
            self.sample_data['cpu_utilization'] < 30, 0,  # Downsize
            np.where(self.sample_data['cpu_utilization'] > 70, 2, 1)  # Upsize or keep
        ))
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_model_creation(self):
        """Test model creation with different configurations."""
        config = ModelConfig(
            model_type=ModelType.REGRESSION,
            model_name="test_model",
            hyperparameters={'n_estimators': 50}
        )
        
        model = self.manager.create_model(config)
        self.assertIsNotNone(model)
        self.assertIn("test_model", self.manager.model_metadata)
        
        metadata = self.manager.model_metadata["test_model"]
        self.assertEqual(metadata['status'], ModelStatus.TRAINING)
        self.assertEqual(metadata['config'].model_name, "test_model")
    
    def test_model_training(self):
        """Test model training functionality."""
        config = ModelConfig(
            model_type=ModelType.REGRESSION,
            model_name="training_test",
            feature_columns=['cpu_utilization', 'memory_utilization', 'cost_per_hour'],
            target_column='optimal_size'
        )
        
        result = self.manager.train_model(
            model_name="training_test",
            training_data=self.sample_data,
            target_data=self.target_data,
            config=config
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('training_time', result)
        self.assertIn('metrics', result)
        self.assertGreater(result['training_samples'], 0)
        
        # Check model metadata was updated
        metadata = self.manager.model_metadata["training_test"]
        self.assertEqual(metadata['status'], ModelStatus.TRAINED)
        self.assertIn('trained_at', metadata)
    
    def test_model_prediction(self):
        """Test model prediction functionality."""
        # First train a model
        config = ModelConfig(
            model_type=ModelType.REGRESSION,
            model_name="prediction_test",
            feature_columns=['cpu_utilization', 'memory_utilization']
        )
        
        self.manager.train_model(
            model_name="prediction_test",
            training_data=self.sample_data,
            target_data=self.target_data,
            config=config
        )
        
        # Make predictions
        test_data = self.sample_data.head(5)
        result = self.manager.predict(
            model_name="prediction_test",
            input_data=test_data
        )
        
        self.assertIn('predictions', result)
        self.assertEqual(len(result['predictions']), 5)
        self.assertIn('inference_time', result)
        self.assertGreater(result['inference_time'], 0)
    
    def test_feature_engineering(self):
        """Test feature engineering functionality."""
        # Add timestamp for time features
        data_with_time = self.sample_data.copy()
        data_with_time['timestamp'] = pd.date_range('2024-01-01', periods=len(data_with_time), freq='H')
        data_with_time['cost'] = data_with_time['cost_per_hour']
        data_with_time['utilization'] = data_with_time['cpu_utilization']
        
        feature_config = {
            'time_features': True,
            'statistical_features': True,
            'finops_features': True,
            'rolling_window': 5
        }
        
        engineered_data = self.manager.engineer_features(data_with_time, feature_config)
        
        # Check that new features were created
        self.assertGreater(len(engineered_data.columns), len(data_with_time.columns))
        
        # Check for specific time features
        time_feature_columns = [col for col in engineered_data.columns if 'timestamp_' in col]
        self.assertGreater(len(time_feature_columns), 0)
        
        # Check for FinOps features
        self.assertIn('cost_per_utilization', engineered_data.columns)
        self.assertIn('efficiency_score', engineered_data.columns)
    
    def test_performance_monitoring(self):
        """Test performance monitoring functionality."""
        # Create some sample actual vs predicted values
        actual_values = [0, 1, 2, 1, 0, 1, 2, 0, 1, 2]
        predicted_values = [0, 1, 1, 1, 0, 2, 2, 0, 1, 1]
        
        result = self.manager.monitor_performance(
            model_name="test_performance",
            actual_values=actual_values,
            predicted_values=predicted_values
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('current_metrics', result)
        self.assertIn('mse', result['current_metrics'])
        self.assertIn('mae', result['current_metrics'])
        self.assertIn('r2_score', result['current_metrics'])
        
        # Check that performance history was stored
        self.assertIn("test_performance", self.manager.performance_history)
    
    def test_drift_detection(self):
        """Test drift detection functionality."""
        # Create reference and new data with some drift
        reference_data = pd.DataFrame({
            'feature1': np.random.normal(0, 1, 100),
            'feature2': np.random.normal(5, 2, 100)
        })
        
        # New data with drift (different mean)
        new_data = pd.DataFrame({
            'feature1': np.random.normal(2, 1, 100),  # Mean shifted
            'feature2': np.random.normal(5, 2, 100)   # No drift
        })
        
        # Create a dummy model config
        config = ModelConfig(
            model_type=ModelType.REGRESSION,
            model_name="drift_test"
        )
        self.manager.model_metadata["drift_test"] = {
            'config': config,
            'status': ModelStatus.TRAINED
        }
        
        result = self.manager.detect_drift(
            model_name="drift_test",
            new_data=new_data,
            reference_data=reference_data
        )
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('drift_metrics', result)
        self.assertIn('feature_drift_score', result['drift_metrics'])
        self.assertGreater(result['drift_metrics']['feature_drift_score'], 0)
    
    def test_model_info_and_listing(self):
        """Test model information retrieval and listing."""
        # Create and train a model
        config = ModelConfig(
            model_type=ModelType.REGRESSION,
            model_name="info_test"
        )
        
        self.manager.train_model(
            model_name="info_test",
            training_data=self.sample_data,
            target_data=self.target_data,
            config=config
        )
        
        # Test get_model_info
        info = self.manager.get_model_info("info_test")
        self.assertIn('config', info)
        self.assertIn('status', info)
        self.assertIn('metrics', info)
        
        # Test list_models
        models_list = self.manager.list_models()
        self.assertIn('models', models_list)
        self.assertIn('total_models', models_list)
        self.assertIn("info_test", models_list['models'])
    
    def test_convenience_functions(self):
        """Test convenience functions for creating pre-configured models."""
        # Test rightsizing model creation
        manager, config = create_rightsizing_model("test_rightsizing")
        self.assertIsInstance(manager, MLModelManager)
        self.assertIsInstance(config, ModelConfig)
        self.assertEqual(config.model_type, ModelType.REGRESSION)
        self.assertEqual(config.model_name, "test_rightsizing")
        
        # Test anomaly detection model creation
        manager, config = create_anomaly_detection_model("test_anomaly")
        self.assertEqual(config.model_type, ModelType.ANOMALY_DETECTION)
        self.assertEqual(config.model_name, "test_anomaly")
        
        # Test forecasting model creation
        manager, config = create_forecasting_model("test_forecast")
        self.assertEqual(config.model_type, ModelType.TIME_SERIES)
        self.assertEqual(config.model_name, "test_forecast")
    
    def test_model_deletion(self):
        """Test model deletion functionality."""
        # Create and train a model
        config = ModelConfig(
            model_type=ModelType.REGRESSION,
            model_name="delete_test"
        )
        
        self.manager.train_model(
            model_name="delete_test",
            training_data=self.sample_data,
            target_data=self.target_data,
            config=config
        )
        
        # Verify model exists
        self.assertIn("delete_test", self.manager.model_metadata)
        
        # Delete model
        result = self.manager.delete_model("delete_test")
        self.assertEqual(result['status'], 'deleted')
        
        # Verify model was removed
        self.assertNotIn("delete_test", self.manager.model_metadata)
        self.assertNotIn("delete_test", self.manager.models)
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test prediction with non-existent model
        result = self.manager.predict(
            model_name="non_existent",
            input_data=self.sample_data.head(5)
        )
        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result)
        
        # Test performance monitoring with mismatched arrays
        result = self.manager.monitor_performance(
            model_name="test",
            actual_values=[1, 2, 3],
            predicted_values=[1, 2]  # Different length
        )
        self.assertEqual(result['status'], 'failed')
        
        # Test drift detection with non-existent model
        result = self.manager.detect_drift(
            model_name="non_existent",
            new_data=self.sample_data
        )
        self.assertEqual(result['status'], 'failed')


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)