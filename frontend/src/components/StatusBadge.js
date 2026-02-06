import React from 'react';

const StatusBadge = ({ status, className = '' }) => {
  const getStatusClass = (status) => {
    const normalizedStatus = status?.toLowerCase();
    switch (normalizedStatus) {
      case 'low':
        return 'status-badge status-low';
      case 'medium':
        return 'status-badge status-medium';
      case 'high':
        return 'status-badge status-high';
      case 'critical':
        return 'status-badge status-critical';
      case 'pending':
        return 'status-badge bg-yellow-100 text-yellow-800';
      case 'approved':
        return 'status-badge bg-blue-100 text-blue-800';
      case 'executed':
        return 'status-badge bg-green-100 text-green-800';
      case 'rolled_back':
        return 'status-badge bg-red-100 text-red-800';
      case 'active':
        return 'status-badge bg-green-100 text-green-800';
      case 'inactive':
        return 'status-badge bg-gray-100 text-gray-800';
      default:
        return 'status-badge bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`${getStatusClass(status)} ${className}`}>
      {status}
    </span>
  );
};

export default StatusBadge;