from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from accounts.decorators import abtest_required
from .models import ABTest, TestVariant, TestLog
from .test_engine import ABTestEngine
from .scheduler import VariantScheduler
from .winner_selector import WinnerSelector
from .metrics_collector import MetricsCollector


@abtest_required
def abtest_list(request):
    """
    Display all A/B tests with status and progress.
    Requirements: 10.4
    """
    creator = request.user.get_creator()
    
    # Get all tests for this creator
    tests = ABTest.objects.filter(creator=creator).prefetch_related('variants', 'winner_variant')
    
    # Prepare test data with progress information
    test_data = []
    for test in tests:
        # Calculate progress
        progress_percentage = 0
        time_remaining = None
        current_variant = None
        
        if test.status == 'active' and test.start_date and test.end_date:
            now = timezone.now()
            total_duration = (test.end_date - test.start_date).total_seconds()
            elapsed = (now - test.start_date).total_seconds()
            
            if total_duration > 0:
                progress_percentage = min(100, (elapsed / total_duration) * 100)
            
            if now < test.end_date:
                time_remaining = test.end_date - now
            
            # Get current variant
            scheduler = VariantScheduler()
            current_variant, _ = scheduler.get_current_variant(test.id)
        
        test_data.append({
            'test': test,
            'progress_percentage': round(progress_percentage, 1),
            'time_remaining': time_remaining,
            'current_variant': current_variant,
            'variant_count': test.variants.count()
        })
    
    context = {
        'test_data': test_data,
    }
    
    return render(request, 'abtesting/test_list.html', context)


@abtest_required
def create_abtest(request):
    """
    Create a new A/B test with variants.
    Requirements: 6.1, 7.1, 8.1, 9.1, 10.1
    """
    if request.method == 'POST':
        # Get form data
        video_id = request.POST.get('video_id')
        video_title = request.POST.get('video_title')
        test_type = request.POST.get('test_type')
        duration_hours = request.POST.get('duration_hours')
        rotation_frequency_hours = request.POST.get('rotation_frequency_hours')
        performance_threshold = request.POST.get('performance_threshold', '0.05')
        auto_select_winner = request.POST.get('auto_select_winner') == 'on'
        
        # Validate required fields
        if not all([video_id, video_title, test_type, duration_hours, rotation_frequency_hours]):
            messages.error(request, "All required fields must be filled")
            return render(request, 'abtesting/create_test.html', {'test_types': ABTest.TEST_TYPE_CHOICES})
        
        try:
            duration_hours = int(duration_hours)
            rotation_frequency_hours = int(rotation_frequency_hours)
            performance_threshold = float(performance_threshold)
        except ValueError:
            messages.error(request, "Invalid numeric values")
            return render(request, 'abtesting/create_test.html', {'test_types': ABTest.TEST_TYPE_CHOICES})
        
        # Get variant data
        variant_names = request.POST.getlist('variant_name[]')
        variant_thumbnails = request.POST.getlist('variant_thumbnail[]')
        variant_titles = request.POST.getlist('variant_title[]')
        variant_descriptions = request.POST.getlist('variant_description[]')
        
        # Validate variant count (2-3)
        if len(variant_names) < 2 or len(variant_names) > 3:
            messages.error(request, "Test must have between 2 and 3 variants")
            return render(request, 'abtesting/create_test.html', {'test_types': ABTest.TEST_TYPE_CHOICES})
        
        # Build variants data
        variants_data = []
        for i in range(len(variant_names)):
            variant = {
                'name': variant_names[i],
                'thumbnail_url': variant_thumbnails[i] if i < len(variant_thumbnails) else None,
                'title': variant_titles[i] if i < len(variant_titles) else None,
                'description': variant_descriptions[i] if i < len(variant_descriptions) else None,
            }
            variants_data.append(variant)
        
        # Create test using engine
        engine = ABTestEngine(user=request.user)
        test, error = engine.create_test(
            video_id=video_id,
            video_title=video_title,
            test_type=test_type,
            variants_data=variants_data,
            duration_hours=duration_hours,
            rotation_frequency_hours=rotation_frequency_hours,
            performance_threshold=performance_threshold,
            auto_select_winner=auto_select_winner
        )
        
        if error:
            messages.error(request, f"Failed to create test: {error}")
            return render(request, 'abtesting/create_test.html', {'test_types': ABTest.TEST_TYPE_CHOICES})
        
        messages.success(request, f"A/B test created successfully for {video_title}")
        return redirect('abtesting:test_detail', test_id=test.id)
    
    # GET request - show form
    context = {
        'test_types': ABTest.TEST_TYPE_CHOICES,
    }
    
    return render(request, 'abtesting/create_test.html', context)


@abtest_required
def abtest_detail(request, test_id):
    """
    Display test details, configuration, and variant performance metrics.
    Requirements: 6.3, 7.3, 8.3, 10.4
    """
    test = get_object_or_404(ABTest, id=test_id, creator=request.user.get_creator())
    
    # Get test status information
    engine = ABTestEngine()
    status_data, error = engine.get_test_status(test_id)
    
    if error:
        messages.error(request, f"Could not fetch test status: {error}")
        status_data = {}
    
    # Get current variant
    scheduler = VariantScheduler()
    current_variant, _ = scheduler.get_current_variant(test_id)
    
    # Get recent logs
    recent_logs = test.logs.all()[:10]
    
    # Check if there's a winner
    winner_info = None
    if test.status in ['active', 'completed']:
        winner_selector = WinnerSelector()
        has_winner, winner_id, winner_message = winner_selector.check_for_winner(test_id)
        winner_info = {
            'has_winner': has_winner,
            'winner_id': winner_id,
            'message': winner_message
        }
    
    # Prepare variant data with performance metrics
    variants_data = []
    for variant in test.variants.all():
        variants_data.append({
            'variant': variant,
            'is_current': current_variant and current_variant.id == variant.id,
        })
    
    context = {
        'test': test,
        'status_data': status_data,
        'current_variant': current_variant,
        'variants_data': variants_data,
        'recent_logs': recent_logs,
        'winner_info': winner_info,
    }
    
    return render(request, 'abtesting/test_detail.html', context)


@abtest_required
def abtest_management(request, test_id):
    """
    Handle test management actions: pause, resume, stop, manual winner selection.
    Requirements: 10.3
    """
    # CRITICAL DEBUG - This MUST print if view is called
    print("=" * 80)
    print("ABTEST_MANAGEMENT VIEW CALLED")
    print(f"Method: {request.method}")
    print(f"Test ID: {test_id}")
    print(f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    print("=" * 80)
    
    test = get_object_or_404(ABTest, id=test_id, creator=request.user.get_creator())
    
    print(f"Test found: {test.video_title}")
    
    if request.method == 'POST':
        print("=" * 80)
        print("POST REQUEST DETECTED")
        print(f"POST data: {dict(request.POST)}")
        print("=" * 80)
        
        # Try both 'action' and 'action_type' for compatibility
        action = request.POST.get('action') or request.POST.get('action_type')
        
        print(f"Action extracted: {action}")
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"POST request received. Action: {action}, User: {request.user.username}")
        logger.info(f"POST data: {request.POST}")
        
        engine = ABTestEngine(user=request.user)
        
        if action == 'start':
            success, error = engine.start_test(test_id)
            if success:
                messages.success(request, "Test started successfully")
            else:
                messages.error(request, f"Failed to start test: {error}")
        
        elif action == 'pause':
            success, error = engine.pause_test(test_id)
            if success:
                messages.success(request, "Test paused successfully")
            else:
                messages.error(request, f"Failed to pause test: {error}")
        
        elif action == 'resume':
            success, error = engine.resume_test(test_id)
            if success:
                messages.success(request, "Test resumed successfully")
            else:
                messages.error(request, f"Failed to resume test: {error}")
        
        elif action == 'stop':
            success, error = engine.stop_test(test_id)
            if success:
                messages.success(request, "Test stopped successfully")
            else:
                messages.error(request, f"Failed to stop test: {error}")
        
        elif action == 'select_winner':
            variant_id = request.POST.get('variant_id')
            winner_selector = WinnerSelector(user=request.user)
            
            if variant_id:
                # Manual winner selection
                winner, error = winner_selector.select_winner(test_id, manual_variant_id=int(variant_id))
            else:
                # Automatic winner selection
                winner, error = winner_selector.select_winner(test_id)
            
            if winner:
                messages.success(request, f"Winner selected: Variant {winner.variant_name}")
            else:
                messages.error(request, f"Failed to select winner: {error}")
        
        elif action == 'apply_winner':
            winner_selector = WinnerSelector(user=request.user)
            success, error = winner_selector.apply_winner(test_id)
            
            if success:
                messages.success(request, "Winner applied to video successfully")
            else:
                messages.error(request, f"Failed to apply winner: {error}")
        
        elif action == 'rotate_variant':
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Rotate variant requested for test {test_id} by user {request.user.username}")
            
            scheduler = VariantScheduler(user=request.user)
            next_variant, error = scheduler.rotate_variant(test_id)
            
            if next_variant:
                logger.info(f"Successfully rotated to variant {next_variant.variant_name}")
                messages.success(request, f"Rotated to variant {next_variant.variant_name}")
            else:
                logger.error(f"Failed to rotate variant: {error}")
                messages.error(request, f"Failed to rotate variant: {error}")
        
        else:
            messages.error(request, "Invalid action")
        
        return redirect('abtesting:test_detail', test_id=test_id)
    
    # GET request - redirect to detail page
    return redirect('abtesting:test_detail', test_id=test_id)


@abtest_required
def abtest_results(request, test_id):
    """
    Display completed test results with winning variant and performance comparison.
    Requirements: 6.4, 7.4, 8.4, 9.3
    """
    test = get_object_or_404(ABTest, id=test_id, creator=request.user.get_creator())
    
    # Validate test is completed
    if test.status != 'completed':
        messages.warning(request, "Test is not yet completed")
        return redirect('abtesting:test_detail', test_id=test_id)
    
    # Get all variants with performance data
    variants = test.variants.all().order_by('variant_name')
    
    # Prepare comparison data
    comparison_data = {
        'variant_names': [],
        'impressions': [],
        'clicks': [],
        'views': [],
        'ctr': [],
    }
    
    for variant in variants:
        comparison_data['variant_names'].append(variant.variant_name)
        comparison_data['impressions'].append(variant.impressions)
        comparison_data['clicks'].append(variant.clicks)
        comparison_data['views'].append(variant.views)
        comparison_data['ctr'].append(variant.ctr * 100)  # Convert to percentage
    
    # Calculate improvement if there's a winner
    improvement_data = None
    if test.winner_variant:
        winner = test.winner_variant
        other_variants = [v for v in variants if v.id != winner.id]
        
        improvements = []
        for other in other_variants:
            if other.ctr > 0:
                improvement = ((winner.ctr - other.ctr) / other.ctr) * 100
            else:
                improvement = 100 if winner.ctr > 0 else 0
            
            improvements.append({
                'variant_name': other.variant_name,
                'improvement_percentage': round(improvement, 2)
            })
        
        improvement_data = {
            'winner': winner,
            'improvements': improvements
        }
    
    # Analyze element impact for combined tests
    element_impact = None
    if test.test_type == 'combined':
        element_impact = _analyze_combined_test_impact(variants)
    
    # Get test logs
    logs = test.logs.all()[:20]
    
    context = {
        'test': test,
        'variants': variants,
        'comparison_data': comparison_data,
        'improvement_data': improvement_data,
        'element_impact': element_impact,
        'logs': logs,
    }
    
    return render(request, 'abtesting/test_results.html', context)


def _analyze_combined_test_impact(variants):
    """
    Analyze which element (thumbnail or title) had greater impact in a combined test.
    
    This function groups variants by thumbnail and title to determine which element
    contributed more to performance differences.
    
    Args:
        variants: QuerySet of TestVariant instances
        
    Returns:
        Dict with impact analysis or None if analysis cannot be performed
    """
    variants_list = list(variants)
    
    if len(variants_list) < 2:
        return None
    
    # Group variants by thumbnail and title
    thumbnail_groups = {}
    title_groups = {}
    
    for variant in variants_list:
        # Group by thumbnail
        thumb_key = variant.thumbnail_url
        if thumb_key not in thumbnail_groups:
            thumbnail_groups[thumb_key] = []
        thumbnail_groups[thumb_key].append(variant)
        
        # Group by title
        title_key = variant.title
        if title_key not in title_groups:
            title_groups[title_key] = []
        title_groups[title_key].append(variant)
    
    # Calculate average CTR for each thumbnail across different titles
    thumbnail_impact = {}
    for thumb_url, thumb_variants in thumbnail_groups.items():
        if len(thumb_variants) > 0:
            avg_ctr = sum(v.ctr for v in thumb_variants) / len(thumb_variants)
            thumbnail_impact[thumb_url] = {
                'avg_ctr': avg_ctr,
                'variant_count': len(thumb_variants),
                'variants': [v.variant_name for v in thumb_variants]
            }
    
    # Calculate average CTR for each title across different thumbnails
    title_impact = {}
    for title_text, title_variants in title_groups.items():
        if len(title_variants) > 0:
            avg_ctr = sum(v.ctr for v in title_variants) / len(title_variants)
            title_impact[title_text] = {
                'avg_ctr': avg_ctr,
                'variant_count': len(title_variants),
                'variants': [v.variant_name for v in title_variants]
            }
    
    # Determine which element had greater impact
    # Calculate variance in CTR for thumbnails and titles
    thumbnail_ctrs = [data['avg_ctr'] for data in thumbnail_impact.values()]
    title_ctrs = [data['avg_ctr'] for data in title_impact.values()]
    
    thumbnail_variance = 0
    title_variance = 0
    
    if len(thumbnail_ctrs) > 1:
        thumb_mean = sum(thumbnail_ctrs) / len(thumbnail_ctrs)
        thumbnail_variance = sum((ctr - thumb_mean) ** 2 for ctr in thumbnail_ctrs) / len(thumbnail_ctrs)
    
    if len(title_ctrs) > 1:
        title_mean = sum(title_ctrs) / len(title_ctrs)
        title_variance = sum((ctr - title_mean) ** 2 for ctr in title_ctrs) / len(title_ctrs)
    
    # Determine primary driver
    if thumbnail_variance > title_variance * 1.2:  # 20% threshold
        primary_driver = 'thumbnail'
        driver_strength = 'strong' if thumbnail_variance > title_variance * 2 else 'moderate'
    elif title_variance > thumbnail_variance * 1.2:
        primary_driver = 'title'
        driver_strength = 'strong' if title_variance > thumbnail_variance * 2 else 'moderate'
    else:
        primary_driver = 'both'
        driver_strength = 'equal'
    
    return {
        'thumbnail_impact': thumbnail_impact,
        'title_impact': title_impact,
        'thumbnail_variance': thumbnail_variance,
        'title_variance': title_variance,
        'primary_driver': primary_driver,
        'driver_strength': driver_strength,
        'analysis_message': _get_impact_message(primary_driver, driver_strength)
    }


def _get_impact_message(primary_driver, driver_strength):
    """Generate a human-readable message about element impact."""
    if primary_driver == 'thumbnail':
        if driver_strength == 'strong':
            return "The thumbnail had a strong impact on performance. Different thumbnails showed significantly different CTRs."
        else:
            return "The thumbnail had a moderate impact on performance. Consider testing more thumbnail variations."
    elif primary_driver == 'title':
        if driver_strength == 'strong':
            return "The title had a strong impact on performance. Different titles showed significantly different CTRs."
        else:
            return "The title had a moderate impact on performance. Consider testing more title variations."
    else:
        return "Both thumbnail and title contributed equally to performance. The combination matters most."
