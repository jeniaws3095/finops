# Configurable thresholds for waste detection
DEFAULT_CPU_THRESHOLD = 5.0  # CPU utilization below 5% is considered waste
DEFAULT_CONNECTION_THRESHOLD = 5  # Database connections below 5 is considered waste
DEFAULT_REQUEST_THRESHOLD = 100  # Requests per hour below 100 is considered waste
DEFAULT_IOPS_THRESHOLD = 10  # IOPS below 10 is considered waste


def is_waste(cpu, threshold=DEFAULT_CPU_THRESHOLD):
    """
    Determine if an EC2 instance is wasting resources based on CPU utilization.
    
    Args:
        cpu: CPU utilization percentage (0-100)
        threshold: CPU threshold below which resource is considered waste (default: 5%)
    
    Returns:
        True if CPU is below threshold, False otherwise
    """
    return cpu < threshold


def is_rds_waste(cpu, connections, threshold_cpu=DEFAULT_CPU_THRESHOLD, threshold_connections=DEFAULT_CONNECTION_THRESHOLD):
    """
    Determine if an RDS instance is wasting resources.
    
    Args:
        cpu: CPU utilization percentage (0-100)
        connections: Number of active database connections
        threshold_cpu: CPU threshold (default: 5%)
        threshold_connections: Connection threshold (default: 5)
    
    Returns:
        True if both CPU and connections are below thresholds, False otherwise
    """
    return cpu < threshold_cpu and connections < threshold_connections


def is_load_balancer_waste(request_count, healthy_hosts, threshold=DEFAULT_REQUEST_THRESHOLD):
    """
    Determine if a load balancer is wasting resources.
    
    Args:
        request_count: Number of requests per hour
        healthy_hosts: Number of healthy target hosts
        threshold: Request threshold (default: 100)
    
    Returns:
        True if request count is below threshold AND has healthy hosts, False otherwise
    """
    return request_count < threshold and healthy_hosts > 0


def is_ebs_waste(read_ops, write_ops, is_attached=True):
    """
    Determine if an EBS volume is wasting resources.
    
    Args:
        read_ops: Number of read operations
        write_ops: Number of write operations
        is_attached: Whether the volume is attached to an instance
    
    Returns:
        True if volume has no I/O activity OR is unattached, False otherwise
    """
    return (read_ops + write_ops == 0) or not is_attached


def is_asg_waste(utilization_percent, threshold=20):
    """
    Determine if an Auto Scaling Group is wasting resources.
    
    Args:
        utilization_percent: Instance utilization percentage (0-100)
        threshold: Utilization threshold (default: 20%)
    
    Returns:
        True if utilization is below threshold, False otherwise
    """
    return utilization_percent < threshold
