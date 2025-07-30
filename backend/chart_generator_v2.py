import matplotlib.pyplot as plt
from io import BytesIO
import base64
import numpy as np

def generate_pie_chart(data, label_col=0, value_col=1):
    labels = [row[label_col] for row in data]
    sizes = [row[value_col] for row in data]

    plt.figure(figsize=(4, 4))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures pie is drawn as a circle

    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)

    chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close()

    return chart_base64


def generate_bar_chart(data, label_col=0, value_col=1):
    labels = [row[label_col] for row in data]
    values = [row[value_col] for row in data]

    plt.figure(figsize=(6, 4))
    bars = plt.bar(labels, values, color='skyblue')
    plt.xlabel("Category")
    plt.ylabel("Quantity")
    plt.title("Bar Chart of Quantity by Category")
    plt.xticks(rotation=45)

    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height, f'{height}', ha='center', va='bottom')

    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)

    chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close()

    return chart_base64


# ==================== NEW CHART TYPES ====================

def generate_donut_chart(data, label_col=0, value_col=1):
    """Generate a donut chart (pie chart with center hole)"""
    labels = [row[label_col] for row in data]
    sizes = [row[value_col] for row in data]

    plt.figure(figsize=(4, 4))
    
    # Create pie chart with a white circle in the center to make it a donut
    wedges, texts, autotexts = plt.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                       startangle=140, pctdistance=0.85)
    
    # Draw a white circle in the center
    centre_circle = plt.Circle((0,0), 0.60, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    
    plt.axis('equal')
    plt.title("Donut Chart")

    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)

    chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close()

    return chart_base64


def generate_column_chart(data, label_col=0, value_col=1):
    """Generate a column chart (vertical bars with enhanced styling)"""
    labels = [row[label_col] for row in data]
    values = [row[value_col] for row in data]

    plt.figure(figsize=(8, 6))
    
    # Create column chart with gradient colors
    colors = plt.cm.viridis(np.linspace(0, 1, len(labels)))
    bars = plt.bar(labels, values, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    plt.xlabel("Category", fontsize=12, fontweight='bold')
    plt.ylabel("Value", fontsize=12, fontweight='bold')
    plt.title("Column Chart", fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on top of bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height + max(values)*0.01, 
                f'{value}', ha='center', va='bottom', fontweight='bold')
    
    # Add grid for better readability
    plt.grid(axis='y', alpha=0.3, linestyle='--')

    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
    buffer.seek(0)

    chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close()

    return chart_base64


def generate_line_chart(data, label_col=0, value_col=1):
    """Generate a line chart with markers and styling"""
    labels = [row[label_col] for row in data]
    values = [row[value_col] for row in data]

    plt.figure(figsize=(8, 6))
    
    # Create line chart with markers and styling
    plt.plot(labels, values, marker='o', markersize=8, linewidth=2.5, 
             color='#2E86C1', markerfacecolor='#E74C3C', markeredgecolor='white', 
             markeredgewidth=2)
    
    plt.xlabel("Category", fontsize=12, fontweight='bold')
    plt.ylabel("Value", fontsize=12, fontweight='bold')
    plt.title("Line Chart", fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on data points
    for i, (label, value) in enumerate(zip(labels, values)):
        plt.annotate(f'{value}', (i, value), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontweight='bold')
    
    # Add grid for better readability
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Fill area under the line with light color
    plt.fill_between(range(len(labels)), values, alpha=0.2, color='#2E86C1')

    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
    buffer.seek(0)

    chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close()

    return chart_base64


def generate_area_chart(data, label_col=0, value_col=1, chart_subtype="normal"):
    """Generate area chart with different subtypes"""
    labels = [row[label_col] for row in data]
    values = [row[value_col] for row in data]

    plt.figure(figsize=(8, 6))
    
    if chart_subtype == "stacked":
        # For stacked area, we'll create multiple series (simulate with random data for demo)
        # In real implementation, you'd pass multiple value columns
        values_series1 = [v * 0.6 for v in values]
        values_series2 = [v * 0.4 for v in values]
        
        plt.stackplot(range(len(labels)), values_series1, values_series2, 
                     labels=['Series 1', 'Series 2'], alpha=0.8,
                     colors=['#3498DB', '#E74C3C'])
        plt.legend(loc='upper right')
        plt.title("Stacked Area Chart", fontsize=14, fontweight='bold')
        
    elif chart_subtype == "percentage":
        # Percentage area chart (normalize to 100%)
        values_series1 = [v * 0.6 for v in values]
        values_series2 = [v * 0.4 for v in values]
        
        # Normalize to percentages
        totals = [s1 + s2 for s1, s2 in zip(values_series1, values_series2)]
        values_pct1 = [s1/total*100 if total > 0 else 0 for s1, total in zip(values_series1, totals)]
        values_pct2 = [s2/total*100 if total > 0 else 0 for s2, total in zip(values_series2, totals)]
        
        plt.stackplot(range(len(labels)), values_pct1, values_pct2, 
                     labels=['Series 1', 'Series 2'], alpha=0.8,
                     colors=['#3498DB', '#E74C3C'])
        plt.ylabel("Percentage (%)", fontsize=12, fontweight='bold')
        plt.ylim(0, 100)
        plt.legend(loc='upper right')
        plt.title("Percentage Area Chart", fontsize=14, fontweight='bold')
        
    else:  # normal area chart
        plt.fill_between(range(len(labels)), values, alpha=0.6, color='#3498DB')
        plt.plot(range(len(labels)), values, color='#2E86C1', linewidth=2, marker='o')
        plt.title("Area Chart", fontsize=14, fontweight='bold')
    
    plt.xlabel("Category", fontsize=12, fontweight='bold')
    if chart_subtype != "percentage":
        plt.ylabel("Value", fontsize=12, fontweight='bold')
    
    plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
    plt.grid(True, alpha=0.3, linestyle='--')

    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
    buffer.seek(0)

    chart_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    plt.close()

    return chart_base64


def generate_stacked_area_chart(data, label_col=0, value_col=1):
    """Wrapper for stacked area chart"""
    return generate_area_chart(data, label_col, value_col, "stacked")


def generate_percentage_area_chart(data, label_col=0, value_col=1):
    """Wrapper for percentage area chart"""
    return generate_area_chart(data, label_col, value_col, "percentage")