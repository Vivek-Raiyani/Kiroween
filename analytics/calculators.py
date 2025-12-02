"""
Analytics calculation services for metrics processing.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime


class MetricsCalculator:
    """Service for calculating analytics metrics."""
    
    @staticmethod
    def calculate_growth_rate(old_value: float, new_value: float) -> float:
        """
        Calculate percentage growth rate between two values.
        
        Args:
            old_value: Previous metric value
            new_value: Current metric value
            
        Returns:
            Growth rate as percentage (e.g., 25.5 for 25.5% growth)
            
        Raises:
            ValueError: If old_value is zero or negative
        """
        if old_value <= 0:
            raise ValueError("old_value must be positive for growth rate calculation")
        
        growth_rate = ((new_value - old_value) / old_value) * 100
        return round(growth_rate, 2)
    
    @staticmethod
    def calculate_engagement_rate(
        likes: int,
        comments: int,
        shares: int,
        views: int
    ) -> float:
        """
        Calculate engagement rate based on interactions and views.
        
        Args:
            likes: Number of likes
            comments: Number of comments
            shares: Number of shares
            views: Number of views
            
        Returns:
            Engagement rate as percentage
            
        Raises:
            ValueError: If views is zero or negative
        """
        if views <= 0:
            raise ValueError("views must be positive for engagement rate calculation")
        
        total_engagement = likes + comments + shares
        engagement_rate = (total_engagement / views) * 100
        return round(engagement_rate, 2)
    
    @staticmethod
    def calculate_ctr(clicks: int, impressions: int) -> float:
        """
        Calculate click-through rate.
        
        Args:
            clicks: Number of clicks
            impressions: Number of impressions
            
        Returns:
            CTR as percentage
            
        Raises:
            ValueError: If impressions is zero or negative
        """
        if impressions <= 0:
            raise ValueError("impressions must be positive for CTR calculation")
        
        ctr = (clicks / impressions) * 100
        return round(ctr, 2)
    
    @staticmethod
    def aggregate_metrics(metrics_list: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Aggregate multiple metric periods into summary statistics.
        
        Args:
            metrics_list: List of metric dictionaries with numeric values
            
        Returns:
            Dictionary with aggregated metrics (sum, average, min, max)
            
        Example:
            >>> metrics = [
            ...     {'views': 100, 'likes': 10},
            ...     {'views': 200, 'likes': 20},
            ...     {'views': 150, 'likes': 15}
            ... ]
            >>> result = MetricsCalculator.aggregate_metrics(metrics)
            >>> result['views']['sum']
            450
        """
        if not metrics_list:
            return {}
        
        # Get all metric keys from first item
        metric_keys = set()
        for metric_dict in metrics_list:
            metric_keys.update(metric_dict.keys())
        
        aggregated = {}
        
        for key in metric_keys:
            # Extract values for this metric, filtering out None values
            values = [
                float(m[key]) for m in metrics_list 
                if key in m and m[key] is not None
            ]
            
            if values:
                aggregated[key] = {
                    'sum': round(sum(values), 2),
                    'average': round(sum(values) / len(values), 2),
                    'min': round(min(values), 2),
                    'max': round(max(values), 2),
                    'count': len(values)
                }
            else:
                aggregated[key] = {
                    'sum': 0,
                    'average': 0,
                    'min': 0,
                    'max': 0,
                    'count': 0
                }
        
        return aggregated
