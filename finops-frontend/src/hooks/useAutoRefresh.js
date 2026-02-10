import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Custom hook for auto-refreshing data at regular intervals
 * Automatically stops when navigating away and resumes when returning
 * @param {Function} callback - Function to call on each refresh
 * @param {number} interval - Interval in milliseconds (default: 10000ms)
 */
export const useAutoRefresh = (callback, interval = 10000) => {
  const intervalRef = useRef(null);
  const location = useLocation();

  useEffect(() => {
    // Start the interval
    intervalRef.current = setInterval(() => {
      callback();
    }, interval);

    // Cleanup on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [callback, interval]);

  // Stop refresh when navigating away, resume when returning
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [location.pathname]);
};
