# Chart.js Integration Guide

This document explains how to use the chart components in the Creator Backoffice Platform.

## Overview

The platform includes three JavaScript files for chart functionality:

1. **main.js** - Core chart utilities and configuration
2. **analytics-charts.js** - Analytics-specific chart components
3. **abtest-charts.js** - A/B testing chart components

## Setup

Chart.js is automatically included in the base template. To use chart components in your templates:

```html
{% block extra_js %}
<!-- Include chart component files as needed -->
<script src="{% static 'js/analytics-charts.js' %}"></script>
<script src="{% static 'js/abtest-charts.js' %}"></script>

<script>
    // Your chart initialization code here
</script>
{% endblock %}
```

## Core Utilities (main.js)

### Chart Colors

```javascript
chartColors.primary    // #DC2626 (red)
chartColors.secondary  // #EF4444 (lighter red)
chartColors.success    // #10B981 (green)
chartColors.warning    // #F59E0B (orange)
chartColors.info       // #3B82F6 (blue)
chartColors.dark       // #000000 (black)
chartColors.light      // #FFFFFF (white)
chartColors.gray       // #6B7280 (gray)
chartColors.palette    // Array of colors for multiple series
```

### Basic Chart Functions

```javascript
// Create a line chart
createLineChart(canvasId, labels, datasets, options)

// Create a bar chart
createBarChart(canvasId, labels, datasets, options)

// Create a pie/doughnut chart
createPieChart(canvasId, labels, data, options)

// Format values for display
formatChartValue(value, type) // types: 'number', 'percent', 'currency', 'time', 'compact'

// Destroy a chart
destroyChart(canvasId)

// Update chart data
updateChartData(chart, labels, datasets)
```

## Analytics Charts (analytics-charts.js)

### Trend Charts

```javascript
// Views trend
createViewsTrendChart('viewsChart', dates, views)

// Watch time trend
createWatchTimeTrendChart('watchTimeChart', dates, watchTime)

// Engagement trend
createEngagementTrendChart('engagementChart', dates, engagement)
```

### Comparison Charts

```javascript
// Top videos
createTopVideosChart('topVideosChart', videoTitles, views)

// Channel metrics (dual axis)
createChannelMetricsChart('metricsChart', dates, {
    views: [100, 200, 300],
    subscribers: [10, 20, 30]
})

// Competitor comparison
createCompetitorComparisonChart('competitorChart', channelNames, {
    subscribers: [1000, 2000, 3000],
    avgViews: [500, 600, 700]
})
```

### Demographics Charts

```javascript
// Age demographics
createAgeDemographicsChart('ageChart', ['18-24', '25-34', '35-44'], [30, 45, 25])

// Gender demographics
createGenderDemographicsChart('genderChart', {
    male: 60,
    female: 35,
    other: 5
})

// Geography
createGeographyChart('geoChart', ['USA', 'UK', 'Canada'], [50, 30, 20])

// Traffic sources
createTrafficSourcesChart('trafficChart', ['Search', 'Suggested', 'Direct'], [1000, 2000, 500])
```

### Specialized Charts

```javascript
// Audience retention
createAudienceRetentionChart('retentionChart', ['0:00', '0:30', '1:00'], [100, 80, 60])

// Subscriber growth with breakdown
createSubscriberGrowthChartWithBreakdown('subChart', dates, {
    gained: [100, 150, 200],
    lost: [20, 30, 25],
    net: [80, 120, 175]
})

// SEO score gauge
createSEOScoreChart('seoChart', 85) // Score 0-100

// Posting time recommendations
createPostingTimeChart('postingChart', ['0', '6', '12', '18'], [20, 50, 80, 60])
```

### Initialize All Analytics Charts

```javascript
const charts = initializeAnalyticsCharts({
    dates: ['Jan', 'Feb', 'Mar'],
    views: [1000, 2000, 3000],
    watchTime: [500, 600, 700],
    engagement: [5.2, 6.1, 7.3],
    subscribers: {
        gained: [100, 150, 200],
        lost: [20, 30, 25],
        net: [80, 120, 175]
    },
    retention: {
        timestamps: ['0:00', '0:30', '1:00'],
        percentages: [100, 80, 60]
    },
    demographics: {
        labels: ['18-24', '25-34', '35-44'],
        values: [30, 45, 25]
    }
});
```

## A/B Test Charts (abtest-charts.js)

### Performance Comparison

```javascript
// CTR comparison
createTestCTRChart('ctrChart', ['A', 'B', 'C'], [5.2, 6.1, 5.8], 1) // Winner index: 1

// Clicks vs Impressions
createClicksImpressionsChart('clicksChart', ['A', 'B'], [1000, 1200], [50, 75])

// Views comparison
createViewsComparisonChart('viewsChart', ['A', 'B', 'C'], [500, 600, 550], 1)
```

### Trend Charts

```javascript
// CTR trend over time
createCTRTrendChart('ctrTrendChart', ['Day 1', 'Day 2', 'Day 3'], {
    'A': [5.0, 5.2, 5.1],
    'B': [5.5, 6.0, 6.1],
    'C': [5.3, 5.4, 5.8]
})

// Impressions trend
createImpressionsTrendChart('impressionsChart', timestamps, {
    'A': [100, 200, 300],
    'B': [150, 250, 350]
})
```

### Test Progress

```javascript
// Progress gauge
createTestProgressGauge('progressChart', 65) // 65% complete

// Rotation timeline
createRotationTimelineChart('timelineChart', 
    ['12:00', '13:00', '14:00', '15:00'],
    ['A', 'A', 'B', 'B']
)
```

### Statistical Charts

```javascript
// Confidence intervals
createConfidenceIntervalChart('ciChart',
    ['A', 'B'],
    [5.2, 6.1],        // means
    [4.8, 5.7],        // lower bounds
    [5.6, 6.5]         // upper bounds
)

// Improvement percentages
createImprovementChart('improvementChart',
    ['A vs B', 'A vs C'],
    [17.3, 11.5]       // improvement percentages
)
```

### Combined Test Charts

```javascript
// Element impact comparison
createElementImpactChart('impactChart',
    ['Thumbnail', 'Title'],
    [5.5, 6.0],        // average CTR
    [0.3, 0.8]         // variance (higher = more impact)
)

// Combination heatmap
createCombinationHeatmapChart('heatmapChart',
    ['Thumb A + Title 1', 'Thumb A + Title 2', 'Thumb B + Title 1'],
    [5.2, 6.1, 5.8]
)
```

### Initialize All A/B Test Charts

```javascript
const charts = initializeABTestCharts({
    variantNames: ['A', 'B', 'C'],
    ctr: [5.2, 6.1, 5.8],
    impressions: [1000, 1200, 1100],
    clicks: [52, 73, 64],
    winnerIndex: 1,
    timestamps: ['Day 1', 'Day 2', 'Day 3'],
    ctrTrend: {
        'A': [5.0, 5.2, 5.1],
        'B': [5.5, 6.0, 6.1],
        'C': [5.3, 5.4, 5.8]
    },
    progress: 65
});
```

## Example Usage in Templates

### Analytics Dashboard

```html
{% block extra_js %}
<script src="{% static 'js/analytics-charts.js' %}"></script>
<script>
    // Initialize charts when DOM is ready
    $(document).ready(function() {
        // Views trend
        createViewsTrendChart('viewsChart', 
            {{ trend_data.dates|safe }}, 
            {{ trend_data.views|safe }}
        );
        
        // Watch time trend
        createWatchTimeTrendChart('watchTimeChart',
            {{ trend_data.dates|safe }},
            {{ trend_data.watch_time|safe }}
        );
        
        // Engagement trend
        createEngagementTrendChart('engagementChart',
            {{ trend_data.dates|safe }},
            {{ trend_data.engagement|safe }}
        );
    });
</script>
{% endblock %}
```

### A/B Test Results

```html
{% block extra_js %}
<script src="{% static 'js/abtest-charts.js' %}"></script>
<script>
    $(document).ready(function() {
        // CTR comparison
        createTestCTRChart('ctrChart',
            {{ comparison_data.variant_names|safe }},
            {{ comparison_data.ctr|safe }},
            {{ winner_index|default:-1 }}
        );
        
        // Performance comparison
        createClicksImpressionsChart('clicksChart',
            {{ comparison_data.variant_names|safe }},
            {{ comparison_data.impressions|safe }},
            {{ comparison_data.clicks|safe }}
        );
    });
</script>
{% endblock %}
```

## Design System Integration

All charts follow the platform's design system:

- **Colors**: Match the manga/comic aesthetic with red accents
- **Fonts**: Use Inter for labels and Oswald for display numbers
- **Borders**: Bold 2-3px borders with dark colors
- **Tooltips**: Black background with rounded corners
- **Animations**: Smooth transitions matching the platform

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Chart.js 4.4.0+
- Responsive and mobile-friendly
- Supports dark mode (via CSS variables)

## Performance Tips

1. **Destroy old charts** before creating new ones:
   ```javascript
   destroyChart('myChart');
   createLineChart('myChart', labels, datasets);
   ```

2. **Update existing charts** instead of recreating:
   ```javascript
   updateChartData(existingChart, newLabels, newDatasets);
   ```

3. **Lazy load charts** for better page performance:
   ```javascript
   if (isInViewport($('#myChart'))) {
       createLineChart('myChart', labels, datasets);
   }
   ```

4. **Use compact formatting** for large numbers:
   ```javascript
   formatChartValue(1500000, 'compact') // "1.5M"
   ```

## Troubleshooting

### Chart not displaying
- Ensure canvas element exists: `<canvas id="myChart"></canvas>`
- Check that Chart.js is loaded before your script
- Verify data is in correct format (arrays, not strings)

### Chart too small/large
- Set explicit height on canvas container:
  ```html
  <div style="height: 300px;">
      <canvas id="myChart"></canvas>
  </div>
  ```

### Colors not matching design
- Use `chartColors` constants from main.js
- Check CSS variables are defined in style.css

### Data not updating
- Use `updateChartData()` instead of recreating chart
- Ensure you're passing new data, not references to old data
