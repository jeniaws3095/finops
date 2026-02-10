import boto3
from datetime import datetime, timedelta

def get_load_balancer_metrics(load_balancer):
    """Collect metrics for a load balancer from CloudWatch"""
    lb_name = load_balancer["load_balancer_name"]
    lb_type = load_balancer["load_balancer_type"]
    region = load_balancer["region"]
    
    cloudwatch = boto3.client("cloudwatch", region_name=region)
    metrics = {}
    
    try:
        # Common metrics for all load balancer types
        metric_queries = [
            ("RequestCount", "Sum"),
            ("TargetResponseTime", "Average"),
            ("HTTPCode_Target_2XX_Count", "Sum"),
            ("HTTPCode_Target_4XX_Count", "Sum"),
            ("HTTPCode_Target_5XX_Count", "Sum"),
            ("UnHealthyHostCount", "Average"),
            ("HealthyHostCount", "Average"),
        ]
        
        # Type-specific metrics
        if lb_type == "application":
            metric_queries.extend([
                ("ActiveConnectionCount", "Sum"),
                ("ProcessedBytes", "Sum"),
            ])
        elif lb_type == "network":
            metric_queries.extend([
                ("ActiveFlowCount", "Sum"),
                ("NewFlowCount", "Sum"),
                ("ProcessedBytes", "Sum"),
            ])
        
        # Determine dimension based on LB type
        if lb_type == "classic":
            dimensions = [{"Name": "LoadBalancerName", "Value": lb_name}]
            namespace = "AWS/ELB"
        else:
            # For ALB/NLB, use LoadBalancer dimension
            lb_arn_parts = load_balancer["load_balancer_arn"].split(":")
            lb_resource = lb_arn_parts[-1]  # app/name/id or net/name/id
            dimensions = [{"Name": "LoadBalancer", "Value": lb_resource}]
            namespace = "AWS/ApplicationELB" if lb_type == "application" else "AWS/NetworkELB"
        
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
                print(f"⚠️ Error collecting {metric_name} for {lb_name}: {e}")
                metrics[metric_name] = 0.0
        
        return metrics
    
    except Exception as e:
        print(f"❌ Error collecting metrics for load balancer {lb_name}: {e}")
        return {}
