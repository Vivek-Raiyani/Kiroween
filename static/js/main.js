// Main JavaScript for Creator Backoffice Platform

$(document).ready(function() {
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
