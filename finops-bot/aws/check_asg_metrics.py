import boto3
from datetime import datetime, timedelta

def get_asg_metrics(asg):
    """Collect metrics for an Auto Scaling Group from CloudWatch"""
    asg_name = asg["asg_name"]
    region = asg["region"]
    
    cloudwatch = boto3.client("cloudwatch", region_name=region)
    metrics = {}
    
    try:
        # ASG-specific metrics
        metric_queries = [
            ("GroupMinSize", "Average"),
            ("GroupMaxSize", "Average"),
            ("GroupDesiredCapacity", "Average"),
            ("GroupInServiceInstances", "Average"),
            ("GroupPendingInstances", "Average"),
            ("GroupTerminatingInstances", "Average"),
            ("GroupTotalInstances", "Average"),
        ]
        
        dimensions = [{"Name": "AutoScalingGroupName", "Value": asg_name}]
        namespace = "AWS/AutoScaling"
        
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
                print(f"⚠️ Error collecting {metric_name} for ASG {asg_name}: {e}")
                metrics[metric_name] = 0.0
        
        # Calculate utilization metrics
        total_instances = metrics.get("GroupTotalInstances", 0)
        in_service = metrics.get("GroupInServiceInstances", 0)
        
        if total_instances > 0:
            metrics["InstanceUtilizationPercent"] = (in_service / total_instances) * 100
        else:
            metrics["InstanceUtilizationPercent"] = 0.0
        
        # Calculate capacity utilization
        desired = metrics.get("GroupDesiredCapacity", 0)
        max_size = metrics.get("GroupMaxSize", 1)
        
        if max_size > 0:
            metrics["CapacityUtilizationPercent"] = (desired / max_size) * 100
        else:
            metrics["CapacityUtilizationPercent"] = 0.0
        
        return metrics
    
    except Exception as e:
        print(f"❌ Error collecting metrics for ASG {asg_name}: {e}")
        return {}
