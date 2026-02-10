from typing import Dict, Any, List
from utils.pricing import get_rds_total_cost

class RDSRecommendation:
    """Generate optimization recommendations for RDS instances"""
    
    @staticmethod
    def analyze_rds_metrics(db_instance_id: str, db_instance_class: str, 
                           storage_type: str, allocated_storage_gb: int,
                           region: str, cpu: float, connections: int,
                           multi_az: bool = False) -> Dict[str, Any]:
        """
        Analyze RDS metrics and generate optimization recommendations.
        
        Args:
            db_instance_id: RDS instance identifier
            db_instance_class: Current instance class (e.g., 'db.t3.large')
            storage_type: Storage type (gp2, gp3, io1, io2)
            allocated_storage_gb: Allocated storage in GB
            region: AWS region
            cpu: CPU utilization percentage (0-100)
            connections: Number of active database connections
            multi_az: Whether Multi-AZ is enabled
        
        Returns:
            dict: Recommendation with action, reasoning, and estimated savings
        """
        
        current_cost = get_rds_total_cost(
            db_instance_class, storage_type, allocated_storage_gb, region, multi_az
        )
        current_monthly_cost = current_cost["total_monthly"]
        
        # Determine recommendation based on metrics
        if cpu < 2.0 and connections < 2:
            # Severely underutilized - recommend deletion
            recommendation = {
                "action": "delete",
                "confidence": 95,
                "reasoning": f"RDS instance is severely underutilized (CPU: {cpu}%, Connections: {connections})",
                "estimated_monthly_savings": current_monthly_cost,
                "estimated_annual_savings": current_monthly_cost * 12,
                "risk_level": "high",
                "risk_description": "Data loss if not backed up. Ensure final snapshot is created.",
                "alternative_actions": [
                    {
                        "action": "stop",
                        "description": "Stop the instance instead of deleting (can be restarted later)",
                        "estimated_savings": current_monthly_cost * 0.9  # Stopped instances still incur some costs
                    },
                    {
                        "action": "resize",
                        "description": "Downsize to smaller instance class",
                        "estimated_savings": current_monthly_cost * 0.3
                    }
                ]
            }
        
        elif cpu < 5.0 and connections < 5:
            # Moderately underutilized - recommend resize
            downsized_class = RDSRecommendation._get_downsized_class(db_instance_class)
            
            if downsized_class:
                downsized_cost = get_rds_total_cost(
                    downsized_class, storage_type, allocated_storage_gb, region, multi_az
                )
                downsized_monthly_cost = downsized_cost["total_monthly"]
                savings = current_monthly_cost - downsized_monthly_cost
                
                recommendation = {
                    "action": "resize",
                    "confidence": 85,
                    "reasoning": f"RDS instance is underutilized (CPU: {cpu}%, Connections: {connections}). Can be downsized.",
                    "current_instance_class": db_instance_class,
                    "recommended_instance_class": downsized_class,
                    "estimated_monthly_savings": savings,
                    "estimated_annual_savings": savings * 12,
                    "risk_level": "low",
                    "risk_description": "Brief downtime during maintenance window. No data loss.",
                    "alternative_actions": [
                        {
                            "action": "stop",
                            "description": "Stop the instance if not needed",
                            "estimated_savings": current_monthly_cost * 0.9
                        },
                        {
                            "action": "delete",
                            "description": "Delete if instance is no longer needed",
                            "estimated_savings": current_monthly_cost
                        }
                    ]
                }
            else:
                # Already at smallest class
                recommendation = {
                    "action": "stop",
                    "confidence": 80,
                    "reasoning": f"RDS instance is underutilized (CPU: {cpu}%, Connections: {connections}). Already at smallest instance class.",
                    "estimated_monthly_savings": current_monthly_cost * 0.9,
                    "estimated_annual_savings": current_monthly_cost * 0.9 * 12,
                    "risk_level": "medium",
                    "risk_description": "Instance will be stopped but can be restarted. Stopped instances still incur storage costs.",
                    "alternative_actions": [
                        {
                            "action": "delete",
                            "description": "Delete if instance is no longer needed",
                            "estimated_savings": current_monthly_cost
                        }
                    ]
                }
        
        elif cpu < 10.0 and connections < 10:
            # Slightly underutilized - recommend monitoring
            recommendation = {
                "action": "monitor",
                "confidence": 60,
                "reasoning": f"RDS instance shows slight underutilization (CPU: {cpu}%, Connections: {connections}). Monitor for trends.",
                "estimated_monthly_savings": 0,
                "estimated_annual_savings": 0,
                "risk_level": "low",
                "risk_description": "No action recommended at this time. Continue monitoring.",
                "alternative_actions": [
                    {
                        "action": "resize",
                        "description": "Downsize if underutilization persists",
                        "estimated_savings": current_monthly_cost * 0.2
                    }
                ]
            }
        
        else:
            # Well-utilized - no action needed
            recommendation = {
                "action": "none",
                "confidence": 100,
                "reasoning": f"RDS instance is well-utilized (CPU: {cpu}%, Connections: {connections}). No optimization needed.",
                "estimated_monthly_savings": 0,
                "estimated_annual_savings": 0,
                "risk_level": "none",
                "risk_description": "Instance is operating normally.",
                "alternative_actions": []
            }
        
        # Add common metadata
        recommendation.update({
            "db_instance_id": db_instance_id,
            "db_instance_class": db_instance_class,
            "current_monthly_cost": current_monthly_cost,
            "current_annual_cost": current_monthly_cost * 12,
            "metrics": {
                "cpu_utilization": cpu,
                "active_connections": connections
            }
        })
        
        return recommendation
    
    @staticmethod
    def _get_downsized_class(current_class: str) -> str:
        """
        Get the next smaller RDS instance class.
        
        Args:
            current_class: Current instance class (e.g., 'db.t3.large')
        
        Returns:
            str: Downsized instance class, or None if already at smallest
        """
        # Downsizing hierarchy for common instance families
        downsizing_map = {
            # t3 family
            "db.t3.2xlarge": "db.t3.xlarge",
            "db.t3.xlarge": "db.t3.large",
            "db.t3.large": "db.t3.medium",
            "db.t3.medium": "db.t3.small",
            "db.t3.small": "db.t3.micro",
            
            # t2 family
            "db.t2.2xlarge": "db.t2.xlarge",
            "db.t2.xlarge": "db.t2.large",
            "db.t2.large": "db.t2.medium",
            "db.t2.medium": "db.t2.small",
            "db.t2.small": "db.t2.micro",
            
            # m5 family
            "db.m5.2xlarge": "db.m5.xlarge",
            "db.m5.xlarge": "db.m5.large",
            "db.m5.large": "db.m5.large",  # Can't downsize further in m5
            
            # r5 family (memory optimized)
            "db.r5.2xlarge": "db.r5.xlarge",
            "db.r5.xlarge": "db.r5.large",
            "db.r5.large": "db.r5.large",  # Can't downsize further in r5
        }
        
        return downsizing_map.get(current_class)
    
    @staticmethod
    def format_recommendation(recommendation: Dict[str, Any]) -> str:
        """
        Format recommendation as human-readable text.
        
        Args:
            recommendation: Recommendation dictionary
        
        Returns:
            str: Formatted recommendation text
        """
        action = recommendation.get("action", "none").upper()
        confidence = recommendation.get("confidence", 0)
        reasoning = recommendation.get("reasoning", "")
        savings = recommendation.get("estimated_monthly_savings", 0)
        annual_savings = recommendation.get("estimated_annual_savings", 0)
        risk = recommendation.get("risk_level", "none").upper()
        
        text = f"""
╔════════════════════════════════════════════════════════════════╗
║                  RDS OPTIMIZATION RECOMMENDATION               ║
╚════════════════════════════════════════════════════════════════╝

📊 RECOMMENDATION: {action}
   Confidence: {confidence}%
   Risk Level: {risk}

💡 REASONING:
   {reasoning}

💰 ESTIMATED SAVINGS:
   Monthly: ${savings:.2f}
   Annual: ${annual_savings:.2f}

⚠️  RISK DESCRIPTION:
   {recommendation.get('risk_description', 'N/A')}
"""
        
        # Add alternative actions if available
        alternatives = recommendation.get("alternative_actions", [])
        if alternatives:
            text += "\n🔄 ALTERNATIVE ACTIONS:\n"
            for alt in alternatives:
                alt_savings = alt.get("estimated_savings", 0)
                text += f"   • {alt['action'].upper()}: {alt['description']}\n"
                text += f"     Estimated Savings: ${alt_savings:.2f}/month\n"
        
        text += "\n" + "="*64 + "\n"
        
        return text


class EC2Recommendation:
    """Generate optimization recommendations for EC2 instances"""
    
    @staticmethod
    def analyze_ec2_metrics(instance_id: str, instance_type: str, region: str,
                           cpu: float, network_in_bytes: float, 
                           network_out_bytes: float) -> Dict[str, Any]:
        """
        Analyze EC2 metrics and generate optimization recommendations.
        
        Args:
            instance_id: EC2 instance identifier
            instance_type: Instance type (e.g., 't2.large')
            region: AWS region
            cpu: CPU utilization percentage (0-100)
            network_in_bytes: Network inbound bytes
            network_out_bytes: Network outbound bytes
        
        Returns:
            dict: Recommendation with action, reasoning, and estimated savings
        """
        from utils.pricing import get_instance_hourly_cost, calculate_monthly_cost
        
        hourly_cost = get_instance_hourly_cost(instance_type, region)
        monthly_cost = calculate_monthly_cost(hourly_cost)
        
        if cpu < 2.0 and network_in_bytes < 1000 and network_out_bytes < 1000:
            # Severely underutilized
            recommendation = {
                "action": "stop",
                "confidence": 90,
                "reasoning": f"EC2 instance is severely underutilized (CPU: {cpu}%, Network: minimal)",
                "estimated_monthly_savings": monthly_cost,
                "estimated_annual_savings": monthly_cost * 12,
                "risk_level": "low",
                "risk_description": "Instance can be restarted when needed."
            }
        
        elif cpu < 5.0:
            # Moderately underutilized - suggest resize
            downsized_type = EC2Recommendation._get_downsized_instance_type(instance_type)
            
            if downsized_type:
                downsized_hourly = get_instance_hourly_cost(downsized_type, region)
                downsized_monthly = calculate_monthly_cost(downsized_hourly)
                savings = monthly_cost - downsized_monthly
                
                recommendation = {
                    "action": "resize",
                    "confidence": 80,
                    "reasoning": f"EC2 instance is underutilized (CPU: {cpu}%). Can be downsized.",
                    "current_instance_type": instance_type,
                    "recommended_instance_type": downsized_type,
                    "estimated_monthly_savings": savings,
                    "estimated_annual_savings": savings * 12,
                    "risk_level": "low",
                    "risk_description": "Brief downtime during resize (typically 2-5 minutes)."
                }
            else:
                recommendation = {
                    "action": "stop",
                    "confidence": 75,
                    "reasoning": f"EC2 instance is underutilized (CPU: {cpu}%). Already at smallest instance type.",
                    "estimated_monthly_savings": monthly_cost,
                    "estimated_annual_savings": monthly_cost * 12,
                    "risk_level": "low",
                    "risk_description": "Instance can be restarted when needed."
                }
        
        elif cpu < 30.0:
            # Moderately utilized - suggest monitoring or slight resize
            downsized_type = EC2Recommendation._get_downsized_instance_type(instance_type)
            
            if downsized_type:
                downsized_hourly = get_instance_hourly_cost(downsized_type, region)
                downsized_monthly = calculate_monthly_cost(downsized_hourly)
                savings = monthly_cost - downsized_monthly
                
                recommendation = {
                    "action": "monitor_or_resize",
                    "confidence": 60,
                    "reasoning": f"EC2 instance shows moderate utilization (CPU: {cpu}%). Could potentially be downsized.",
                    "current_instance_type": instance_type,
                    "recommended_instance_type": downsized_type,
                    "estimated_monthly_savings": savings,
                    "estimated_annual_savings": savings * 12,
                    "risk_level": "medium",
                    "risk_description": "Monitor for peak usage patterns before resizing. Brief downtime during resize.",
                    "alternative_actions": [
                        {
                            "action": "monitor",
                            "description": "Continue monitoring for 2-4 weeks to identify peak usage patterns",
                            "estimated_savings": 0
                        }
                    ]
                }
            else:
                recommendation = {
                    "action": "none",
                    "confidence": 100,
                    "reasoning": f"EC2 instance is well-utilized (CPU: {cpu}%). Already at smallest instance type.",
                    "estimated_monthly_savings": 0,
                    "estimated_annual_savings": 0,
                    "risk_level": "none",
                    "risk_description": "Instance is operating normally."
                }
        
        else:
            # Well-utilized
            recommendation = {
                "action": "none",
                "confidence": 100,
                "reasoning": f"EC2 instance is well-utilized (CPU: {cpu}%). No optimization needed.",
                "estimated_monthly_savings": 0,
                "estimated_annual_savings": 0,
                "risk_level": "none",
                "risk_description": "Instance is operating normally."
            }
        
        recommendation.update({
            "instance_id": instance_id,
            "instance_type": instance_type,
            "current_monthly_cost": monthly_cost,
            "current_annual_cost": monthly_cost * 12,
            "metrics": {
                "cpu_utilization": cpu,
                "network_in_bytes": network_in_bytes,
                "network_out_bytes": network_out_bytes
            }
        })
        
        return recommendation
    
    @staticmethod
    def _get_downsized_instance_type(current_type: str) -> str:
        """
        Get the next smaller EC2 instance type.
        
        Args:
            current_type: Current instance type (e.g., 't2.large')
        
        Returns:
            str: Downsized instance type, or None if already at smallest
        """
        # Downsizing hierarchy for common instance families
        downsizing_map = {
            # t2 family
            "t2.2xlarge": "t2.xlarge",
            "t2.xlarge": "t2.large",
            "t2.large": "t2.medium",
            "t2.medium": "t2.small",
            "t2.small": "t2.micro",
            
            # t3 family
            "t3.2xlarge": "t3.xlarge",
            "t3.xlarge": "t3.large",
            "t3.large": "t3.medium",
            "t3.medium": "t3.small",
            "t3.small": "t3.micro",
            
            # t4g family (burstable - Graviton2)
            "t4g.2xlarge": "t4g.xlarge",
            "t4g.xlarge": "t4g.large",
            "t4g.large": "t4g.medium",
            "t4g.medium": "t4g.small",
            "t4g.small": "t4g.micro",
            
            # m5 family
            "m5.2xlarge": "m5.xlarge",
            "m5.xlarge": "m5.large",
            "m5.large": "m5.large",  # Can't downsize further
            
            # m6g family (general purpose - Graviton2)
            "m6g.16xlarge": "m6g.12xlarge",
            "m6g.12xlarge": "m6g.8xlarge",
            "m6g.8xlarge": "m6g.4xlarge",
            "m6g.4xlarge": "m6g.2xlarge",
            "m6g.2xlarge": "m6g.xlarge",
            "m6g.xlarge": "m6g.large",
            
            # m7g family (general purpose - Graviton3)
            "m7g.16xlarge": "m7g.12xlarge",
            "m7g.12xlarge": "m7g.8xlarge",
            "m7g.8xlarge": "m7g.4xlarge",
            "m7g.4xlarge": "m7g.2xlarge",
            "m7g.2xlarge": "m7g.xlarge",
            "m7g.xlarge": "m7g.large",
            
            # c5 family
            "c5.2xlarge": "c5.xlarge",
            "c5.xlarge": "c5.large",
            "c5.large": "c5.large",  # Can't downsize further
            
            # c6g family (compute optimized - Graviton2)
            "c6g.16xlarge": "c6g.12xlarge",
            "c6g.12xlarge": "c6g.8xlarge",
            "c6g.8xlarge": "c6g.4xlarge",
            "c6g.4xlarge": "c6g.2xlarge",
            "c6g.2xlarge": "c6g.xlarge",
            "c6g.xlarge": "c6g.large",
            
            # c7g family (compute optimized - Graviton3)
            "c7g.16xlarge": "c7g.12xlarge",
            "c7g.12xlarge": "c7g.8xlarge",
            "c7g.8xlarge": "c7g.4xlarge",
            "c7g.4xlarge": "c7g.2xlarge",
            "c7g.2xlarge": "c7g.xlarge",
            "c7g.xlarge": "c7g.large",
            
            # r6g family (memory optimized - Graviton2)
            "r6g.16xlarge": "r6g.12xlarge",
            "r6g.12xlarge": "r6g.8xlarge",
            "r6g.8xlarge": "r6g.4xlarge",
            "r6g.4xlarge": "r6g.2xlarge",
            "r6g.2xlarge": "r6g.xlarge",
            "r6g.xlarge": "r6g.large",
            
            # r7g family (memory optimized - Graviton3)
            "r7g.16xlarge": "r7g.12xlarge",
            "r7g.12xlarge": "r7g.8xlarge",
            "r7g.8xlarge": "r7g.4xlarge",
            "r7g.4xlarge": "r7g.2xlarge",
            "r7g.2xlarge": "r7g.xlarge",
            "r7g.xlarge": "r7g.large",
            
            # g4dn family (GPU - NVIDIA T4)
            "g4dn.16xlarge": "g4dn.12xlarge",
            "g4dn.12xlarge": "g4dn.8xlarge",
            "g4dn.8xlarge": "g4dn.4xlarge",
            "g4dn.4xlarge": "g4dn.2xlarge",
            "g4dn.2xlarge": "g4dn.xlarge",
            
            # g5 family (GPU - NVIDIA A10G)
            "g5.24xlarge": "g5.16xlarge",
            "g5.16xlarge": "g5.12xlarge",
            "g5.12xlarge": "g5.8xlarge",
            "g5.8xlarge": "g5.4xlarge",
            "g5.4xlarge": "g5.2xlarge",
            "g5.2xlarge": "g5.xlarge",
            
            # g6 family (GPU - NVIDIA L4)
            "g6.24xlarge": "g6.16xlarge",
            "g6.16xlarge": "g6.12xlarge",
            "g6.12xlarge": "g6.8xlarge",
            "g6.8xlarge": "g6.4xlarge",
            "g6.4xlarge": "g6.2xlarge",
            "g6.2xlarge": "g6.xlarge",
        }
        
        return downsizing_map.get(current_type)
