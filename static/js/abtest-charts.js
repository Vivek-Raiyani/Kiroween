/**
 * A/B Testing Chart Components
 * Reusable chart components for A/B test visualization
 */

// ============================================================================
// Performance Comparison Charts
// ============================================================================

/**
 * Create CTR comparison chart for A/B test variants
 * @param {string} canvasId - Canvas element ID
 * @param {Array} variantNames - Variant names (A, B, C)
 * @param {Array} ctrValues - CTR values for each variant
 * @param {number} winnerIndex - Index of winning variant (-1 if no winner)
 * @returns {Chart} Chart.js instance
 */
function createTestCTRChart(canvasId, variantNames, ctrValues, winnerIndex = -1) {
    return createCTRComparisonChart(canvasId, variantNames, ctrValues, winnerIndex);
}

/**
 * Create clicks vs impressions comparison chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} variantNames - Variant names
 * @param {Array} impressions - Impression counts
 * @param {Array} clicks - Click counts
 * @returns {Chart} Chart.js instance
 */
function createClicksImpressionsChart(canvasId, variantNames, impressions, clicks) {
    return createPerformanceComparisonChart(canvasId, variantNames, {
        impressions: impressions,
        clicks: clicks
    });
}

/**
 * Create views comparison chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} variantNames - Variant names
 * @param {Array} views - View counts
 * @param {number} winnerIndex - Index of winning variant
 * @returns {Chart} Chart.js instance
 */
function createViewsComparisonChart(canvasId, variantNames, views, winnerIndex = -1) {
    const colors = variantNames.map((_, index) => 
        index === winnerIndex ? '#FFD700' : chartColors.secondary
    );
    
    return createBarChart(canvasId, variantNames, [{
        label: 'Views',
        data: views,
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
                    text: 'Views',
                    font: { weight: 'bold' }
                },
                ticks: {
                    callback: function(value) {
                        return formatChartValue(value, 'compact');
                    }
                }
            }
        }
    });
}

// ============================================================================
// CTR Trend Charts
// ============================================================================

/**
 * Create CTR trend over time for all variants
 * @param {string} canvasId - Canvas element ID
 * @param {Array} timestamps - Time points
 * @param {Object} variantData - Object with variant names as keys and CTR arrays as values
 * @returns {Chart} Chart.js instance
 */
function createCTRTrendChart(canvasId, timestamps, variantData) {
    const datasets = Object.keys(variantData).map((variantName, index) => ({
        label: `Variant ${variantName}`,
        data: variantData[variantName],
        borderColor: chartColors.palette[index % chartColors.palette.length],
        backgroundColor: `${chartColors.palette[index % chartColors.palette.length]}1A`,
        borderWidth: 3,
        fill: false,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6
    }));
    
    return createLineChart(canvasId, timestamps, datasets, {
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + '%';
                    }
                }
            }
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
            },
            x: {
                title: {
                    display: true,
                    text: 'Time',
                    font: { weight: 'bold' }
                }
            }
        }
    });
}

/**
 * Create impressions trend over time for all variants
 * @param {string} canvasId - Canvas element ID
 * @param {Array} timestamps - Time points
 * @param {Object} variantData - Object with variant names as keys and impression arrays as values
 * @returns {Chart} Chart.js instance
 */
function createImpressionsTrendChart(canvasId, timestamps, variantData) {
    const datasets = Object.keys(variantData).map((variantName, index) => ({
        label: `Variant ${variantName}`,
        data: variantData[variantName],
        borderColor: chartColors.palette[index % chartColors.palette.length],
        backgroundColor: `${chartColors.palette[index % chartColors.palette.length]}1A`,
        borderWidth: 2,
        fill: true,
        tension: 0.4
    }));
    
    return createLineChart(canvasId, timestamps, datasets, {
        scales: {
            y: {
                title: {
                    display: true,
                    text: 'Impressions',
                    font: { weight: 'bold' }
                },
                ticks: {
                    callback: function(value) {
                        return formatChartValue(value, 'compact');
                    }
                }
            }
        }
    });
}

// ============================================================================
// Multi-Metric Comparison Charts
// ============================================================================

/**
 * Create comprehensive variant comparison chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} variantNames - Variant names
 * @param {Object} metrics - Object with metric names and their values per variant
 * @returns {Chart} Chart.js instance
 */
function createVariantMetricsChart(canvasId, variantNames, metrics) {
    const datasets = Object.keys(metrics).map((metricName, index) => ({
        label: metricName,
        data: metrics[metricName],
        backgroundColor: chartColors.palette[index % chartColors.palette.length],
        borderColor: chartColors.dark,
        borderWidth: 2
    }));
    
    return createBarChart(canvasId, variantNames, datasets, {
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
 * Create radar chart for variant performance across multiple dimensions
 * @param {string} canvasId - Canvas element ID
 * @param {Array} dimensions - Dimension labels (CTR, Views, Engagement, etc.)
 * @param {Object} variantData - Object with variant names as keys and metric arrays as values
 * @returns {Chart} Chart.js instance
 */
function createVariantRadarChart(canvasId, dimensions, variantData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const datasets = Object.keys(variantData).map((variantName, index) => ({
        label: `Variant ${variantName}`,
        data: variantData[variantName],
        borderColor: chartColors.palette[index % chartColors.palette.length],
        backgroundColor: `${chartColors.palette[index % chartColors.palette.length]}33`,
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
    }));
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: dimensions,
            datasets: datasets
        },
        options: {
            ...getDefaultChartOptions(),
            scales: {
                r: {
                    beginAtZero: true,
                    grid: {
                        color: chartColors.grid
                    }
                }
            }
        }
    });
}

// ============================================================================
// Test Progress Visualization
// ============================================================================

/**
 * Create test progress gauge
 * @param {string} canvasId - Canvas element ID
 * @param {number} progress - Progress percentage (0-100)
 * @returns {Chart} Chart.js instance
 */
function createTestProgressGauge(canvasId, progress) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Complete', 'Remaining'],
            datasets: [{
                data: [progress, 100 - progress],
                backgroundColor: [chartColors.success, 'rgba(0, 0, 0, 0.05)'],
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
 * Create variant rotation timeline
 * @param {string} canvasId - Canvas element ID
 * @param {Array} timestamps - Time points
 * @param {Array} activeVariants - Variant names active at each time point
 * @returns {Chart} Chart.js instance
 */
function createRotationTimelineChart(canvasId, timestamps, activeVariants) {
    // Convert variant names to numeric values for visualization
    const uniqueVariants = [...new Set(activeVariants)];
    const variantValues = activeVariants.map(v => uniqueVariants.indexOf(v) + 1);
    
    return createLineChart(canvasId, timestamps, [{
        label: 'Active Variant',
        data: variantValues,
        borderColor: chartColors.primary,
        backgroundColor: 'rgba(220, 38, 38, 0.1)',
        stepped: true,
        fill: true
    }], {
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return 'Variant: ' + uniqueVariants[context.parsed.y - 1];
                    }
                }
            }
        },
        scales: {
            y: {
                title: {
                    display: true,
                    text: 'Variant',
                    font: { weight: 'bold' }
                },
                ticks: {
                    stepSize: 1,
                    callback: function(value) {
                        return uniqueVariants[value - 1] || '';
                    }
                }
            }
        }
    });
}

// ============================================================================
// Statistical Visualization
// ============================================================================

/**
 * Create confidence interval chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} variantNames - Variant names
 * @param {Array} means - Mean CTR values
 * @param {Array} lowerBounds - Lower confidence bounds
 * @param {Array} upperBounds - Upper confidence bounds
 * @returns {Chart} Chart.js instance
 */
function createConfidenceIntervalChart(canvasId, variantNames, means, lowerBounds, upperBounds) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    // Calculate error bars
    const errorBars = means.map((mean, i) => ({
        y: mean,
        yMin: lowerBounds[i],
        yMax: upperBounds[i]
    }));
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: variantNames,
            datasets: [{
                label: 'CTR with 95% CI',
                data: means,
                backgroundColor: chartColors.primary,
                borderColor: chartColors.dark,
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            ...getDefaultChartOptions(),
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            return [
                                'Mean CTR: ' + means[index].toFixed(2) + '%',
                                '95% CI: [' + lowerBounds[index].toFixed(2) + '%, ' + 
                                upperBounds[index].toFixed(2) + '%]'
                            ];
                        }
                    }
                }
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
        }
    });
}

/**
 * Create improvement percentage chart
 * @param {string} canvasId - Canvas element ID
 * @param {Array} comparisonLabels - Comparison labels (e.g., "A vs B", "A vs C")
 * @param {Array} improvements - Improvement percentages
 * @returns {Chart} Chart.js instance
 */
function createImprovementChart(canvasId, comparisonLabels, improvements) {
    const colors = improvements.map(value => 
        value > 0 ? chartColors.success : chartColors.primary
    );
    
    return createBarChart(canvasId, comparisonLabels, [{
        label: 'Improvement (%)',
        data: improvements,
        backgroundColor: colors,
        borderColor: chartColors.dark
    }], {
        indexAxis: 'y', // Horizontal bars
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const value = context.parsed.x;
                        return (value > 0 ? '+' : '') + value.toFixed(1) + '% improvement';
                    }
                }
            }
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Improvement (%)',
                    font: { weight: 'bold' }
                },
                ticks: {
                    callback: function(value) {
                        return (value > 0 ? '+' : '') + value + '%';
                    }
                }
            }
        }
    });
}

// ============================================================================
// Combined Test Visualization
// ============================================================================

/**
 * Create element impact comparison for combined tests
 * @param {string} canvasId - Canvas element ID
 * @param {Array} elements - Element names (Thumbnail, Title)
 * @param {Array} avgCTR - Average CTR for each element
 * @param {Array} variance - Variance for each element
 * @returns {Chart} Chart.js instance
 */
function createElementImpactChart(canvasId, elements, avgCTR, variance) {
    return createBarChart(canvasId, elements, [
        {
            label: 'Average CTR',
            data: avgCTR,
            backgroundColor: chartColors.primary,
            borderColor: chartColors.dark,
            yAxisID: 'y'
        },
        {
            label: 'Variance (Impact)',
            data: variance,
            backgroundColor: chartColors.warning,
            borderColor: chartColors.dark,
            yAxisID: 'y1'
        }
    ], {
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: 'Average CTR (%)',
                    font: { weight: 'bold' }
                },
                ticks: {
                    callback: function(value) {
                        return value.toFixed(1) + '%';
                    }
                }
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: 'Variance',
                    font: { weight: 'bold' }
                },
                grid: {
                    drawOnChartArea: false
                }
            }
        }
    });
}

/**
 * Create thumbnail-title combination heatmap (simplified as grouped bar)
 * @param {string} canvasId - Canvas element ID
 * @param {Array} combinations - Combination labels
 * @param {Array} ctrValues - CTR for each combination
 * @returns {Chart} Chart.js instance
 */
function createCombinationHeatmapChart(canvasId, combinations, ctrValues) {
    const maxCTR = Math.max(...ctrValues);
    const colors = ctrValues.map(value => {
        const ratio = value / maxCTR;
        if (ratio >= 0.9) return chartColors.success;
        if (ratio >= 0.7) return chartColors.warning;
        return chartColors.primary;
    });
    
    return createBarChart(canvasId, combinations, [{
        label: 'CTR',
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

// ============================================================================
// Chart Update Helpers
// ============================================================================

/**
 * Update A/B test charts with new data
 * @param {Object} charts - Object containing chart instances
 * @param {Object} newData - New data to update charts with
 */
function updateABTestCharts(charts, newData) {
    if (charts.ctr && newData.ctr) {
        updateChartData(charts.ctr, newData.variantNames, [{
            label: 'CTR (%)',
            data: newData.ctr.values,
            backgroundColor: newData.ctr.colors || chartColors.primary
        }]);
    }
    
    if (charts.performance && newData.performance) {
        updateChartData(charts.performance, newData.variantNames, [
            {
                label: 'Impressions',
                data: newData.performance.impressions,
                backgroundColor: 'rgba(128, 128, 128, 0.5)'
            },
            {
                label: 'Clicks',
                data: newData.performance.clicks,
                backgroundColor: chartColors.primary
            }
        ]);
    }
}

/**
 * Initialize all A/B test charts on a page
 * @param {Object} data - Data object containing all chart data
 * @returns {Object} Object containing all chart instances
 */
function initializeABTestCharts(data) {
    const charts = {};
    
    // CTR comparison
    if (document.getElementById('ctrChart') && data.ctr) {
        charts.ctr = createTestCTRChart(
            'ctrChart', 
            data.variantNames, 
            data.ctr, 
            data.winnerIndex || -1
        );
    }
    
    // Clicks vs Impressions
    if (document.getElementById('clicksChart') && data.impressions && data.clicks) {
        charts.performance = createClicksImpressionsChart(
            'clicksChart',
            data.variantNames,
            data.impressions,
            data.clicks
        );
    }
    
    // CTR trend
    if (document.getElementById('ctrTrendChart') && data.ctrTrend) {
        charts.ctrTrend = createCTRTrendChart(
            'ctrTrendChart',
            data.timestamps,
            data.ctrTrend
        );
    }
    
    // Test progress
    if (document.getElementById('progressChart') && data.progress !== undefined) {
        charts.progress = createTestProgressGauge('progressChart', data.progress);
    }
    
    return charts;
}
