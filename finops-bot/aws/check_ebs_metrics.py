import boto3
from datetime import datetime, timedelta

def get_ebs_volume_metrics(volume):
    """Collect metrics for an EBS volume from CloudWatch"""
    volume_id = volume["volume_id"]
    region = volume["region"]
    
    cloudwatch = boto3.client("cloudwatch", region_name=region)
    metrics = {}
    
    try:
        # EBS volume metrics
        metric_queries = [
            ("VolumeReadBytes", "Sum"),
            ("VolumeWriteBytes", "Sum"),
            ("VolumeReadOps", "Sum"),
            ("VolumeWriteOps", "Sum"),
            ("VolumeThroughputPercentage", "Average"),
            ("VolumeConsumedReadWriteOps", "Sum"),
        ]
        
        dimensions = [{"Name": "VolumeId", "Value": volume_id}]
        namespace = "AWS/EBS"
        
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
                print(f"⚠️ Error collecting {metric_name} for {volume_id}: {e}")
                metrics[metric_name] = 0.0
        
        # Calculate utilization metrics
        total_read_bytes = metrics.get("VolumeReadBytes", 0)
        total_write_bytes = metrics.get("VolumeWriteBytes", 0)
        total_bytes = total_read_bytes + total_write_bytes
        
        # Calculate I/O operations per second (approximate)
        read_ops = metrics.get("VolumeReadOps", 0)
        write_ops = metrics.get("VolumeWriteOps", 0)
        total_ops = read_ops + write_ops
        
        # Estimate IOPS (operations per 10 minutes / 600 seconds)
        estimated_iops = total_ops / 600 if total_ops > 0 else 0
        
        metrics["TotalBytesTransferred"] = total_bytes
        metrics["EstimatedIOPS"] = round(estimated_iops, 2)
        metrics["ReadWriteRatio"] = (
            (total_read_bytes / total_bytes * 100) if total_bytes > 0 else 0
        )
        
        return metrics
    
    except Exception as e:
        print(f"❌ Error collecting metrics for volume {volume_id}: {e}")
        return {}


def is_volume_unused(volume, metrics):
    """Determine if an EBS volume is unused/underutilized"""
    # Volume is unused if:
    # 1. Not attached to any instance
    # 2. No read/write activity in last 10 minutes
    # 3. State is available (not in-use)
    
    if volume["state"] == "available":
        return True
    
    if volume["attached_instance_id"] is None:
        return True
    
    total_ops = metrics.get("VolumeReadOps", 0) + metrics.get("VolumeWriteOps", 0)
    if total_ops == 0:
        return True
    
    return False
