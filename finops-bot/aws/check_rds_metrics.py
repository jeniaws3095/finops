import boto3
from datetime import datetime, timedelta

def get_rds_instance_metrics(rds_instance):
    """Collect metrics for an RDS instance from CloudWatch"""
    db_instance_id = rds_instance["db_instance_id"]
    region = rds_instance["region"]
    engine = rds_instance["engine"]
    
    cloudwatch = boto3.client("cloudwatch", region_name=region)
    metrics = {}
    
    try:
        # Common RDS metrics
        metric_queries = [
            ("CPUUtilization", "Average"),
            ("DatabaseConnections", "Average"),
            ("ReadLatency", "Average"),
            ("WriteLatency", "Average"),
            ("ReadThroughput", "Average"),
            ("WriteThroughput", "Average"),
            ("FreeableMemory", "Average"),
            ("SwapUsage", "Average"),
            ("DiskQueueDepth", "Average"),
            ("ReadIOPS", "Average"),
            ("WriteIOPS", "Average"),
        ]
        
        dimensions = [{"Name": "DBInstanceIdentifier", "Value": db_instance_id}]
        namespace = "AWS/RDS"
        
        # Collect each metric
        for metric_name, stat in metric_queries:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace=namespace,
                    MetricName=metric_name,
                    Dimensions=dimensions,
                    StartTime=datetime.utcnow() - timedelta(minutes=10),
                    EndTime=datetime.utcnow(),
                    Period=300,
                    Statistics=[stat]
                )
                
                datapoints = response.get("Datapoints", [])
                if datapoints:
                    # Get the most recent datapoint
                    latest = sorted(datapoints, key=lambda x: x["Timestamp"])[-1]
                    metrics[metric_name] = latest[stat]
                else:
                    metrics[metric_name] = 0.0
            
            except Exception as e:
                print(f"⚠️ Error collecting {metric_name} for {db_instance_id}: {e}")
                metrics[metric_name] = 0.0
        
        # Calculate utilization metrics
        cpu = metrics.get("CPUUtilization", 0)
        connections = metrics.get("DatabaseConnections", 0)
        memory = metrics.get("FreeableMemory", 0)
        
        # Estimate memory utilization (assuming 8GB default, varies by instance class)
        # This is approximate - actual memory depends on instance class
        total_memory_bytes = 8 * 1024 * 1024 * 1024  # 8GB default
        memory_utilization = ((total_memory_bytes - memory) / total_memory_bytes * 100) if memory >= 0 else 0
        
        metrics["MemoryUtilizationPercent"] = round(memory_utilization, 2)
        metrics["TotalConnections"] = connections
        metrics["CPUUtilizationPercent"] = cpu
        
        return metrics
    
    except Exception as e:
        print(f"❌ Error collecting metrics for RDS instance {db_instance_id}: {e}")
        return {}


def is_rds_underutilized(rds_instance, metrics):
    """Determine if an RDS instance is underutilized"""
    # Instance is underutilized if:
    # 1. CPU < 5% for extended period
    # 2. Very few database connections (< 5)
    # 3. Status is available/stopped
    
    status = rds_instance["status"]
    
    if status in ["stopped", "stopping", "deleting"]:
        return True
    
    cpu = metrics.get("CPUUtilization", 0)
    connections = metrics.get("DatabaseConnections", 0)
    
    if cpu < 5 and connections < 5:
        return True
    
    return False
