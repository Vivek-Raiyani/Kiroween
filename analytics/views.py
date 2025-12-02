from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from integrations.youtube import YouTubeAnalyticsService
from .models import AnalyticsCache, ChannelMetrics, CompetitorChannel, SEOAnalysis, PostingRecommendation
from .calculators import MetricsCalculator
from .seo_analyzer import SEOAnalyzer
from .posting_analyzer import PostingAnalyzer
from accounts.decorators import analytics_required


@analytics_required
def analytics_dashboard(request):
    """
    Main analytics dashboard showing key metrics and performance trends.
    Requirements: 12.1, 12.4
    """
    youtube_service = YouTubeAnalyticsService(user=request.user)
    
    # Get channel ID
    channel_id, error = youtube_service.get_channel_id()
    if error:
        messages.error(request, f"Could not fetch analytics: {error}")
        return render(request, 'analytics/dashboard.html', {
            'error': error,
            'has_youtube': False
        })
    
    # Default time period: last 30 days
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except ValueError:
        days = 30
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Fetch channel metrics
    channel_metrics, error = youtube_service.get_channel_metrics(start_date, end_date)
    
    if error:
        messages.error(request, f"Could not fetch channel metrics: {error}")
        # Return early with error state if API fails
        return render(request, 'analytics/dashboard.html', {
            'error': error,
            'has_youtube': True,
            'api_error': True,
            'time_period': days,
        })
    
    # Calculate key metrics
    total_views = 0
    total_watch_time = 0
    total_likes = 0
    total_comments = 0
    total_shares = 0
    subscribers_gained = 0
    subscribers_lost = 0
    
    for row in channel_metrics.get('rows', []):
        total_views += int(row.get('views', 0))
        total_watch_time += int(row.get('estimatedMinutesWatched', 0))
        total_likes += int(row.get('likes', 0))
        total_comments += int(row.get('comments', 0))
        total_shares += int(row.get('shares', 0))
        subscribers_gained += int(row.get('subscribersGained', 0))
        subscribers_lost += int(row.get('subscribersLost', 0))
    
    # Calculate engagement rate
    engagement_rate = 0
    if total_views > 0:
        engagement_rate = MetricsCalculator.calculate_engagement_rate(
            total_likes, total_comments, total_shares, total_views
        )
    
    # Get latest channel metrics from database for subscriber count
    latest_channel_metrics = ChannelMetrics.objects.filter(
        creator=request.user.get_creator(),
        channel_id=channel_id
    ).first()
    
    subscriber_count = latest_channel_metrics.subscribers if latest_channel_metrics else 0
    net_subscribers = subscribers_gained - subscribers_lost
    
    # Prepare trend data for charts
    trend_data = {
        'dates': [],
        'views': [],
        'watch_time': [],
        'engagement': []
    }
    
    for row in channel_metrics.get('rows', []):
        trend_data['dates'].append(row.get('day', ''))
        trend_data['views'].append(int(row.get('views', 0)))
        trend_data['watch_time'].append(int(row.get('estimatedMinutesWatched', 0)))
        
        # Calculate daily engagement
        views = int(row.get('views', 0))
        if views > 0:
            likes = int(row.get('likes', 0))
            comments = int(row.get('comments', 0))
            shares = int(row.get('shares', 0))
            daily_engagement = MetricsCalculator.calculate_engagement_rate(likes, comments, shares, views)
            trend_data['engagement'].append(daily_engagement)
        else:
            trend_data['engagement'].append(0)
    
    # Get active A/B tests (placeholder for now - will be implemented in A/B testing module)
    active_tests = []
    
    context = {
        'has_youtube': True,
        'channel_id': channel_id,
        'time_period': days,
        'start_date': start_date,
        'end_date': end_date,
        'total_views': total_views,
        'total_watch_time': total_watch_time,
        'subscriber_count': subscriber_count,
        'net_subscribers': net_subscribers,
        'engagement_rate': engagement_rate,
        'trend_data': trend_data,
        'active_tests': active_tests,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@analytics_required
def video_analytics(request, video_id):
    """
    Display detailed analytics for a specific video.
    Requirements: 1.1, 1.3
    """
    youtube_service = YouTubeAnalyticsService(user=request.user)
    
    # Default time period: last 30 days
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except ValueError:
        days = 30
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Fetch video metrics
    video_metrics, error = youtube_service.get_video_metrics(video_id, start_date, end_date)
    
    if error:
        messages.error(request, f"Could not fetch video metrics: {error}")
        return redirect('analytics:dashboard')
    
    # Fetch traffic sources
    traffic_sources, error = youtube_service.get_traffic_sources(video_id, start_date, end_date)
    if error:
        traffic_sources = {'sources': []}
    
    # Fetch demographics
    demographics, error = youtube_service.get_demographics(video_id, start_date, end_date)
    if error:
        demographics = {'age_gender': [], 'geography': []}
    
    # Fetch retention data
    retention_data, error = youtube_service.get_retention_data(video_id)
    if error:
        retention_data = {}
    
    # Calculate aggregate metrics
    total_views = 0
    total_watch_time = 0
    total_likes = 0
    total_comments = 0
    total_shares = 0
    
    for row in video_metrics.get('rows', []):
        total_views += int(row.get('views', 0))
        total_watch_time += int(row.get('estimatedMinutesWatched', 0))
        total_likes += int(row.get('likes', 0))
        total_comments += int(row.get('comments', 0))
        total_shares += int(row.get('shares', 0))
    
    # Calculate engagement rate
    engagement_rate = 0
    if total_views > 0:
        engagement_rate = MetricsCalculator.calculate_engagement_rate(
            total_likes, total_comments, total_shares, total_views
        )
    
    # Prepare trend data
    trend_data = {
        'dates': [],
        'views': [],
        'watch_time': []
    }
    
    for row in video_metrics.get('rows', []):
        trend_data['dates'].append(row.get('day', ''))
        trend_data['views'].append(int(row.get('views', 0)))
        trend_data['watch_time'].append(int(row.get('estimatedMinutesWatched', 0)))
    
    context = {
        'video_id': video_id,
        'time_period': days,
        'start_date': start_date,
        'end_date': end_date,
        'total_views': total_views,
        'total_watch_time': total_watch_time,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'engagement_rate': engagement_rate,
        'trend_data': trend_data,
        'traffic_sources': traffic_sources.get('sources', []),
        'demographics': demographics,
        'retention_data': retention_data,
    }
    
    return render(request, 'analytics/video_analytics.html', context)


@analytics_required
def channel_analytics(request):
    """
    Display channel growth analytics and top-performing videos.
    Requirements: 2.1, 2.2, 2.4
    """
    youtube_service = YouTubeAnalyticsService(user=request.user)
    
    # Get channel ID
    channel_id, error = youtube_service.get_channel_id()
    if error:
        messages.error(request, f"Could not fetch analytics: {error}")
        return redirect('analytics:dashboard')
    
    # Default time period: last 90 days for growth trends
    time_period = request.GET.get('period', '90')
    try:
        days = int(time_period)
    except ValueError:
        days = 90
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Fetch channel metrics
    channel_metrics, error = youtube_service.get_channel_metrics(start_date, end_date)
    
    if error:
        messages.error(request, f"Could not fetch channel metrics: {error}")
        channel_metrics = {'rows': []}
    
    # Prepare subscriber trend data
    subscriber_trend = {
        'dates': [],
        'gained': [],
        'lost': [],
        'net': []
    }
    
    total_views = 0
    total_watch_time = 0
    
    for row in channel_metrics.get('rows', []):
        subscriber_trend['dates'].append(row.get('day', ''))
        gained = int(row.get('subscribersGained', 0))
        lost = int(row.get('subscribersLost', 0))
        subscriber_trend['gained'].append(gained)
        subscriber_trend['lost'].append(lost)
        subscriber_trend['net'].append(gained - lost)
        
        total_views += int(row.get('views', 0))
        total_watch_time += int(row.get('estimatedMinutesWatched', 0))
    
    # Calculate growth rates
    # Get metrics from 30 days ago and compare to last 30 days
    if len(channel_metrics.get('rows', [])) >= 60:
        rows = channel_metrics['rows']
        mid_point = len(rows) // 2
        
        old_views = sum(int(row.get('views', 0)) for row in rows[:mid_point])
        new_views = sum(int(row.get('views', 0)) for row in rows[mid_point:])
        
        try:
            view_growth = MetricsCalculator.calculate_growth_rate(old_views, new_views)
        except ValueError:
            view_growth = 0
    else:
        view_growth = 0
    
    # Get latest channel metrics for current subscriber count
    latest_metrics = ChannelMetrics.objects.filter(
        creator=request.user.get_creator(),
        channel_id=channel_id
    ).first()
    
    current_subscribers = latest_metrics.subscribers if latest_metrics else 0
    
    # Get top-performing videos (placeholder - would need video list from API)
    top_videos = []
    
    context = {
        'channel_id': channel_id,
        'time_period': days,
        'start_date': start_date,
        'end_date': end_date,
        'current_subscribers': current_subscribers,
        'total_views': total_views,
        'total_watch_time': total_watch_time,
        'view_growth': view_growth,
        'subscriber_trend': subscriber_trend,
        'top_videos': top_videos,
    }
    
    return render(request, 'analytics/channel_analytics.html', context)


@analytics_required
def competitor_analysis(request):
    """
    Display competitor comparison and analysis.
    Requirements: 3.1, 3.2
    """
    creator = request.user.get_creator()
    
    # Get competitor channels
    competitors = CompetitorChannel.objects.filter(
        creator=creator,
        is_active=True
    )
    
    # Handle adding new competitor
    if request.method == 'POST':
        channel_id = request.POST.get('channel_id')
        channel_name = request.POST.get('channel_name')
        
        if channel_id and channel_name:
            CompetitorChannel.objects.create(
                creator=creator,
                competitor_channel_id=channel_id,
                channel_name=channel_name
            )
            messages.success(request, f"Added {channel_name} to competitor tracking")
            return redirect('analytics:competitor_analysis')
    
    # Fetch metrics for each competitor (simplified for now)
    competitor_data = []
    for competitor in competitors:
        competitor_data.append({
            'id': competitor.id,
            'channel_id': competitor.competitor_channel_id,
            'name': competitor.channel_name,
            'subscribers': 0,  # Would fetch from YouTube API
            'avg_views': 0,
            'upload_frequency': 0,
        })
    
    context = {
        'competitors': competitor_data,
    }
    
    return render(request, 'analytics/competitor_analysis.html', context)


@analytics_required
def seo_insights(request):
    """
    Display SEO analysis and optimization recommendations.
    Requirements: 4.1, 4.2, 4.4
    """
    # Get recent SEO analyses
    recent_analyses = SEOAnalysis.objects.filter(
        video_id__in=[]  # Would filter by user's videos
    ).order_by('-analyzed_at')[:10]
    
    # Handle new SEO analysis
    if request.method == 'POST':
        video_id = request.POST.get('video_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        tags = request.POST.get('tags', '').split(',')
        
        if video_id and title and description:
            # Perform SEO analysis
            analysis_result = SEOAnalyzer.analyze_video(title, description, tags)
            keyword_suggestions = SEOAnalyzer.suggest_keywords(title, description)
            
            # Save analysis
            SEOAnalysis.objects.create(
                video_id=video_id,
                title=title,
                description=description,
                tags=tags,
                seo_score=analysis_result['seo_score'],
                keyword_suggestions=keyword_suggestions,
                recommendations=analysis_result['recommendations']
            )
            
            messages.success(request, f"SEO analysis complete. Score: {analysis_result['seo_score']}/100")
            return redirect('analytics:seo_insights')
    
    context = {
        'recent_analyses': recent_analyses,
    }
    
    return render(request, 'analytics/seo_insights.html', context)


@analytics_required
def posting_recommendations(request):
    """
    Display optimal posting time recommendations.
    Requirements: 5.3
    """
    youtube_service = YouTubeAnalyticsService(user=request.user)
    
    # Get channel ID
    channel_id, error = youtube_service.get_channel_id()
    if error:
        messages.error(request, f"Could not fetch recommendations: {error}")
        return redirect('analytics:dashboard')
    
    # Get posting recommendations from database
    recommendations = PostingRecommendation.objects.filter(
        creator=request.user.get_creator(),
        channel_id=channel_id
    ).order_by('-expected_engagement')[:3]
    
    # Format recommendations for display
    formatted_recommendations = []
    for rec in recommendations:
        formatted_recommendations.append({
            'day': PostingAnalyzer.format_day_name(rec.day_of_week),
            'time': PostingAnalyzer.format_time(rec.hour),
            'expected_engagement': rec.expected_engagement,
            'confidence': rec.confidence_score,
        })
    
    # If no recommendations, generate default ones
    if not formatted_recommendations:
        default_recs = PostingAnalyzer.recommend_posting_times(channel_id, [], 'default')
        for rec in default_recs:
            formatted_recommendations.append({
                'day': PostingAnalyzer.format_day_name(rec['day_of_week']),
                'time': PostingAnalyzer.format_time(rec['hour']),
                'expected_engagement': rec['expected_engagement'],
                'confidence': rec['confidence_score'],
                'reason': rec.get('reason', '')
            })
    
    context = {
        'recommendations': formatted_recommendations,
    }
    
    return render(request, 'analytics/posting_recommendations.html', context)



@analytics_required
def export_video_metrics_csv(request, video_id):
    """
    Export video metrics to CSV format.
    Requirements: 13.1, 13.2, 13.4
    """
    from .exporters import CSVExporter
    
    youtube_service = YouTubeAnalyticsService(user=request.user)
    
    # Get time period from query params
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except ValueError:
        days = 30
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Fetch video metrics
    video_metrics, error = youtube_service.get_video_metrics(video_id, start_date, end_date)
    
    if error:
        messages.error(request, f"Could not fetch video metrics: {error}")
        return redirect('analytics:video_analytics', video_id=video_id)
    
    # Format data for export
    metrics_data = []
    for row in video_metrics.get('rows', []):
        views = int(row.get('views', 0))
        likes = int(row.get('likes', 0))
        comments = int(row.get('comments', 0))
        shares = int(row.get('shares', 0))
        
        engagement_rate = 0
        if views > 0:
            engagement_rate = MetricsCalculator.calculate_engagement_rate(likes, comments, shares, views)
        
        metrics_data.append({
            'date': row.get('day', ''),
            'views': views,
            'watch_time': int(row.get('estimatedMinutesWatched', 0)),
            'likes': likes,
            'comments': comments,
            'shares': shares,
            'ctr': float(row.get('ctr', 0)),
            'engagement_rate': engagement_rate
        })
    
    return CSVExporter.export_video_metrics(video_id, metrics_data, start_date, end_date)


@analytics_required
def export_channel_metrics_csv(request):
    """
    Export channel metrics to CSV format.
    Requirements: 13.1, 13.2, 13.4
    """
    from .exporters import CSVExporter
    
    youtube_service = YouTubeAnalyticsService(user=request.user)
    
    # Get channel ID
    channel_id, error = youtube_service.get_channel_id()
    if error:
        messages.error(request, f"Could not fetch analytics: {error}")
        return redirect('analytics:dashboard')
    
    # Get time period from query params
    time_period = request.GET.get('period', '90')
    try:
        days = int(time_period)
    except ValueError:
        days = 90
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Fetch channel metrics
    channel_metrics, error = youtube_service.get_channel_metrics(start_date, end_date)
    
    if error:
        messages.error(request, f"Could not fetch channel metrics: {error}")
        return redirect('analytics:channel_analytics')
    
    # Format data for export
    metrics_data = []
    for row in channel_metrics.get('rows', []):
        metrics_data.append({
            'date': row.get('day', ''),
            'subscribers': 0,  # Would need to fetch from separate API call
            'subscribers_gained': int(row.get('subscribersGained', 0)),
            'subscribers_lost': int(row.get('subscribersLost', 0)),
            'views': int(row.get('views', 0)),
            'watch_time': int(row.get('estimatedMinutesWatched', 0)),
            'avg_view_duration': float(row.get('averageViewDuration', 0))
        })
    
    return CSVExporter.export_channel_metrics(channel_id, metrics_data, start_date, end_date)


@analytics_required
def export_video_metrics_pdf(request, video_id):
    """
    Export video analytics report to PDF format.
    Requirements: 13.1, 13.3, 13.4
    """
    from .exporters import PDFExporter
    
    youtube_service = YouTubeAnalyticsService(user=request.user)
    
    # Get time period from query params
    time_period = request.GET.get('period', '30')
    try:
        days = int(time_period)
    except ValueError:
        days = 30
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Fetch video metrics
    video_metrics, error = youtube_service.get_video_metrics(video_id, start_date, end_date)
    
    if error:
        messages.error(request, f"Could not fetch video metrics: {error}")
        return redirect('analytics:video_analytics', video_id=video_id)
    
    # Calculate aggregate metrics
    total_views = 0
    total_watch_time = 0
    total_likes = 0
    total_comments = 0
    total_shares = 0
    
    trend_data = {
        'dates': [],
        'views': [],
        'engagement': []
    }
    
    for row in video_metrics.get('rows', []):
        views = int(row.get('views', 0))
        likes = int(row.get('likes', 0))
        comments = int(row.get('comments', 0))
        shares = int(row.get('shares', 0))
        
        total_views += views
        total_watch_time += int(row.get('estimatedMinutesWatched', 0))
        total_likes += likes
        total_comments += comments
        total_shares += shares
        
        trend_data['dates'].append(row.get('day', ''))
        trend_data['views'].append(views)
        
        if views > 0:
            engagement = MetricsCalculator.calculate_engagement_rate(likes, comments, shares, views)
            trend_data['engagement'].append(engagement)
        else:
            trend_data['engagement'].append(0)
    
    # Calculate engagement rate
    engagement_rate = 0
    if total_views > 0:
        engagement_rate = MetricsCalculator.calculate_engagement_rate(
            total_likes, total_comments, total_shares, total_views
        )
    
    # Prepare report data
    report_data = {
        'report_type': 'Video Analytics',
        'video_id': video_id,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'metrics': {
            'total_views': total_views,
            'total_watch_time': total_watch_time,
            'engagement_rate': engagement_rate,
            'ctr': 0  # Would need from API
        },
        'trend_data': trend_data
    }
    
    # Generate charts
    charts = PDFExporter.add_charts_to_pdf(report_data)
    
    return PDFExporter.generate_analytics_report(report_data, charts)


@analytics_required
def export_channel_metrics_pdf(request):
    """
    Export channel analytics report to PDF format.
    Requirements: 13.1, 13.3, 13.4
    """
    from .exporters import PDFExporter
    
    youtube_service = YouTubeAnalyticsService(user=request.user)
    
    # Get channel ID
    channel_id, error = youtube_service.get_channel_id()
    if error:
        messages.error(request, f"Could not fetch analytics: {error}")
        return redirect('analytics:dashboard')
    
    # Get time period from query params
    time_period = request.GET.get('period', '90')
    try:
        days = int(time_period)
    except ValueError:
        days = 90
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Fetch channel metrics
    channel_metrics, error = youtube_service.get_channel_metrics(start_date, end_date)
    
    if error:
        messages.error(request, f"Could not fetch channel metrics: {error}")
        return redirect('analytics:channel_analytics')
    
    # Calculate aggregate metrics
    total_views = 0
    total_watch_time = 0
    subscribers_gained = 0
    subscribers_lost = 0
    
    trend_data = {
        'dates': [],
        'views': [],
        'engagement': []
    }
    
    for row in channel_metrics.get('rows', []):
        views = int(row.get('views', 0))
        total_views += views
        total_watch_time += int(row.get('estimatedMinutesWatched', 0))
        subscribers_gained += int(row.get('subscribersGained', 0))
        subscribers_lost += int(row.get('subscribersLost', 0))
        
        trend_data['dates'].append(row.get('day', ''))
        trend_data['views'].append(views)
    
    # Get latest channel metrics for subscriber count
    latest_metrics = ChannelMetrics.objects.filter(
        creator=request.user.get_creator(),
        channel_id=channel_id
    ).first()
    
    current_subscribers = latest_metrics.subscribers if latest_metrics else 0
    
    # Prepare report data
    report_data = {
        'report_type': 'Channel Analytics',
        'channel_id': channel_id,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'metrics': {
            'total_views': total_views,
            'total_watch_time': total_watch_time,
            'subscribers': current_subscribers,
            'engagement_rate': 0  # Would calculate from data
        },
        'trend_data': trend_data
    }
    
    # Generate charts
    charts = PDFExporter.add_charts_to_pdf(report_data)
    
    return PDFExporter.generate_analytics_report(report_data, charts)
