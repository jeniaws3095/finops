#!/usr/bin/env python3
"""
Basic test for ML Models utilities without external dependencies.

Tests the basic structure and functionality that doesn't require pandas/sklearn.
"""

import unittest
import tempfile
import shutil
import sys
import os
from pathlib import Path

# Add project root to path (for standalone run)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

try:
    from utils.ml_models import (
        ModelType, ModelStatus, ModelMetrics, DriftMetrics, ModelConfig
    )
    ML_MODELS_AVAILABLE = True
except ImportError as e:
    print(f"ML models import failed: {e}")
    ML_MODELS_AVAILABLE = False


class TestMLModelsBasic(unittest.TestCase):
    """Basic test cases for ML model utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @unittest.skipUnless(ML_MODELS_AVAILABLE, "ML models not available")
    def test_model_enums(self):
        """Test model enums and constants."""
        # Test ModelType enum
        self.assertEqual(ModelType.REGRESSION.value, "regression")
        self.assertEqual(ModelType.CLASSIFICATION.value, "classification")
        self.assertEqual(ModelType.CLUSTERING.value, "clustering")
        self.assertEqual(ModelType.ANOMALY_DETECTION.value, "anomaly_detection")
        self.assertEqual(ModelType.TIME_SERIES.value, "time_series")
        
        # Test ModelStatus enum
        self.assertEqual(ModelStatus.TRAINING.value, "training")
        self.assertEqual(ModelStatus.TRAINED.value, "trained")
        self.assertEqual(ModelStatus.VALIDATED.value, "validated")
        self.assertEqual(ModelStatus.DEPLOYED.value, "deployed")
        self.assertEqual(ModelStatus.DEPRECATED.value, "deprecated")
        self.assertEqual(ModelStatus.FAILED.value, "failed")
    
    @unittest.skipUnless(ML_MODELS_AVAILABLE, "ML models not available")
    def test_model_metrics_dataclass(self):
        """Test ModelMetrics dataclass."""
        metrics = ModelMetrics()
        
        # Test default values
        self.assertEqual(metrics.accuracy, 0.0)
        self.assertEqual(metrics.precision, 0.0)
        self.assertEqual(metrics.recall, 0.0)
        self.assertEqual(metrics.f1_score, 0.0)
        self.assertEqual(metrics.mse, 0.0)
        self.assertEqual(metrics.mae, 0.0)
        self.assertEqual(metrics.r2_score, 0.0)
        self.assertEqual(metrics.cross_val_score, 0.0)
        self.assertEqual(metrics.training_time, 0.0)
        self.assertEqual(metrics.inference_time, 0.0)
        self.assertEqual(metrics.model_size_mb, 0.0)
        
        # Test custom values
        custom_metrics = ModelMetrics(
            accuracy=0.95,
            mse=0.1,
            training_time=120.5
        )
        self.assertEqual(custom_metrics.accuracy, 0.95)
        self.assertEqual(custom_metrics.mse, 0.1)
        self.assertEqual(custom_metrics.training_time, 120.5)
    
    @unittest.skipUnless(ML_MODELS_AVAILABLE, "ML models not available")
    def test_drift_metrics_dataclass(self):
        """Test DriftMetrics dataclass."""
        drift_metrics = DriftMetrics()
        
        # Test default values
        self.assertEqual(drift_metrics.feature_drift_score, 0.0)
        self.assertEqual(drift_metrics.prediction_drift_score, 0.0)
        self.assertEqual(drift_metrics.data_quality_score, 0.0)
        self.assertEqual(drift_metrics.drift_detected, False)
        self.assertEqual(drift_metrics.drift_severity, "none")
        self.assertEqual(drift_metrics.affected_features, [])
        
        # Test custom values
        custom_drift = DriftMetrics(
            feature_drift_score=0.7,
            drift_detected=True,
            drift_severity="high",
            affected_features=["feature1", "feature2"]
        )
        self.assertEqual(custom_drift.feature_drift_score, 0.7)
        self.assertTrue(custom_drift.drift_detected)
        self.assertEqual(custom_drift.drift_severity, "high")
        self.assertEqual(len(custom_drift.affected_features), 2)
    
    @unittest.skipUnless(ML_MODELS_AVAILABLE, "ML models not available")
    def test_model_config_dataclass(self):
        """Test ModelConfig dataclass."""
        config = ModelConfig(
            model_type=ModelType.REGRESSION,
            model_name="test_model"
        )
        
        # Test required fields
        self.assertEqual(config.model_type, ModelType.REGRESSION)
        self.assertEqual(config.model_name, "test_model")
        
        # Test default values
        self.assertEqual(config.version, "1.0.0")
        self.assertEqual(config.hyperparameters, {})
        self.assertEqual(config.feature_columns, [])
        self.assertEqual(config.target_column, "")
        self.assertEqual(config.validation_split, 0.2)
        self.assertEqual(config.test_split, 0.1)
        self.assertEqual(config.cross_validation_folds, 5)
        self.assertEqual(config.random_state, 42)
        
        # Test custom values
        custom_config = ModelConfig(
            model_type=ModelType.ANOMALY_DETECTION,
            model_name="anomaly_model",
            version="2.0.0",
            hyperparameters={"n_estimators": 100},
            feature_columns=["cpu", "memory"],
            target_column="anomaly",
            validation_split=0.3
        )
        self.assertEqual(custom_config.model_type, ModelType.ANOMALY_DETECTION)
        self.assertEqual(custom_config.version, "2.0.0")
        self.assertEqual(custom_config.hyperparameters["n_estimators"], 100)
        self.assertEqual(len(custom_config.feature_columns), 2)
        self.assertEqual(custom_config.target_column, "anomaly")
        self.assertEqual(custom_config.validation_split, 0.3)
    
    def test_import_structure(self):
        """Test that the module structure is correct."""
        if not ML_MODELS_AVAILABLE:
            self.skipTest("ML models not available")
        
        # Test that we can import the main classes
        from utils.ml_models import (
            MLModelManager, ModelConfig, ModelType, ModelStatus, 
            ModelMetrics, DriftMetrics
        )
        
        # Test that convenience functions are available
        from utils.ml_models import (
            create_rightsizing_model, create_anomaly_detection_model, 
            create_forecasting_model
        )
        
        # All imports successful
        self.assertTrue(True)
    
    def test_file_structure(self):
        """Test that the ML models file exists and has the right structure."""
        ml_models_path = Path(__file__).parent / "utils" / "ml_models.py"
        self.assertTrue(ml_models_path.exists(), "ml_models.py file should exist")
        
        # Read the file and check for key components
        with open(ml_models_path, 'r') as f:
            content = f.read()
        
        # Check for key classes and functions
        self.assertIn("class MLModelManager", content)
        self.assertIn("class ModelType", content)
        self.assertIn("class ModelStatus", content)
        self.assertIn("class ModelMetrics", content)
        self.assertIn("class DriftMetrics", content)
        self.assertIn("class ModelConfig", content)
        
        # Check for key methods
        self.assertIn("def create_model", content)
        self.assertIn("def train_model", content)
        self.assertIn("def predict", content)
        self.assertIn("def detect_drift", content)
        self.assertIn("def monitor_performance", content)
        self.assertIn("def engineer_features", content)
        
        # Check for convenience functions
        self.assertIn("def create_rightsizing_model", content)
        self.assertIn("def create_anomaly_detection_model", content)
        self.assertIn("def create_forecasting_model", content)
        
        # Check for requirements comments
        self.assertIn("Requirements: 3.2", content)
        self.assertIn("Requirements: 3.5", content)
        self.assertIn("Requirements: 4.5", content)


if __name__ == '__main__':
    print("Running basic ML models tests...")
    print(f"ML models available: {ML_MODELS_AVAILABLE}")
    
    # Run the tests
    unittest.main(verbosity=2)