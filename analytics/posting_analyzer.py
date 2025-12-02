"""
Posting time analysis service for optimal video publishing.
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class PostingAnalyzer:
    """Service for analyzing posting patterns and recommending optimal times."""
    
    # Industry standard recommendations by category (hour of day, 24-hour format)
    INDUSTRY_STANDARDS = {
        'default': [
            (14, 'Weekday afternoon'),  # 2 PM
            (18, 'Evening'),             # 6 PM
            (12, 'Weekend noon'),        # 12 PM
        ],
        'gaming': [
            (15, 'After school'),        # 3 PM
            (20, 'Evening gaming'),      # 8 PM
            (12, 'Weekend noon'),        # 12 PM
        ],
        'education': [
            (10, 'Morning learning'),    # 10 AM
            (14, 'Afternoon study'),     # 2 PM
            (19, 'Evening review'),      # 7 PM
        ],
        'entertainment': [
            (18, 'After work'),          # 6 PM
            (20, 'Prime time'),          # 8 PM
            (14, 'Weekend afternoon'),   # 2 PM
        ],
    }
    
    # Minimum videos needed for reliable analysis
    MIN_VIDEOS_FOR_ANALYSIS = 10
    
    @classmethod
    def analyze_posting_patterns(
        cls,
        videos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze historical video performance to identify posting patterns.
        
        Args:
            videos: List of video dictionaries with:
                - published_at: datetime of publication
                - views: view count
                - likes: like count
                - comments: comment count
                - engagement_rate: engagement rate (optional)
                
        Returns:
            Dictionary containing:
                - patterns: Dict mapping (day_of_week, hour) to performance metrics
                - best_days: List of best performing days
                - best_hours: List of best performing hours
                - sample_size: Number of videos analyzed
        """
        if not videos:
            return {
                'patterns': {},
                'best_days': [],
                'best_hours': [],
                'sample_size': 0
            }
        
        # Group videos by day of week and hour
        patterns = defaultdict(lambda: {
            'videos': [],
            'total_views': 0,
            'total_engagement': 0,
            'avg_views': 0,
            'avg_engagement': 0
        })
        
        for video in videos:
            published_at = video.get('published_at')
            if not isinstance(published_at, datetime):
                continue
            
            day_of_week = published_at.weekday()  # 0=Monday, 6=Sunday
            hour = published_at.hour
            
            views = video.get('views', 0)
            engagement = video.get('engagement_rate', 0)
            
            # If engagement_rate not provided, calculate from likes and comments
            if engagement == 0 and views > 0:
                likes = video.get('likes', 0)
                comments = video.get('comments', 0)
                engagement = ((likes + comments) / views) * 100
            
            key = (day_of_week, hour)
            patterns[key]['videos'].append(video)
            patterns[key]['total_views'] += views
            patterns[key]['total_engagement'] += engagement
        
        # Calculate averages
        for key, data in patterns.items():
            video_count = len(data['videos'])
            if video_count > 0:
                data['avg_views'] = data['total_views'] / video_count
                data['avg_engagement'] = data['total_engagement'] / video_count
                data['count'] = video_count
        
        # Find best days and hours
        day_performance = defaultdict(lambda: {'views': 0, 'engagement': 0, 'count': 0})
        hour_performance = defaultdict(lambda: {'views': 0, 'engagement': 0, 'count': 0})
        
        for (day, hour), data in patterns.items():
            day_performance[day]['views'] += data['avg_views']
            day_performance[day]['engagement'] += data['avg_engagement']
            day_performance[day]['count'] += 1
            
            hour_performance[hour]['views'] += data['avg_views']
            hour_performance[hour]['engagement'] += data['avg_engagement']
            hour_performance[hour]['count'] += 1
        
        # Sort by engagement (primary) and views (secondary)
        best_days = sorted(
            day_performance.items(),
            key=lambda x: (x[1]['engagement'], x[1]['views']),
            reverse=True
        )[:3]
        
        best_hours = sorted(
            hour_performance.items(),
            key=lambda x: (x[1]['engagement'], x[1]['views']),
            reverse=True
        )[:5]
        
        return {
            'patterns': dict(patterns),
            'best_days': [{'day': day, **metrics} for day, metrics in best_days],
            'best_hours': [{'hour': hour, **metrics} for hour, metrics in best_hours],
            'sample_size': len(videos)
        }
    
    @classmethod
    def get_audience_activity(
        cls,
        channel_id: str,
        videos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze audience activity patterns based on video performance.
        
        Args:
            channel_id: YouTube channel ID
            videos: List of video dictionaries with performance data
            
        Returns:
            Dictionary containing:
                - activity_by_day: Activity levels by day of week
                - activity_by_hour: Activity levels by hour of day
                - peak_times: List of peak activity periods
        """
        if not videos:
            return {
                'activity_by_day': {},
                'activity_by_hour': {},
                'peak_times': []
            }
        
        # Analyze when videos get the most engagement
        day_activity = defaultdict(float)
        hour_activity = defaultdict(float)
        
        for video in videos:
            published_at = video.get('published_at')
            if not isinstance(published_at, datetime):
                continue
            
            day_of_week = published_at.weekday()
            hour = published_at.hour
            
            # Use engagement as proxy for audience activity
            engagement = video.get('engagement_rate', 0)
            if engagement == 0:
                views = video.get('views', 0)
                likes = video.get('likes', 0)
                comments = video.get('comments', 0)
                if views > 0:
                    engagement = ((likes + comments) / views) * 100
            
            day_activity[day_of_week] += engagement
            hour_activity[hour] += engagement
        
        # Normalize by count
        day_counts = Counter(v.get('published_at').weekday() for v in videos if isinstance(v.get('published_at'), datetime))
        hour_counts = Counter(v.get('published_at').hour for v in videos if isinstance(v.get('published_at'), datetime))
        
        for day in day_activity:
            if day_counts[day] > 0:
                day_activity[day] /= day_counts[day]
        
        for hour in hour_activity:
            if hour_counts[hour] > 0:
                hour_activity[hour] /= hour_counts[hour]
        
        # Find peak times (top 3 combinations)
        peak_times = []
        for day in range(7):
            for hour in range(24):
                if day in day_activity and hour in hour_activity:
                    combined_score = (day_activity[day] + hour_activity[hour]) / 2
                    peak_times.append({
                        'day': day,
                        'hour': hour,
                        'activity_score': round(combined_score, 2)
                    })
        
        peak_times.sort(key=lambda x: x['activity_score'], reverse=True)
        
        return {
            'activity_by_day': {day: round(score, 2) for day, score in day_activity.items()},
            'activity_by_hour': {hour: round(score, 2) for hour, score in hour_activity.items()},
            'peak_times': peak_times[:10]
        }
    
    @classmethod
    def recommend_posting_times(
        cls,
        channel_id: str,
        videos: List[Dict[str, Any]],
        category: str = 'default'
    ) -> List[Dict[str, Any]]:
        """
        Generate top 3 posting time recommendations.
        
        Args:
            channel_id: YouTube channel ID
            videos: List of video dictionaries with performance data
            category: Channel category for industry standards fallback
            
        Returns:
            List of top 3 recommendations, each containing:
                - day_of_week: Day (0=Monday, 6=Sunday)
                - hour: Hour of day (0-23)
                - expected_engagement: Expected engagement level
                - confidence_score: Confidence in recommendation (0-1)
                - reason: Explanation for recommendation
        """
        recommendations = []
        
        # Check if we have enough data for analysis
        if len(videos) >= cls.MIN_VIDEOS_FOR_ANALYSIS:
            # Use historical data
            patterns = cls.analyze_posting_patterns(videos)
            audience_activity = cls.get_audience_activity(channel_id, videos)
            
            # Combine pattern analysis with audience activity
            scored_times = []
            
            for (day, hour), data in patterns['patterns'].items():
                # Calculate score based on views and engagement
                view_score = data['avg_views']
                engagement_score = data['avg_engagement'] * 100  # Weight engagement higher
                
                # Get audience activity score for this time
                activity_score = 0
                for peak in audience_activity['peak_times']:
                    if peak['day'] == day and peak['hour'] == hour:
                        activity_score = peak['activity_score']
                        break
                
                # Combined score
                combined_score = (view_score + engagement_score + activity_score) / 3
                
                # Confidence based on sample size
                confidence = min(1.0, data['count'] / 5)  # Full confidence at 5+ videos
                
                scored_times.append({
                    'day_of_week': day,
                    'hour': hour,
                    'expected_engagement': round(combined_score, 2),
                    'confidence_score': round(confidence, 2),
                    'reason': f'Based on {data["count"]} videos with avg {data["avg_views"]:.0f} views'
                })
            
            # Sort by expected engagement
            scored_times.sort(key=lambda x: x['expected_engagement'], reverse=True)
            recommendations = scored_times[:3]
        
        # If insufficient data, use industry standards
        if len(recommendations) < 3:
            industry_times = cls.INDUSTRY_STANDARDS.get(category, cls.INDUSTRY_STANDARDS['default'])
            
            for hour, reason in industry_times:
                # Determine best day based on category
                if 'weekend' in reason.lower():
                    day = 5  # Saturday
                else:
                    day = 2  # Wednesday (mid-week)
                
                recommendations.append({
                    'day_of_week': day,
                    'hour': hour,
                    'expected_engagement': 50.0,  # Neutral score
                    'confidence_score': 0.3,  # Low confidence for industry standards
                    'reason': f'Industry standard: {reason}'
                })
            
            recommendations = recommendations[:3]
        
        return recommendations
    
    @staticmethod
    def format_day_name(day_of_week: int) -> str:
        """Convert day number to name."""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[day_of_week] if 0 <= day_of_week <= 6 else 'Unknown'
    
    @staticmethod
    def format_time(hour: int) -> str:
        """Format hour as readable time."""
        if hour == 0:
            return '12:00 AM'
        elif hour < 12:
            return f'{hour}:00 AM'
        elif hour == 12:
            return '12:00 PM'
        else:
            return f'{hour - 12}:00 PM'
