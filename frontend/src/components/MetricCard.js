import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

const MetricCard = ({ 
  title, 
  value, 
  change, 
  changeType = 'neutral', 
  icon: Icon, 
  className = '' 
}) => {
  const getChangeColor = () => {
    switch (changeType) {
      case 'positive':
        return 'text-success-600';
      case 'negative':
        return 'text-danger-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTrendIcon = () => {
    if (changeType === 'positive') return TrendingUp;
    if (changeType === 'negative') return TrendingDown;
    return null;
  };

  const TrendIcon = getTrendIcon();

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center">
        <div className="flex-shrink-0">
          {Icon && <Icon className="h-8 w-8 text-primary-600" />}
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
            <dd className="flex items-baseline">
              <div className="text-2xl font-semibold text-gray-900">{value}</div>
              {change && (
                <div className={`ml-2 flex items-baseline text-sm font-semibold ${getChangeColor()}`}>
                  {TrendIcon && <TrendIcon className="self-center flex-shrink-0 h-4 w-4 mr-1" />}
                  <span>{change}</span>
                </div>
              )}
            </dd>
          </dl>
        </div>
      </div>
    </div>
  );
};

export default MetricCard;