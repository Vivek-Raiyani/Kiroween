// Main JavaScript for Creator Backoffice Platform

$(document).ready(function() {
    // Initialize view management system
    initializeViewManagement();
    
    // Initialize mobile menu
    initializeMobileMenu();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize confirmation dialogs
    initializeConfirmDialogs();
    
    // Auto-dismiss alerts after 8 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 8000);

    // Loading spinner for form submissions with custom messages
    $('form').on('submit', function(e) {
        const $form = $(this);
        const loadingMessage = $form.data('loading-message') || 'Processing...';
        
        // Don't show spinner for search forms
        if ($form.hasClass('no-spinner')) {
            return;
        }
        
        // Validate form before submission
        if (!validateForm($form)) {
            e.preventDefault();
            return false;
        }
        
        showLoadingSpinner(loadingMessage);
        
        // Add loading state to submit button
        const $submitBtn = $form.find('button[type="submit"]');
        $submitBtn.addClass('btn-loading').prop('disabled', true);
    });

    // File upload drag and drop
    $('.upload-area').on('dragover', function(e) {
        e.preventDefault();
        $(this).addClass('dragover');
    });

    $('.upload-area').on('dragleave', function(e) {
        e.preventDefault();
        $(this).removeClass('dragover');
    });

    $('.upload-area').on('drop', function(e) {
        e.preventDefault();
        $(this).removeClass('dragover');
        var files = e.originalEvent.dataTransfer.files;
        handleFileUpload(files);
    });

    // Enhanced form validation with better feedback
    $('input, textarea, select').on('blur', function() {
        validateField($(this));
    });

    // Real-time validation for required fields
    $('input[required], textarea[required], select[required]').on('input change', function() {
        const $field = $(this);
        if ($field.val()) {
            $field.removeClass('is-invalid').addClass('is-valid');
            $field.siblings('.invalid-feedback').hide();
        }
    });

    // File size validation
    $('input[type="file"]').on('change', function() {
        const file = this.files[0];
        if (file) {
            const maxSize = $(this).data('max-size') || (5 * 1024 * 1024 * 1024); // 5GB default
            if (file.size > maxSize) {
                const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(0);
                showAlert(`File size exceeds the maximum limit of ${maxSizeMB}MB`, 'danger');
                $(this).val('');
                return false;
            }
            
            // Show file name and size
            const fileName = file.name;
            const fileSize = formatFileSize(file.size);
            $(this).siblings('.file-info').remove();
            $(this).after(`<div class="file-info text-muted mt-2"><i class="bi bi-file-earmark"></i> ${fileName} (${fileSize})</div>`);
        }
    });
    
    // Search form enhancements
    $('.search-form input[type="text"]').on('input', debounce(function() {
        const query = $(this).val();
        if (query.length > 2) {
            // Could trigger live search here
            $(this).addClass('is-valid');
        }
    }, 300));
    
    // Table row click to navigate
    $('.table-hover tbody tr[data-href]').on('click', function() {
        window.location = $(this).data('href');
    });
    
    // Keyboard shortcuts
    $(document).on('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            $('input[type="search"], input[name="q"]').first().focus();
        }
    });
});

// Show loading spinner with custom message
function showLoadingSpinner(message) {
    message = message || 'Loading...';
    
    if ($('.spinner-overlay').length === 0) {
        $('body').append(`
            <div class="spinner-overlay show">
                <div class="spinner-border text-light" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="loading-text">${message}</div>
            </div>
        `);
    } else {
        $('.spinner-overlay .loading-text').text(message);
        $('.spinner-overlay').addClass('show');
    }
}

// Hide loading spinner
function hideLoadingSpinner() {
    $('.spinner-overlay').removeClass('show');
    $('.btn-loading').removeClass('btn-loading').prop('disabled', false);
}

// Handle file upload
function handleFileUpload(files) {
    // This will be implemented in the file upload functionality
    console.log('Files to upload:', files);
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize custom confirmation dialogs
function initializeConfirmDialogs() {
    $('.confirm-action').on('click', function(e) {
        e.preventDefault();
        const $btn = $(this);
        const message = $btn.data('confirm-message') || 'Are you sure you want to perform this action?';
        const title = $btn.data('confirm-title') || 'Confirm Action';
        const confirmText = $btn.data('confirm-text') || 'Confirm';
        const cancelText = $btn.data('cancel-text') || 'Cancel';
        
        showConfirmDialog(title, message, confirmText, cancelText, function() {
            // If it's a form button, submit the form
            if ($btn.closest('form').length) {
                $btn.closest('form').off('submit').submit();
            } else if ($btn.attr('href')) {
                window.location = $btn.attr('href');
            }
        });
    });
}

// Show custom confirmation dialog
function showConfirmDialog(title, message, confirmText, cancelText, onConfirm) {
    const dialogHtml = `
        <div class="confirm-dialog show">
            <div class="confirm-dialog-content">
                <h5 class="mb-3">${title}</h5>
                <p>${message}</p>
                <div class="confirm-dialog-buttons">
                    <button class="btn btn-secondary confirm-cancel">${cancelText}</button>
                    <button class="btn btn-danger confirm-ok">${confirmText}</button>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(dialogHtml);
    
    $('.confirm-ok').on('click', function() {
        $('.confirm-dialog').remove();
        if (onConfirm) onConfirm();
    });
    
    $('.confirm-cancel').on('click', function() {
        $('.confirm-dialog').remove();
    });
    
    // Close on background click
    $('.confirm-dialog').on('click', function(e) {
        if ($(e.target).hasClass('confirm-dialog')) {
            $('.confirm-dialog').remove();
        }
    });
}

// Validate entire form
function validateForm($form) {
    let isValid = true;
    
    $form.find('input[required], textarea[required], select[required]').each(function() {
        if (!validateField($(this))) {
            isValid = false;
        }
    });
    
    if (!isValid) {
        showAlert('Please fill in all required fields correctly.', 'danger');
        // Scroll to first invalid field
        const $firstInvalid = $form.find('.is-invalid').first();
        if ($firstInvalid.length) {
            $('html, body').animate({
                scrollTop: $firstInvalid.offset().top - 100
            }, 300);
        }
    }
    
    return isValid;
}

// Validate individual field
function validateField($field) {
    const value = $field.val();
    const fieldType = $field.attr('type');
    let isValid = true;
    let errorMessage = '';
    
    // Check if required
    if ($field.prop('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required.';
    }
    
    // Email validation
    if (fieldType === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address.';
        }
    }
    
    // URL validation
    if (fieldType === 'url' && value) {
        try {
            new URL(value);
        } catch {
            isValid = false;
            errorMessage = 'Please enter a valid URL.';
        }
    }
    
    // Min/max length
    const minLength = $field.attr('minlength');
    const maxLength = $field.attr('maxlength');
    if (minLength && value.length < minLength) {
        isValid = false;
        errorMessage = `Minimum length is ${minLength} characters.`;
    }
    if (maxLength && value.length > maxLength) {
        isValid = false;
        errorMessage = `Maximum length is ${maxLength} characters.`;
    }
    
    // Update field state
    if (isValid) {
        $field.removeClass('is-invalid').addClass('is-valid');
        $field.siblings('.invalid-feedback').remove();
    } else {
        $field.removeClass('is-valid').addClass('is-invalid');
        $field.siblings('.invalid-feedback').remove();
        $field.after(`<div class="invalid-feedback d-block">${errorMessage}</div>`);
    }
    
    return isValid;
}

// Show upload progress
function showUploadProgress(percent) {
    let $progress = $('.upload-progress');
    if ($progress.length === 0) {
        $progress = $(`
            <div class="upload-progress show">
                <div class="progress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" 
                         style="width: 0%"
                         aria-valuenow="0" 
                         aria-valuemin="0" 
                         aria-valuemax="100">0%</div>
                </div>
            </div>
        `);
        $('form').append($progress);
    }
    
    $progress.addClass('show');
    $progress.find('.progress-bar')
        .css('width', percent + '%')
        .attr('aria-valuenow', percent)
        .text(percent + '%');
}

// Hide upload progress
function hideUploadProgress() {
    $('.upload-progress').removeClass('show');
}

// Retry mechanism for failed operations
function setupRetryButton(selector, retryFunction) {
    $(selector).on('click', function(e) {
        e.preventDefault();
        const $btn = $(this);
        $btn.prop('disabled', true).text('Retrying...');
        
        retryFunction().then(function() {
            $btn.prop('disabled', false).text('Retry');
        }).catch(function() {
            $btn.prop('disabled', false).text('Retry');
        });
    });
}

// Show alert message
function showAlert(message, type) {
    type = type || 'info';
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('.container').first().prepend(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Get file type icon
function getFileTypeIcon(mimeType) {
    if (!mimeType) return 'bi-file-earmark';
    
    if (mimeType.startsWith('video/')) return 'bi-file-play';
    if (mimeType.startsWith('image/')) return 'bi-file-image';
    if (mimeType.startsWith('audio/')) return 'bi-file-music';
    if (mimeType.includes('pdf')) return 'bi-file-pdf';
    if (mimeType.includes('word') || mimeType.includes('document')) return 'bi-file-word';
    if (mimeType.includes('sheet') || mimeType.includes('excel')) return 'bi-file-excel';
    if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) return 'bi-file-ppt';
    if (mimeType.includes('zip') || mimeType.includes('rar') || mimeType.includes('archive')) return 'bi-file-zip';
    if (mimeType.includes('text')) return 'bi-file-text';
    
    return 'bi-file-earmark';
}

// Get file type color class
function getFileTypeColor(mimeType) {
    if (!mimeType) return 'default';
    
    if (mimeType.startsWith('video/')) return 'video';
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('audio/')) return 'audio';
    if (mimeType.includes('document') || mimeType.includes('text')) return 'document';
    if (mimeType.includes('zip') || mimeType.includes('rar')) return 'archive';
    
    return 'default';
}

// Add breadcrumb navigation
function addBreadcrumb(items) {
    const breadcrumbHtml = `
        <nav aria-label="breadcrumb">
            <ol class="breadcrumb">
                ${items.map((item, index) => {
                    if (index === items.length - 1) {
                        return `<li class="breadcrumb-item active" aria-current="page">${item.text}</li>`;
                    } else {
                        return `<li class="breadcrumb-item"><a href="${item.url}">${item.text}</a></li>`;
                    }
                }).join('')}
            </ol>
        </nav>
    `;
    
    $('main .container').prepend(breadcrumbHtml);
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showAlert('Copied to clipboard!', 'success');
        }).catch(function() {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showAlert('Copied to clipboard!', 'success');
    } catch (err) {
        showAlert('Failed to copy to clipboard', 'danger');
    }
    
    document.body.removeChild(textArea);
}

// Smooth scroll to element
function scrollToElement(selector, offset) {
    offset = offset || 100;
    const $element = $(selector);
    
    if ($element.length) {
        $('html, body').animate({
            scrollTop: $element.offset().top - offset
        }, 500);
    }
}

// Check if element is in viewport
function isInViewport($element) {
    const elementTop = $element.offset().top;
    const elementBottom = elementTop + $element.outerHeight();
    const viewportTop = $(window).scrollTop();
    const viewportBottom = viewportTop + $(window).height();
    
    return elementBottom > viewportTop && elementTop < viewportBottom;
}

// Lazy load images
function lazyLoadImages() {
    $('img[data-src]').each(function() {
        const $img = $(this);
        if (isInViewport($img)) {
            $img.attr('src', $img.data('src'));
            $img.removeAttr('data-src');
        }
    });
}

// Initialize lazy loading on scroll
$(window).on('scroll', debounce(lazyLoadImages, 100));
$(document).ready(lazyLoadImages);

// ============================================================================
// View Management System
// ============================================================================

/**
 * Initialize view management system
 * Sets up navigation handlers and manages view switching
 */
function initializeViewManagement() {
    // Set initial active state based on current URL
    setInitialActiveState();
    
    // Convert Django messages to toasts
    convertDjangoMessagesToToasts();
    
    // Note: Navigation links use Django routing (href attributes)
    // The active state is managed by setInitialActiveState() based on current URL
}

// Navigation functions removed - using Django routing instead
// Active state is managed by setInitialActiveState() based on current URL

/**
 * Set initial active state based on current URL or page
 */
function setInitialActiveState() {
    // Try to determine active view from current URL path
    const path = window.location.pathname;
    
    // Remove active class from all nav links first
    $('.nav-link').removeClass('active');
    
    // Find the nav link that matches the current path
    $('.nav-link').each(function() {
        const $link = $(this);
        const href = $link.attr('href');
        
        // Check if the current path matches or starts with the link's href
        if (href && (path === href || path.startsWith(href + '/'))) {
            $link.addClass('active');
        }
    });
    
    // If no exact match found, try broader matching
    if ($('.nav-link.active').length === 0) {
        let matchedLink = null;
        
        // Map URL paths to navigation links
        if (path.includes('/dashboard')) {
            matchedLink = $('.nav-link[data-target="dashboard"]');
        } else if (path.includes('/analytics')) {
            if (path.includes('/channel')) {
                matchedLink = $('.nav-link[data-target="channel-analytics"]');
            } else if (path.includes('/competitor')) {
                matchedLink = $('.nav-link[data-target="competitor-analysis"]');
            } else if (path.includes('/seo')) {
                matchedLink = $('.nav-link[data-target="seo-insights"]');
            } else if (path.includes('/posting')) {
                matchedLink = $('.nav-link[data-target="posting-recommendations"]');
            } else {
                matchedLink = $('.nav-link[data-target="analytics-dashboard"]');
            }
        } else if (path.includes('/abtesting') || path.includes('/abtest')) {
            matchedLink = $('.nav-link[data-target="abtesting"]');
        } else if (path.includes('/files')) {
            matchedLink = $('.nav-link[data-target="files"]');
        } else if (path.includes('/approvals')) {
            if (path.includes('/pending')) {
                matchedLink = $('.nav-link[data-target="approvals"]');
            } else if (path.includes('/youtube')) {
                matchedLink = $('.nav-link[data-target="youtube-uploads"]');
            } else if (path.includes('/direct')) {
                matchedLink = $('.nav-link[data-target="direct-upload"]');
            } else {
                matchedLink = $('.nav-link[data-target="requests"]');
            }
        } else if (path.includes('/team')) {
            matchedLink = $('.nav-link[data-target="team"]');
        } else if (path.includes('/integrations')) {
            matchedLink = $('.nav-link[data-target="integrations"]');
        }
        
        // Add active class to matched link
        if (matchedLink && matchedLink.length > 0) {
            matchedLink.addClass('active');
        }
    }
}

/**
 * Convert Django messages to toast notifications
 */
function convertDjangoMessagesToToasts() {
    const $djangoMessages = $('.django-messages .message');
    
    $djangoMessages.each(function() {
        const $message = $(this);
        const text = $message.text().trim();
        const level = $message.data('level') || 'info';
        
        // Map Django message levels to toast types
        let toastType = 'info';
        if (level.includes('success')) {
            toastType = 'success';
        } else if (level.includes('error') || level.includes('danger')) {
            toastType = 'error';
        } else if (level.includes('warning')) {
            toastType = 'warning';
        }
        
        // Show toast
        showToast(text, toastType);
    });
    
    // Remove Django messages container
    $('.django-messages').remove();
}

/**
 * Show toast notification
 * @param {string} message - The message to display
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
 */
function showToast(message, type = 'info') {
    const $container = $('.toast-container');
    
    // Limit to 5 toasts
    const $existingToasts = $container.find('.toast');
    if ($existingToasts.length >= 5) {
        $existingToasts.first().remove();
    }
    
    // Icon mapping
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const icon = icons[type] || icons.info;
    
    // Role mapping for ARIA
    const roles = {
        success: 'status',
        error: 'alert',
        warning: 'alert',
        info: 'status'
    };
    
    const role = roles[type] || 'status';
    
    // Create toast element with proper ARIA attributes
    const $toast = $(`
        <div class="toast toast-${type}" role="${role}" aria-live="${type === 'error' || type === 'warning' ? 'assertive' : 'polite'}">
            <i class="fas ${icon}" aria-hidden="true"></i>
            <span class="toast-message">${message}</span>
            <button class="toast-close" aria-label="Close notification" tabindex="0">&times;</button>
        </div>
    `);
    
    // Add to container
    $container.append($toast);
    
    // Trigger animation
    setTimeout(() => {
        $toast.addClass('show');
    }, 10);
    
    // Auto-dismiss after 5 seconds
    const dismissTimeout = setTimeout(() => {
        dismissToast($toast);
    }, 5000);
    
    // Manual close button
    $toast.find('.toast-close').on('click', function() {
        clearTimeout(dismissTimeout);
        dismissToast($toast);
    });
    
    // Keyboard support for close button
    $toast.find('.toast-close').on('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            clearTimeout(dismissTimeout);
            dismissToast($toast);
        }
    });
}

/**
 * Dismiss a toast notification
 * @param {jQuery} $toast - The toast element to dismiss
 */
function dismissToast($toast) {
    $toast.removeClass('show').addClass('hiding');
    
    setTimeout(() => {
        $toast.remove();
    }, 300);
}

// Browser back/forward buttons work automatically with Django routing

// ============================================================================
// Mobile Menu Management
// ============================================================================

/**
 * Initialize mobile menu functionality
 * Sets up toggle button, overlay, and navigation handlers
 */
function initializeMobileMenu() {
    const $sidebar = $('#sidebar');
    const $mobileToggle = $('#mobileMenuToggle');
    const $mobileOverlay = $('#mobileOverlay');
    
    // Toggle menu on button click
    $mobileToggle.on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        toggleMobileMenu();
    });
    
    // Close menu when overlay is clicked
    $mobileOverlay.on('click', function() {
        closeMobileMenu();
    });
    
    // Close menu when navigation link is clicked
    $('.sidebar .nav-link').on('click', function() {
        // Only close on mobile
        if (window.innerWidth <= 768) {
            closeMobileMenu();
        }
    });
    
    // Close menu on escape key
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape' && $sidebar.hasClass('mobile-open')) {
            closeMobileMenu();
            // Return focus to toggle button
            $mobileToggle.focus();
        }
    });
    
    // Keyboard navigation for sidebar
    initializeKeyboardNavigation();
    
    // Handle window resize
    let resizeTimer;
    $(window).on('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            // Close mobile menu if window is resized to desktop
            if (window.innerWidth > 768 && $sidebar.hasClass('mobile-open')) {
                closeMobileMenu();
            }
        }, 250);
    });
}

/**
 * Toggle mobile menu open/closed
 */
function toggleMobileMenu() {
    const $sidebar = $('#sidebar');
    const $mobileOverlay = $('#mobileOverlay');
    const $mobileToggle = $('#mobileMenuToggle');
    
    if ($sidebar.hasClass('mobile-open')) {
        closeMobileMenu();
    } else {
        openMobileMenu();
    }
}

/**
 * Open mobile menu
 */
function openMobileMenu() {
    const $sidebar = $('#sidebar');
    const $mobileOverlay = $('#mobileOverlay');
    const $mobileToggle = $('#mobileMenuToggle');
    
    $sidebar.addClass('mobile-open');
    $mobileOverlay.addClass('show');
    $mobileToggle.find('i').removeClass('fa-bars').addClass('fa-times');
    
    // Update ARIA attributes
    $mobileToggle.attr('aria-expanded', 'true');
    $mobileOverlay.attr('aria-hidden', 'false');
    
    // Prevent body scroll when menu is open
    $('body').css('overflow', 'hidden');
    
    // Set focus to first navigation link for accessibility
    setTimeout(function() {
        $('.sidebar .nav-link').first().focus();
    }, 300);
}

/**
 * Close mobile menu
 */
function closeMobileMenu() {
    const $sidebar = $('#sidebar');
    const $mobileOverlay = $('#mobileOverlay');
    const $mobileToggle = $('#mobileMenuToggle');
    
    $sidebar.removeClass('mobile-open');
    $mobileOverlay.removeClass('show');
    $mobileToggle.find('i').removeClass('fa-times').addClass('fa-bars');
    
    // Update ARIA attributes
    $mobileToggle.attr('aria-expanded', 'false');
    $mobileOverlay.attr('aria-hidden', 'true');
    
    // Restore body scroll
    $('body').css('overflow', '');
}

/**
 * Initialize keyboard navigation for sidebar
 * Enables arrow key navigation through menu items
 */
function initializeKeyboardNavigation() {
    const $navLinks = $('.sidebar .nav-link');
    
    $navLinks.on('keydown', function(e) {
        const $current = $(this);
        const currentIndex = $navLinks.index($current);
        let $target = null;
        
        switch(e.key) {
            case 'ArrowDown':
                // Move to next nav link
                e.preventDefault();
                $target = $navLinks.eq(currentIndex + 1);
                if ($target.length) {
                    $target.focus();
                }
                break;
                
            case 'ArrowUp':
                // Move to previous nav link
                e.preventDefault();
                $target = $navLinks.eq(currentIndex - 1);
                if ($target.length) {
                    $target.focus();
                }
                break;
                
            case 'Home':
                // Move to first nav link
                e.preventDefault();
                $navLinks.first().focus();
                break;
                
            case 'End':
                // Move to last nav link
                e.preventDefault();
                $navLinks.last().focus();
                break;
                
            case 'Enter':
            case ' ':
                // Activate link on Enter or Space
                e.preventDefault();
                $current[0].click();
                break;
        }
    });
    
    // Keyboard navigation for buttons
    $('.btn, .toast-close, .logout-btn').on('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            $(this)[0].click();
        }
    });
}

// ============================================================================
// Chart.js Utility Functions
// ============================================================================

// Chart.js default configuration
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif";
    Chart.defaults.color = '#6B7280';
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
}

// Chart color palette matching design system
const chartColors = {
    primary: '#DC2626',        // --accent-red
    secondary: '#EF4444',      // lighter red
    success: '#10B981',        // green
    warning: '#F59E0B',        // orange
    info: '#3B82F6',           // blue
    dark: '#000000',           // --ink
    light: '#FFFFFF',          // --paper
    gray: '#6B7280',           // medium gray
    grid: 'rgba(0, 0, 0, 0.05)',
    
    // Gradient colors for multiple series
    palette: [
        '#DC2626', '#EF4444', '#F87171', '#FCA5A5', '#FEE2E2',
        '#10B981', '#34D399', '#6EE7B7', '#A7F3D0', '#D1FAE5'
    ]
};

/**
 * Create a line chart for trend visualization
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - X-axis labels
 * @param {Array} datasets - Array of dataset objects
 * @param {Object} options - Additional chart options
 * @returns {Chart} Chart.js instance
 */
function createLineChart(canvasId, labels, datasets, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const defaultDatasetOptions = {
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBorderColor: '#fff',
        pointBorderWidth: 2
    };
    
    // Apply default styling to datasets
    datasets = datasets.map((dataset, index) => ({
        ...defaultDatasetOptions,
        borderColor: dataset.borderColor || chartColors.palette[index % chartColors.palette.length],
        backgroundColor: dataset.backgroundColor || `${chartColors.palette[index % chartColors.palette.length]}1A`,
        pointBackgroundColor: dataset.borderColor || chartColors.palette[index % chartColors.palette.length],
        ...dataset
    }));
    
    return new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            ...getDefaultChartOptions(),
            ...options,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: chartColors.grid },
                    ...options.scales?.y
                },
                x: {
                    grid: { display: false },
                    ...options.scales?.x
                }
            }
        }
    });
}

/**
 * Create a bar chart for comparisons
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - X-axis labels
 * @param {Array} datasets - Array of dataset objects
 * @param {Object} options - Additional chart options
 * @returns {Chart} Chart.js instance
 */
function createBarChart(canvasId, labels, datasets, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const defaultDatasetOptions = {
        borderRadius: 6,
        borderSkipped: false,
        borderWidth: 2,
        borderColor: chartColors.dark
    };
    
    // Apply default styling to datasets
    datasets = datasets.map((dataset, index) => ({
        ...defaultDatasetOptions,
        backgroundColor: dataset.backgroundColor || chartColors.palette[index % chartColors.palette.length],
        ...dataset
    }));
    
    return new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            ...getDefaultChartOptions(),
            ...options,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: chartColors.grid },
                    ...options.scales?.y
                },
                x: {
                    grid: { display: false },
                    ...options.scales?.x
                }
            }
        }
    });
}

/**
 * Create a pie/doughnut chart for demographics
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - Segment labels
 * @param {Array} data - Data values
 * @param {Object} options - Additional chart options
 * @returns {Chart} Chart.js instance
 */
function createPieChart(canvasId, labels, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: options.type || 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: chartColors.palette.slice(0, data.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            ...getDefaultChartOptions(),
            ...options,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 12 },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                ...options.plugins
            }
        }
    });
}

/**
 * Get default chart options
 * @returns {Object} Default options object
 */
function getDefaultChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    padding: 15,
                    font: { size: 12, weight: '600' },
                    usePointStyle: true,
                    pointStyle: 'circle'
                }
            },
            tooltip: {
                backgroundColor: '#000',
                padding: 12,
                cornerRadius: 8,
                titleFont: { size: 14, weight: 'bold' },
                bodyFont: { size: 13 },
                displayColors: true,
                boxPadding: 6
            }
        }
    };
}

/**
 * Format number for chart display
 * @param {number} value - Number to format
 * @param {string} type - Format type (number, percent, currency, time)
 * @returns {string} Formatted string
 */
function formatChartValue(value, type = 'number') {
    if (value === null || value === undefined) return '--';
    
    switch (type) {
        case 'percent':
            return value.toFixed(2) + '%';
        case 'currency':
            return '$' + value.toLocaleString();
        case 'time':
            return value.toLocaleString() + ' min';
        case 'compact':
            if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
            if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
            return value.toLocaleString();
        default:
            return value.toLocaleString();
    }
}

/**
 * Create CTR comparison chart for A/B tests
 * @param {string} canvasId - Canvas element ID
 * @param {Array} variantNames - Variant names (A, B, C)
 * @param {Array} ctrValues - CTR values
 * @param {number} winnerIndex - Index of winning variant
 * @returns {Chart} Chart.js instance
 */
function createCTRComparisonChart(canvasId, variantNames, ctrValues, winnerIndex = -1) {
    const colors = variantNames.map((_, index) => 
        index === winnerIndex ? '#FFD700' : chartColors.primary
    );
    
    return createBarChart(canvasId, variantNames, [{
        label: 'CTR (%)',
        data: ctrValues,
        backgroundColor: colors,
        borderColor: chartColors.dark
    }], {
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: {
                title: {
                    display: true,
                    text: 'CTR (%)',
                    font: { weight: 'bold' }
                },
                ticks: {
                    callback: function(value) {
                        return value.toFixed(1) + '%';
                    }
                }
            }
        }
    });
}

/**
 * Create performance comparison chart for A/B tests
 * @param {string} canvasId - Canvas element ID
 * @param {Array} variantNames - Variant names
 * @param {Object} data - Object with impressions and clicks arrays
 * @returns {Chart} Chart.js instance
 */
function createPerformanceComparisonChart(canvasId, variantNames, data) {
    return createBarChart(canvasId, variantNames, [
        {
            label: 'Impressions',
            data: data.impressions,
            backgroundColor: 'rgba(128, 128, 128, 0.5)',
            borderColor: chartColors.dark
        },
        {
            label: 'Clicks',
            data: data.clicks,
            backgroundColor: chartColors.primary,
            borderColor: chartColors.dark
        }
    ], {
        scales: {
            y: {
                ticks: {
                    callback: function(value) {
                        return formatChartValue(value, 'compact');
                    }
                }
            }
        }
    });
}

/**
 * Create subscriber growth chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} dates - Date labels
 * @param {Object} data - Object with gained, lost, and net arrays
 * @returns {Chart} Chart.js instance
 */
function createSubscriberGrowthChart(canvasId, dates, data) {
    return createLineChart(canvasId, dates, [
        {
            label: 'Gained',
            data: data.gained,
            borderColor: chartColors.success,
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            pointRadius: 3,
            pointHoverRadius: 5
        },
        {
            label: 'Lost',
            data: data.lost,
            borderColor: chartColors.primary,
            backgroundColor: 'rgba(220, 38, 38, 0.1)',
            pointRadius: 3,
            pointHoverRadius: 5
        },
        {
            label: 'Net Change',
            data: data.net,
            borderColor: chartColors.warning,
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            fill: false,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderDash: [5, 5]
        }
    ]);
}

/**
 * Create retention curve chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} timestamps - Time points
 * @param {Array} percentages - Retention percentages
 * @returns {Chart} Chart.js instance
 */
function createRetentionChart(canvasId, timestamps, percentages) {
    return createLineChart(canvasId, timestamps, [{
        label: 'Retention %',
        data: percentages,
        borderColor: chartColors.success,
        backgroundColor: 'rgba(16, 185, 129, 0.1)'
    }], {
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: {
                max: 100,
                ticks: {
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }
        }
    });
}

/**
 * Destroy chart instance if it exists
 * @param {string} canvasId - Canvas element ID
 */
function destroyChart(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas && Chart.getChart(canvas)) {
        Chart.getChart(canvas).destroy();
    }
}

/**
 * Update chart data
 * @param {Chart} chart - Chart instance
 * @param {Array} labels - New labels
 * @param {Array} datasets - New datasets
 */
function updateChartData(chart, labels, datasets) {
    if (!chart) return;
    
    chart.data.labels = labels;
    chart.data.datasets = datasets;
    chart.update();
}
