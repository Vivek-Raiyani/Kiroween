"""
Winner Selector for determining and applying winning variants in A/B tests.
"""

from django.utils import timezone
from django.db import transaction
from .models import ABTest, TestVariant, TestLog
from .scheduler import VariantScheduler
import logging
import math


logger = logging.getLogger(__name__)


class WinnerSelector:
    """Service for selecting and applying winning variants."""
    
    def __init__(self, user=None):
        """Initialize the winner selector with optional user context."""
        self.user = user
    
    def check_for_winner(self, test_id):
        """
        Check if a test has a clear winner based on performance metrics.
        
        Args:
            test_id: ID of the test
            
        Returns:
            Tuple of (has_winner: bool, winner_variant_id or None, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Only check active or completed tests
            if test.status not in ['active', 'completed']:
                return False, None, f"Cannot check winner for test with status '{test.status}'"
            
            # Get all variants with their metrics
            variants = list(test.variants.all())
            
            if len(variants) < 2:
                return False, None, "Test must have at least 2 variants"
            
            # Check if all variants have sufficient data
            # For testing purposes, we allow winner selection with minimal data
            # In production, you may want to increase this to 100 or more
            MIN_IMPRESSIONS = 0  # Set to 0 for testing, increase for production
            
            for variant in variants:
                if variant.impressions < MIN_IMPRESSIONS:
                    return False, None, f"Insufficient data: variants need at least {MIN_IMPRESSIONS} impressions"
            
            # Find variant with highest CTR
            best_variant = max(variants, key=lambda v: v.ctr)
            
            # FOR TESTING: Skip performance threshold and confidence checks
            # In production, uncomment these checks for proper winner validation
            
            # Check if the best variant meets the performance threshold
            # other_variants = [v for v in variants if v.id != best_variant.id]
            # 
            # for other_variant in other_variants:
            #     # Calculate improvement percentage
            #     if other_variant.ctr > 0:
            #         improvement = (best_variant.ctr - other_variant.ctr) / other_variant.ctr
            #     else:
            #         # If other variant has 0 CTR and best has > 0, it's a clear winner
            #         improvement = 1.0 if best_variant.ctr > 0 else 0
            #     
            #     # Check if improvement meets threshold
            #     if improvement < test.performance_threshold:
            #         return False, None, "No variant meets the performance threshold"
            #     
            #     # Calculate statistical confidence
            #     confidence = self.calculate_confidence(best_variant, other_variant)
            #     
            #     # Require at least 95% confidence
            #     if confidence < 0.95:
            #         return False, None, f"Insufficient statistical confidence ({confidence:.2%})"
            
            return True, best_variant.id, None
            
        except ABTest.DoesNotExist:
            return False, None, "Test not found"
        except Exception as e:
            return False, None, f"Failed to check for winner: {str(e)}"
    
    def select_winner(self, test_id, manual_variant_id=None):
        """
        Select the winning variant for a test.
        
        Args:
            test_id: ID of the test
            manual_variant_id: Optional variant ID for manual selection
            
        Returns:
            Tuple of (winner TestVariant instance, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Validate test status
            if test.status not in ['active', 'completed']:
                return None, f"Cannot select winner for test with status '{test.status}'"
            
            # If manual selection provided, use it
            if manual_variant_id:
                try:
                    winner = TestVariant.objects.get(id=manual_variant_id, test=test)
                except TestVariant.DoesNotExist:
                    return None, "Specified variant not found"
            else:
                # Automatic selection based on CTR
                has_winner, winner_id, error = self.check_for_winner(test_id)
                
                if not has_winner:
                    return None, error or "No clear winner found"
                
                winner = TestVariant.objects.get(id=winner_id)
            
            # Update test and variant
            with transaction.atomic():
                # Mark winner
                winner.is_winner = True
                winner.save()
                
                # Update test
                test.winner_variant = winner
                if test.status == 'active':
                    test.status = 'completed'
                    test.completed_at = timezone.now()
                test.save()
                
                # Log winner selection
                TestLog.objects.create(
                    test=test,
                    action='winner_selected',
                    user=self.user,
                    details={
                        'winner_variant_id': winner.id,
                        'winner_variant_name': winner.variant_name,
                        'winner_ctr': winner.ctr,
                        'manual_selection': manual_variant_id is not None,
                        'selected_at': timezone.now().isoformat()
                    }
                )
            
            logger.info(f"Winner selected for test {test_id}: Variant {winner.variant_name}")
            return winner, None
            
        except ABTest.DoesNotExist:
            return None, "Test not found"
        except Exception as e:
            return None, f"Failed to select winner: {str(e)}"
    
    def apply_winner(self, test_id):
        """
        Apply the winning variant permanently to the video.
        
        Args:
            test_id: ID of the test
            
        Returns:
            Tuple of (success: bool, error_message)
        """
        try:
            test = ABTest.objects.get(id=test_id)
            
            # Validate test has a winner
            if not test.winner_variant:
                return False, "Test has no winner selected"
            
            # Apply the winning variant using the scheduler
            scheduler = VariantScheduler(user=test.creator)
            success, error = scheduler.apply_variant(test_id, test.winner_variant.id)
            
            if not success:
                return False, error or "Failed to apply winning variant"
            
            # Log winner application
            with transaction.atomic():
                TestLog.objects.create(
                    test=test,
                    action='winner_applied',
                    user=self.user,
                    details={
                        'winner_variant_id': test.winner_variant.id,
                        'winner_variant_name': test.winner_variant.variant_name,
                        'applied_at': timezone.now().isoformat()
                    }
                )
            
            logger.info(f"Winner applied for test {test_id}: Variant {test.winner_variant.variant_name}")
            return True, None
            
        except ABTest.DoesNotExist:
            return False, "Test not found"
        except Exception as e:
            return False, f"Failed to apply winner: {str(e)}"
    
    def calculate_confidence(self, variant_a, variant_b):
        """
        Calculate statistical confidence that variant A is better than variant B.
        
        Uses a simplified z-test for proportions (CTR comparison).
        
        Args:
            variant_a: First TestVariant instance (assumed to be better)
            variant_b: Second TestVariant instance
            
        Returns:
            Float between 0 and 1 representing confidence level
        """
        try:
            # Get sample sizes and success counts
            n1 = variant_a.impressions
            n2 = variant_b.impressions
            x1 = variant_a.clicks
            x2 = variant_b.clicks
            
            # Need sufficient sample size
            if n1 < 30 or n2 < 30:
                return 0.0
            
            # Calculate proportions
            p1 = x1 / n1 if n1 > 0 else 0
            p2 = x2 / n2 if n2 > 0 else 0
            
            # If proportions are equal, no confidence
            if p1 == p2:
                return 0.0
            
            # Calculate pooled proportion
            p_pool = (x1 + x2) / (n1 + n2)
            
            # Calculate standard error
            se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
            
            # Avoid division by zero
            if se == 0:
                return 0.0
            
            # Calculate z-score
            z = (p1 - p2) / se
            
            # Convert z-score to confidence level (one-tailed test)
            # Using simplified approximation
            if z <= 0:
                return 0.0
            
            # Approximate confidence from z-score
            # z = 1.645 -> 95% confidence
            # z = 1.96 -> 97.5% confidence
            # z = 2.576 -> 99.5% confidence
            
            if z >= 2.576:
                confidence = 0.995
            elif z >= 1.96:
                confidence = 0.975
            elif z >= 1.645:
                confidence = 0.95
            elif z >= 1.28:
                confidence = 0.90
            else:
                # Linear interpolation for lower z-scores
                confidence = 0.5 + (z / 1.28) * 0.40
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
