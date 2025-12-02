"""
Export services for analytics and A/B testing data.
Supports CSV and PDF export formats.
Requirements: 13.2, 13.3, 13.4
"""

import csv
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import pandas as pd
from io import BytesIO


class CSVExporter:
    """
    Service for exporting analytics and A/B testing data to CSV format.
    Requirements: 13.2, 13.4
    """
    
    @staticmethod
    def export_video_metrics(video_id: str, metrics_data: List[Dict[str, Any]], 
                            start_date: datetime, end_date: datetime) -> HttpResponse:
        """
        Export video metrics to CSV format.
        
        Args:
            video_id: YouTube video ID
            metrics_data: List of metric dictionaries with date and values
            start_date: Start date for the data range
            end_date: End date for the data range
            
        Returns:
            HttpResponse with CSV file attachment
            
        Requirements: 13.2, 13.4
        """
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f'video_metrics_{video_id}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Video ID',
            'Date',
            'Views',
            'Watch Time (minutes)',
            'Likes',
            'Comments',
            'Shares',
            'CTR (%)',
            'Engagement Rate (%)'
        ])
        
        # Write data rows
        for row in metrics_data:
            writer.writerow([
                video_id,
                row.get('date', ''),
                row.get('views', 0),
                row.get('watch_time', 0),
                row.get('likes', 0),
                row.get('comments', 0),
                row.get('shares', 0),
                row.get('ctr', 0),
                row.get('engagement_rate', 0)
            ])
        
        # Write summary row
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Total Views', sum(row.get('views', 0) for row in metrics_data)])
        writer.writerow(['Total Watch Time', sum(row.get('watch_time', 0) for row in metrics_data)])
        writer.writerow(['Total Likes', sum(row.get('likes', 0) for row in metrics_data)])
        writer.writerow(['Total Comments', sum(row.get('comments', 0) for row in metrics_data)])
        writer.writerow(['Total Shares', sum(row.get('shares', 0) for row in metrics_data)])
        
        return response
    
    @staticmethod
    def export_channel_metrics(channel_id: str, metrics_data: List[Dict[str, Any]], 
                               start_date: datetime, end_date: datetime) -> HttpResponse:
        """
        Export channel metrics to CSV format.
        
        Args:
            channel_id: YouTube channel ID
            metrics_data: List of metric dictionaries with date and values
            start_date: Start date for the data range
            end_date: End date for the data range
            
        Returns:
            HttpResponse with CSV file attachment
            
        Requirements: 13.2, 13.4
        """
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f'channel_metrics_{channel_id}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Channel ID',
            'Date',
            'Subscribers',
            'Subscribers Gained',
            'Subscribers Lost',
            'Net Subscribers',
            'Total Views',
            'Watch Time (minutes)',
            'Average View Duration (seconds)'
        ])
        
        # Write data rows
        for row in metrics_data:
            gained = row.get('subscribers_gained', 0)
            lost = row.get('subscribers_lost', 0)
            writer.writerow([
                channel_id,
                row.get('date', ''),
                row.get('subscribers', 0),
                gained,
                lost,
                gained - lost,
                row.get('views', 0),
                row.get('watch_time', 0),
                row.get('avg_view_duration', 0)
            ])
        
        # Write summary row
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Total Subscribers Gained', sum(row.get('subscribers_gained', 0) for row in metrics_data)])
        writer.writerow(['Total Subscribers Lost', sum(row.get('subscribers_lost', 0) for row in metrics_data)])
        writer.writerow(['Net Subscriber Change', 
                        sum(row.get('subscribers_gained', 0) for row in metrics_data) - 
                        sum(row.get('subscribers_lost', 0) for row in metrics_data)])
        writer.writerow(['Total Views', sum(row.get('views', 0) for row in metrics_data)])
        writer.writerow(['Total Watch Time', sum(row.get('watch_time', 0) for row in metrics_data)])
        
        return response
    
    @staticmethod
    def export_test_results(test_id: int, test_data: Dict[str, Any]) -> HttpResponse:
        """
        Export A/B test results to CSV format.
        
        Args:
            test_id: A/B test ID
            test_data: Dictionary containing test configuration and results
            
        Returns:
            HttpResponse with CSV file attachment
            
        Requirements: 13.2, 13.4
        """
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        filename = f'abtest_results_{test_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write test information
        writer.writerow(['A/B Test Results'])
        writer.writerow(['Test ID', test_id])
        writer.writerow(['Video ID', test_data.get('video_id', '')])
        writer.writerow(['Video Title', test_data.get('video_title', '')])
        writer.writerow(['Test Type', test_data.get('test_type', '')])
        writer.writerow(['Status', test_data.get('status', '')])
        writer.writerow(['Start Date', test_data.get('start_date', '')])
        writer.writerow(['End Date', test_data.get('end_date', '')])
        writer.writerow(['Duration (hours)', test_data.get('duration_hours', '')])
        writer.writerow([])
        
        # Write variant results header
        writer.writerow(['Variant Results'])
        writer.writerow([
            'Variant',
            'Impressions',
            'Clicks',
            'Views',
            'CTR (%)',
            'Is Winner'
        ])
        
        # Write variant data
        variants = test_data.get('variants', [])
        for variant in variants:
            writer.writerow([
                variant.get('variant_name', ''),
                variant.get('impressions', 0),
                variant.get('clicks', 0),
                variant.get('views', 0),
                variant.get('ctr', 0),
                'Yes' if variant.get('is_winner', False) else 'No'
            ])
        
        # Write variant content details
        writer.writerow([])
        writer.writerow(['Variant Content Details'])
        
        for variant in variants:
            writer.writerow([])
            writer.writerow(['Variant', variant.get('variant_name', '')])
            
            if test_data.get('test_type') in ['thumbnail', 'combined']:
                writer.writerow(['Thumbnail URL', variant.get('thumbnail_url', '')])
            
            if test_data.get('test_type') in ['title', 'combined']:
                writer.writerow(['Title', variant.get('title', '')])
            
            if test_data.get('test_type') == 'description':
                writer.writerow(['Description', variant.get('description', '')])
        
        # Write winner information
        writer.writerow([])
        writer.writerow(['Winner Information'])
        winner_variant = next((v for v in variants if v.get('is_winner')), None)
        if winner_variant:
            writer.writerow(['Winning Variant', winner_variant.get('variant_name', '')])
            writer.writerow(['Winning CTR', winner_variant.get('ctr', 0)])
        else:
            writer.writerow(['No winner selected yet'])
        
        return response



class PDFExporter:
    """
    Service for exporting analytics and A/B testing data to PDF format with charts.
    Requirements: 13.3, 13.4
    """
    
    @staticmethod
    def generate_analytics_report(report_data: Dict[str, Any], charts: Optional[List[BytesIO]] = None) -> HttpResponse:
        """
        Generate a comprehensive analytics report in PDF format.
        
        Args:
            report_data: Dictionary containing analytics data and metadata
            charts: Optional list of chart images as BytesIO objects
            
        Returns:
            HttpResponse with PDF file attachment
            
        Requirements: 13.3, 13.4
        """
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        filename = f'analytics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Create PDF document
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#000000'),
            spaceAfter=30,
            alignment=1  # Center
        )
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Title
        title = Paragraph(f"Analytics Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Report metadata
        metadata = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Report Type:', report_data.get('report_type', 'Analytics')],
            ['Date Range:', f"{report_data.get('start_date', '')} to {report_data.get('end_date', '')}"],
        ]
        
        if report_data.get('channel_id'):
            metadata.append(['Channel ID:', report_data.get('channel_id')])
        if report_data.get('video_id'):
            metadata.append(['Video ID:', report_data.get('video_id')])
        
        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Key Metrics Section
        elements.append(Paragraph("Key Metrics", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        metrics = report_data.get('metrics', {})
        metrics_data = [
            ['Metric', 'Value'],
            ['Total Views', f"{metrics.get('total_views', 0):,}"],
            ['Total Watch Time', f"{metrics.get('total_watch_time', 0):,} minutes"],
            ['Engagement Rate', f"{metrics.get('engagement_rate', 0):.2f}%"],
        ]
        
        if 'subscribers' in metrics:
            metrics_data.append(['Subscribers', f"{metrics.get('subscribers', 0):,}"])
        if 'ctr' in metrics:
            metrics_data.append(['CTR', f"{metrics.get('ctr', 0):.2f}%"])
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Add charts if provided
        if charts:
            elements.append(Paragraph("Performance Trends", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            
            for chart_buffer in charts:
                chart_buffer.seek(0)
                img = Image(chart_buffer, width=6*inch, height=3*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
        
        # Detailed Data Section
        if report_data.get('detailed_data'):
            elements.append(PageBreak())
            elements.append(Paragraph("Detailed Data", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            
            detailed_data = report_data.get('detailed_data', [])
            if detailed_data:
                # Get headers from first row
                headers = list(detailed_data[0].keys())
                table_data = [headers]
                
                # Add data rows (limit to 50 rows for PDF)
                for row in detailed_data[:50]:
                    table_data.append([str(row.get(h, '')) for h in headers])
                
                # Calculate column widths dynamically
                num_cols = len(headers)
                col_width = 6.5 * inch / num_cols
                
                detailed_table = Table(table_data, colWidths=[col_width] * num_cols)
                detailed_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
                ]))
                elements.append(detailed_table)
                
                if len(detailed_data) > 50:
                    elements.append(Spacer(1, 0.1*inch))
                    elements.append(Paragraph(
                        f"Note: Showing first 50 of {len(detailed_data)} rows. Download CSV for complete data.",
                        normal_style
                    ))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF from buffer
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response
    
    @staticmethod
    def generate_test_report(test_data: Dict[str, Any]) -> HttpResponse:
        """
        Generate an A/B test results report in PDF format.
        
        Args:
            test_data: Dictionary containing test configuration and results
            
        Returns:
            HttpResponse with PDF file attachment
            
        Requirements: 13.3, 13.4
        """
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        test_id = test_data.get('test_id', 'unknown')
        filename = f'abtest_report_{test_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Create PDF document
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#000000'),
            spaceAfter=30,
            alignment=1  # Center
        )
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Title
        title = Paragraph(f"A/B Test Results Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Test Information
        test_info = [
            ['Test ID:', str(test_data.get('test_id', ''))],
            ['Video ID:', test_data.get('video_id', '')],
            ['Video Title:', test_data.get('video_title', '')],
            ['Test Type:', test_data.get('test_type', '').title()],
            ['Status:', test_data.get('status', '').title()],
            ['Start Date:', str(test_data.get('start_date', ''))],
            ['End Date:', str(test_data.get('end_date', ''))],
            ['Duration:', f"{test_data.get('duration_hours', 0)} hours"],
        ]
        
        info_table = Table(test_info, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Variant Results
        elements.append(Paragraph("Variant Performance", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        variants = test_data.get('variants', [])
        variant_data = [['Variant', 'Impressions', 'Clicks', 'Views', 'CTR (%)', 'Winner']]
        
        for variant in variants:
            variant_data.append([
                variant.get('variant_name', ''),
                f"{variant.get('impressions', 0):,}",
                f"{variant.get('clicks', 0):,}",
                f"{variant.get('views', 0):,}",
                f"{variant.get('ctr', 0):.2f}",
                '✓' if variant.get('is_winner', False) else ''
            ])
        
        variant_table = Table(variant_data, colWidths=[1*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch, 0.8*inch])
        variant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        elements.append(variant_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Generate comparison chart
        chart_buffer = PDFExporter._create_variant_comparison_chart(variants)
        if chart_buffer:
            elements.append(Paragraph("Performance Comparison", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            chart_buffer.seek(0)
            img = Image(chart_buffer, width=6*inch, height=3*inch)
            elements.append(img)
            elements.append(Spacer(1, 0.3*inch))
        
        # Winner Summary
        winner_variant = next((v for v in variants if v.get('is_winner')), None)
        if winner_variant:
            elements.append(Paragraph("Winner Summary", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            
            winner_text = f"""
            <b>Winning Variant:</b> {winner_variant.get('variant_name', '')}<br/>
            <b>CTR:</b> {winner_variant.get('ctr', 0):.2f}%<br/>
            <b>Total Impressions:</b> {winner_variant.get('impressions', 0):,}<br/>
            <b>Total Clicks:</b> {winner_variant.get('clicks', 0):,}<br/>
            <b>Total Views:</b> {winner_variant.get('views', 0):,}
            """
            elements.append(Paragraph(winner_text, normal_style))
        else:
            elements.append(Paragraph("Winner Summary", heading_style))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("No winner has been selected yet.", normal_style))
        
        # Variant Content Details
        elements.append(PageBreak())
        elements.append(Paragraph("Variant Content Details", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        for variant in variants:
            variant_heading = Paragraph(f"<b>Variant {variant.get('variant_name', '')}</b>", normal_style)
            elements.append(variant_heading)
            elements.append(Spacer(1, 0.1*inch))
            
            content_data = []
            
            if test_data.get('test_type') in ['thumbnail', 'combined']:
                content_data.append(['Thumbnail URL:', variant.get('thumbnail_url', 'N/A')])
            
            if test_data.get('test_type') in ['title', 'combined']:
                content_data.append(['Title:', variant.get('title', 'N/A')])
            
            if test_data.get('test_type') == 'description':
                desc = variant.get('description', 'N/A')
                # Truncate long descriptions
                if len(desc) > 200:
                    desc = desc[:200] + '...'
                content_data.append(['Description:', desc])
            
            if content_data:
                content_table = Table(content_data, colWidths=[1.5*inch, 5*inch])
                content_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(content_table)
            
            elements.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF from buffer
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response
    
    @staticmethod
    def _create_variant_comparison_chart(variants: List[Dict[str, Any]]) -> Optional[BytesIO]:
        """
        Create a bar chart comparing variant CTRs.
        
        Args:
            variants: List of variant dictionaries
            
        Returns:
            BytesIO buffer containing the chart image, or None if no data
        """
        if not variants:
            return None
        
        try:
            # Extract data
            variant_names = [v.get('variant_name', '') for v in variants]
            ctrs = [v.get('ctr', 0) for v in variants]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(8, 4))
            
            # Create bar chart
            bars = ax.bar(variant_names, ctrs, color=['#4CAF50' if v.get('is_winner') else '#2196F3' for v in variants])
            
            # Customize chart
            ax.set_xlabel('Variant', fontsize=12, fontweight='bold')
            ax.set_ylabel('CTR (%)', fontsize=12, fontweight='bold')
            ax.set_title('Variant CTR Comparison', fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}%',
                       ha='center', va='bottom', fontsize=10)
            
            # Save to buffer
            buffer = BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            
            return buffer
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None
    
    @staticmethod
    def add_charts_to_pdf(report_data: Dict[str, Any]) -> List[BytesIO]:
        """
        Generate charts for analytics data to be included in PDF reports.
        
        Args:
            report_data: Dictionary containing analytics data
            
        Returns:
            List of BytesIO buffers containing chart images
            
        Requirements: 13.3, 13.4
        """
        charts = []
        
        try:
            # Views trend chart
            if report_data.get('trend_data') and report_data['trend_data'].get('dates'):
                trend_data = report_data['trend_data']
                dates = trend_data.get('dates', [])
                views = trend_data.get('views', [])
                
                if dates and views:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.plot(dates, views, marker='o', linewidth=2, color='#2196F3')
                    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
                    ax.set_ylabel('Views', fontsize=12, fontweight='bold')
                    ax.set_title('Views Trend', fontsize=14, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    
                    # Rotate x-axis labels for better readability
                    plt.xticks(rotation=45, ha='right')
                    
                    buffer = BytesIO()
                    plt.tight_layout()
                    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                    plt.close()
                    charts.append(buffer)
            
            # Engagement trend chart
            if report_data.get('trend_data') and report_data['trend_data'].get('engagement'):
                trend_data = report_data['trend_data']
                dates = trend_data.get('dates', [])
                engagement = trend_data.get('engagement', [])
                
                if dates and engagement:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.plot(dates, engagement, marker='s', linewidth=2, color='#4CAF50')
                    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
                    ax.set_ylabel('Engagement Rate (%)', fontsize=12, fontweight='bold')
                    ax.set_title('Engagement Rate Trend', fontsize=14, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    
                    plt.xticks(rotation=45, ha='right')
                    
                    buffer = BytesIO()
                    plt.tight_layout()
                    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                    plt.close()
                    charts.append(buffer)
        
        except Exception as e:
            print(f"Error generating charts: {e}")
        
        return charts
