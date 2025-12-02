/**
 * Analytics Chart Components
 * Reusable chart components for YouTube Analytics dashboards
 */

// ============================================================================
// Line Charts for Trends
// ============================================================================

/**
 * Create views trend chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} dates - Date labels
 * @param {Array} views - View counts
 * @returns {Chart} Chart.js instance
 */
function createViewsTrendChart(canvasId, dates, views) {
    return createLineChart(canvasId, dates, [{
        label: 'Views',
        data: views,
        borderColor: chartColors.primary,
        backgroundColor: 'rgba(220, 38, 38, 0.1)',
        pointBackgroundColor: chartColors.primary
    }], {
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return 'Views: ' + formatChartValue(context.parsed.y, 'compact');
                    }
                }
            }
        },
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
 * Create watch time trend chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} dates - Date labels
 * @param {Array} watchTime - Watch time in minutes
 * @returns {Chart} Chart.js instance
 */
function createWatchTimeTrendChart(canvasId, dates, watchTime) {
    return createLineChart(canvasId, dates, [{
        label: 'Watch Time (minutes)',
        data: watchTime,
        borderColor: chartColors.secondary,
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        pointBackgroundColor: chartColors.secondary
    }], {
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return 'Watch Time: ' + formatChartValue(context.parsed.y, 'compact') + ' min';
                    }
                }
            }
        },
        scales: {
            y: {
                ticks: {
                    callback: function(value) {
                        return formatChartValue(value, 'compact') + ' min';
                    }
                }
            }
        }
    });
}

/**
 * Create engagement trend chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} dates - Date labels
 * @param {Array} engagement - Engagement rate percentages
 * @returns {Chart} Chart.js instance
 */
function createEngagementTrendChart(canvasId, dates, engagement) {
    return createBarChart(canvasId, dates, [{
        label: 'Engagement Rate (%)',
        data: engagement,
        backgroundColor: chartColors.success,
        borderColor: chartColors.dark
    }], {
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return 'Engagement: ' + context.parsed.y.toFixed(2) + '%';
                    }
                }
            }
        },
        scales: {
            y: {
                ticks: {
                    callback: function(value) {
                        return value.toFixed(1) + '%';
                    }
                }
            }
        }
    });
}

// ============================================================================
// Bar Charts for Comparisons
// ============================================================================

/**
 * Create top videos comparison chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} videoTitles - Video titles (truncated)
 * @param {Array} views - View counts
 * @returns {Chart} Chart.js instance
 */
function createTopVideosChart(canvasId, videoTitles, views) {
    return createBarChart(canvasId, videoTitles, [{
        label: 'Views',
        data: views,
        backgroundColor: chartColors.primary,
        borderColor: chartColors.dark
    }], {
        indexAxis: 'y', // Horizontal bar chart
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: {
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
 * Create channel metrics comparison chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} dates - Date labels
 * @param {Object} data - Object with multiple metric arrays
 * @returns {Chart} Chart.js instance
 */
function createChannelMetricsChart(canvasId, dates, data) {
    const datasets = [];
    
    if (data.views) {
        datasets.push({
            label: 'Views',
            data: data.views,
            borderColor: chartColors.primary,
            backgroundColor: 'rgba(220, 38, 38, 0.1)',
            yAxisID: 'y'
        });
    }
    
    if (data.subscribers) {
        datasets.push({
            label: 'Subscribers',
            data: data.subscribers,
            borderColor: chartColors.success,
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            yAxisID: 'y1'
        });
    }
    
    return createLineChart(canvasId, dates, datasets, {
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: 'Views',
                    font: { weight: 'bold' }
                }
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: 'Subscribers',
                    font: { weight: 'bold' }
                },
                grid: {
                    drawOnChartArea: false
                }
            }
        }
    });
}

// ============================================================================
// Pie/Doughnut Charts for Demographics
// ============================================================================

/**
 * Create age demographics chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} ageGroups - Age group labels
 * @param {Array} percentages - Percentage values
 * @returns {Chart} Chart.js instance
 */
function createAgeDemographicsChart(canvasId, ageGroups, percentages) {
    return createPieChart(canvasId, ageGroups, percentages, {
        type: 'doughnut',
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.label + ': ' + context.parsed.toFixed(1) + '%';
                    }
                }
            }
        }
    });
}

/**
 * Create gender demographics chart
 * @param {string} canvasId - Canvas element ID
 * @param {Object} data - Object with male and female percentages
 * @returns {Chart} Chart.js instance
 */
function createGenderDemographicsChart(canvasId, data) {
    return createPieChart(canvasId, ['Male', 'Female', 'Other'], 
        [data.male || 0, data.female || 0, data.other || 0], {
        type: 'doughnut',
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.label + ': ' + context.parsed.toFixed(1) + '%';
                    }
                }
            }
        }
    });
}

/**
 * Create geography demographics chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} countries - Country names
 * @param {Array} percentages - Percentage values
 * @returns {Chart} Chart.js instance
 */
function createGeographyChart(canvasId, countries, percentages) {
    return createPieChart(canvasId, countries, percentages, {
        type: 'doughnut',
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.label + ': ' + context.parsed.toFixed(1) + '%';
                    }
                }
            }
        }
    });
}

/**
 * Create traffic sources chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} sources - Traffic source names
 * @param {Array} views - View counts per source
 * @returns {Chart} Chart.js instance
 */
function createTrafficSourcesChart(canvasId, sources, views) {
    return createPieChart(canvasId, sources, views, {
        type: 'doughnut',
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((context.parsed / total) * 100).toFixed(1);
                        return context.label + ': ' + formatChartValue(context.parsed, 'compact') + 
                               ' (' + percentage + '%)';
                    }
                }
            }
        }
    });
}

// ============================================================================
// Specialized Analytics Charts
// ============================================================================

/**
 * Create audience retention chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} timestamps - Time points (e.g., "0:00", "0:30", "1:00")
 * @param {Array} percentages - Retention percentages
 * @returns {Chart} Chart.js instance
 */
function createAudienceRetentionChart(canvasId, timestamps, percentages) {
    return createRetentionChart(canvasId, timestamps, percentages);
}

/**
 * Create subscriber growth chart with gained/lost breakdown
 * @param {string} canvasId - Canvas element ID
 * @param {Array} dates - Date labels
 * @param {Object} data - Object with gained, lost, and net arrays
 * @returns {Chart} Chart.js instance
 */
function createSubscriberGrowthChartWithBreakdown(canvasId, dates, data) {
    return createSubscriberGrowthChart(canvasId, dates, data);
}

/**
 * Create multi-metric comparison chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} dates - Date labels
 * @param {Object} metrics - Object with metric name as key and data array as value
 * @returns {Chart} Chart.js instance
 */
function createMultiMetricChart(canvasId, dates, metrics) {
    const datasets = Object.keys(metrics).map((metricName, index) => ({
        label: metricName,
        data: metrics[metricName],
        borderColor: chartColors.palette[index % chartColors.palette.length],
        backgroundColor: `${chartColors.palette[index % chartColors.palette.length]}1A`
    }));
    
    return createLineChart(canvasId, dates, datasets);
}

/**
 * Create competitor comparison chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} channelNames - Channel names
 * @param {Object} data - Object with metric arrays (subscribers, avgViews, etc.)
 * @returns {Chart} Chart.js instance
 */
function createCompetitorComparisonChart(canvasId, channelNames, data) {
    const datasets = [];
    
    if (data.subscribers) {
        datasets.push({
            label: 'Subscribers',
            data: data.subscribers,
            backgroundColor: chartColors.primary,
            borderColor: chartColors.dark
        });
    }
    
    if (data.avgViews) {
        datasets.push({
            label: 'Avg Views',
            data: data.avgViews,
            backgroundColor: chartColors.success,
            borderColor: chartColors.dark
        });
    }
    
    return createBarChart(canvasId, channelNames, datasets, {
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
 * Create SEO score gauge chart
 * @param {string} canvasId - Canvas element ID
 * @param {number} score - SEO score (0-100)
 * @returns {Chart} Chart.js instance
 */
function createSEOScoreChart(canvasId, score) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    // Determine color based on score
    let color = chartColors.primary;
    if (score >= 80) color = chartColors.success;
    else if (score >= 60) color = chartColors.warning;
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Score', 'Remaining'],
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [color, 'rgba(0, 0, 0, 0.05)'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

/**
 * Create posting time heatmap (simplified as bar chart)
 * @param {string} canvasId - Canvas element ID
 * @param {Array} hours - Hour labels (0-23)
 * @param {Array} engagement - Expected engagement per hour
 * @returns {Chart} Chart.js instance
 */
function createPostingTimeChart(canvasId, hours, engagement) {
    // Color bars based on engagement level
    const colors = engagement.map(value => {
        const max = Math.max(...engagement);
        const ratio = value / max;
        if (ratio >= 0.8) return chartColors.success;
        if (ratio >= 0.5) return chartColors.warning;
        return chartColors.gray;
    });
    
    return createBarChart(canvasId, hours, [{
        label: 'Expected Engagement',
        data: engagement,
        backgroundColor: colors,
        borderColor: chartColors.dark
    }], {
        plugins: {
            legend: { display: false }
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Hour of Day',
                    font: { weight: 'bold' }
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Engagement Score',
                    font: { weight: 'bold' }
                }
            }
        }
    });
}

// ============================================================================
// Chart Update Helpers
// ============================================================================

/**
 * Update analytics dashboard charts with new data
 * @param {Object} charts - Object containing chart instances
 * @param {Object} newData - New data to update charts with
 */
function updateAnalyticsCharts(charts, newData) {
    if (charts.views && newData.views) {
        updateChartData(charts.views, newData.dates, [{
            label: 'Views',
            data: newData.views.data,
            borderColor: chartColors.primary,
            backgroundColor: 'rgba(220, 38, 38, 0.1)'
        }]);
    }
    
    if (charts.watchTime && newData.watchTime) {
        updateChartData(charts.watchTime, newData.dates, [{
            label: 'Watch Time',
            data: newData.watchTime.data,
            borderColor: chartColors.secondary,
            backgroundColor: 'rgba(239, 68, 68, 0.1)'
        }]);
    }
    
    if (charts.engagement && newData.engagement) {
        updateChartData(charts.engagement, newData.dates, [{
            label: 'Engagement',
            data: newData.engagement.data,
            backgroundColor: chartColors.success
        }]);
    }
}

/**
 * Initialize all analytics charts on a page
 * @param {Object} data - Data object containing all chart data
 * @returns {Object} Object containing all chart instances
 */
function initializeAnalyticsCharts(data) {
    const charts = {};
    
    // Views trend
    if (document.getElementById('viewsChart') && data.views) {
        charts.views = createViewsTrendChart('viewsChart', data.dates, data.views);
    }
    
    // Watch time trend
    if (document.getElementById('watchTimeChart') && data.watchTime) {
        charts.watchTime = createWatchTimeTrendChart('watchTimeChart', data.dates, data.watchTime);
    }
    
    // Engagement trend
    if (document.getElementById('engagementChart') && data.engagement) {
        charts.engagement = createEngagementTrendChart('engagementChart', data.dates, data.engagement);
    }
    
    // Subscriber growth
    if (document.getElementById('subscriberChart') && data.subscribers) {
        charts.subscribers = createSubscriberGrowthChartWithBreakdown(
            'subscriberChart', data.dates, data.subscribers
        );
    }
    
    // Retention
    if (document.getElementById('retentionChart') && data.retention) {
        charts.retention = createAudienceRetentionChart(
            'retentionChart', data.retention.timestamps, data.retention.percentages
        );
    }
    
    // Demographics
    if (document.getElementById('demographicsChart') && data.demographics) {
        charts.demographics = createAgeDemographicsChart(
            'demographicsChart', data.demographics.labels, data.demographics.values
        );
    }
    
    return charts;
}
