"""
============================================================================
E-COMMERCE DATA WAREHOUSE - DASHBOARD VISUALIZATION SCRIPT
============================================================================

Description:
    This script executes SQL queries from the data warehouse and creates
    professional visualizations for business intelligence analysis.
    
    It generates 10 main dashboard visualizations:
    1. Monthly sales revenue trend (line chart)
    2. Top 10 product categories by revenue (horizontal bar)
    3. Sales by customer state (bar chart)
    4. Payment methods distribution (pie chart)
    5. Top 10 categories by quantity sold (horizontal bar)
    6. Orders by day of week (bar chart)
    7. Top 10 sellers by revenue (horizontal bar)
    8. Quarterly sales comparison (bar chart)
    9. Delivery time analysis (histogram)
    10. Revenue per customer state (bar chart)

============================================================================
"""

import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Set style for all plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============================================================================
# CONFIGURATION
# ============================================================================


DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ecommerce_dw',
    'user': 'postgres',
    'password': os.environ['DB_PASSWORD']
}


OUTPUT_DIR = 'dashboards'


os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def connect_to_database():
    """Create and return database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        print(f"✓ Connected to database '{DB_CONFIG['database']}'")
        return conn
    except Exception as e:
        print(f"✗ ERROR connecting to database: {e}")
        raise

def execute_query(conn, query, description):
    """Execute SQL query and return DataFrame"""
    try:
        print(f"\n  Executing query: {description}...", end=" ")
        df = pd.read_sql_query(query, conn)
        print(f"✓ ({len(df)} rows)")
        return df
    except Exception as e:
        print(f"✗ ERROR")
        print(f"  Error details: {e}")
        return None

def save_plot(filename, dpi=300):
    """Save current plot to file"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=dpi, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {filepath}")

# ============================================================================
# DASHBOARD 1: MONTHLY SALES REVENUE TREND
# ============================================================================

def create_dashboard_1(conn):
    """Monthly sales revenue trend - Line chart"""
    print_section("DASHBOARD 1: Monthly Sales Revenue Trend")
    
    query = """
    SELECT 
        d.year,
        d.month,
        d.month_name,
        TO_CHAR(TO_DATE(d.year || '-' || d.month || '-01', 'YYYY-MM-DD'), 'YYYY-MM') AS year_month,
        ROUND(SUM(f.total_value), 2) AS total_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.order_date_key = d.date_key
    GROUP BY d.year, d.month, d.month_name
    ORDER BY d.year, d.month;
    """
    
    df = execute_query(conn, query, "Monthly revenue trend")
    if df is None or df.empty:
        return
    
    
    plt.figure(figsize=(14, 6))
    plt.plot(df.index, df['total_revenue'], marker='o', linewidth=2, markersize=6, color='#2E86AB')
    
    
    plt.title('Monthly Sales Revenue Trend', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Month', fontsize=12, fontweight='bold')
    plt.ylabel('Revenue ($)', fontsize=12, fontweight='bold')
    plt.xticks(df.index, df['year_month'], rotation=45, ha='right')
    plt.grid(True, alpha=0.3)
    
    
    for i, value in enumerate(df['total_revenue']):
        if i % 2 == 0:  
            plt.text(i, value, f'${value/1000:.0f}K', 
                    ha='center', va='bottom', fontsize=8)
    
    
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    save_plot('01_monthly_revenue_trend.png')

# ============================================================================
# DASHBOARD 2: TOP 10 PRODUCT CATEGORIES BY REVENUE
# ============================================================================

def create_dashboard_2(conn):
    """Top 10 product categories by revenue - Horizontal bar chart"""
    print_section("DASHBOARD 2: Top 10 Product Categories by Revenue")
    
    query = """
    SELECT 
        p.product_category_english AS category,
        ROUND(SUM(f.total_value), 2) AS total_revenue
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    WHERE p.product_category_english != 'uncategorized'
    GROUP BY p.product_category_english
    ORDER BY total_revenue DESC
    LIMIT 10;
    """
    
    df = execute_query(conn, query, "Top 10 categories by revenue")
    if df is None or df.empty:
        return
    
    
    plt.figure(figsize=(12, 8))
    colors = sns.color_palette("RdYlGn_r", len(df))
    bars = plt.barh(df['category'], df['total_revenue'], color=colors)
    
    
    plt.title('Top 10 Product Categories by Revenue', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Revenue ($)', fontsize=12, fontweight='bold')
    plt.ylabel('Category', fontsize=12, fontweight='bold')
    plt.gca().invert_yaxis()  
    
    
    for i, (bar, value) in enumerate(zip(bars, df['total_revenue'])):
        plt.text(value, bar.get_y() + bar.get_height()/2, 
                f'${value/1000:.1f}K', 
                ha='left', va='center', fontsize=10, fontweight='bold')
    
    
    ax = plt.gca()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    save_plot('02_top_categories_revenue.png')

# ============================================================================
# DASHBOARD 3: SALES BY CUSTOMER STATE
# ============================================================================

def create_dashboard_3(conn):
    """Sales by customer state - Bar chart"""
    print_section("DASHBOARD 3: Sales by Customer State")
    
    query = """
    SELECT 
        c.customer_state AS state,
        ROUND(SUM(f.total_value), 2) AS total_revenue,
        COUNT(DISTINCT f.order_id) AS num_orders
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    GROUP BY c.customer_state
    ORDER BY total_revenue DESC
    LIMIT 15;
    """
    
    df = execute_query(conn, query, "Sales by state")
    if df is None or df.empty:
        return
    
    
    plt.figure(figsize=(14, 7))
    colors = sns.color_palette("Blues_r", len(df))
    bars = plt.bar(df['state'], df['total_revenue'], color=colors)
    
    
    plt.title('Sales Revenue by Customer State (Top 15)', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('State', fontsize=12, fontweight='bold')
    plt.ylabel('Revenue ($)', fontsize=12, fontweight='bold')
    plt.xticks(rotation=0)
    
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'${height/1000:.0f}K',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    save_plot('03_sales_by_state.png')

# ============================================================================
# DASHBOARD 4: PAYMENT METHODS DISTRIBUTION
# ============================================================================

def create_dashboard_4(conn):
    """Payment methods distribution - Pie chart"""
    print_section("DASHBOARD 4: Payment Methods Distribution")
    
    query = """
    SELECT 
        pm.payment_type,
        COUNT(DISTINCT f.order_id) AS num_orders,
        ROUND(SUM(f.total_value), 2) AS total_revenue
    FROM fact_sales f
    JOIN dim_payment pm ON f.payment_key = pm.payment_key
    WHERE pm.payment_type != 'not_defined'
    GROUP BY pm.payment_type
    ORDER BY total_revenue DESC;
    """
    
    df = execute_query(conn, query, "Payment methods distribution")
    if df is None or df.empty:
        return
    
    
    plt.figure(figsize=(10, 8))
    colors = sns.color_palette("Set2", len(df))
    
    
    labels = [f"{row['payment_type']}\n${row['total_revenue']/1000:.0f}K\n({row['total_revenue']/df['total_revenue'].sum()*100:.1f}%)" 
              for _, row in df.iterrows()]
    
    wedges, texts, autotexts = plt.pie(df['total_revenue'], 
                                        labels=labels,
                                        colors=colors,
                                        autopct='',
                                        startangle=90,
                                        textprops={'fontsize': 11, 'fontweight': 'bold'})
    
    plt.title('Payment Methods Distribution by Revenue', fontsize=16, fontweight='bold', pad=20)
    
    save_plot('04_payment_methods_distribution.png')

# ============================================================================
# DASHBOARD 5: TOP 10 CATEGORIES BY QUANTITY SOLD
# ============================================================================

def create_dashboard_5(conn):
    """Top 10 categories by quantity sold - Horizontal bar chart"""
    print_section("DASHBOARD 5: Top 10 Categories by Quantity Sold")
    
    query = """
    SELECT 
        p.product_category_english AS category,
        COUNT(f.sales_id) AS total_items_sold,
        ROUND(SUM(f.total_value), 2) AS total_revenue
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    WHERE p.product_category_english != 'uncategorized'
    GROUP BY p.product_category_english
    ORDER BY total_items_sold DESC
    LIMIT 10;
    """
    
    df = execute_query(conn, query, "Top 10 categories by quantity")
    if df is None or df.empty:
        return
    
    
    plt.figure(figsize=(12, 8))
    colors = sns.color_palette("Greens_r", len(df))
    bars = plt.barh(df['category'], df['total_items_sold'], color=colors)
    
    
    plt.title('Top 10 Product Categories by Quantity Sold', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Number of Items Sold', fontsize=12, fontweight='bold')
    plt.ylabel('Category', fontsize=12, fontweight='bold')
    plt.gca().invert_yaxis()
    
    
    for bar, value in zip(bars, df['total_items_sold']):
        plt.text(value, bar.get_y() + bar.get_height()/2, 
                f'{value:,}', 
                ha='left', va='center', fontsize=10, fontweight='bold')
    
    save_plot('05_top_categories_quantity.png')

# ============================================================================
# DASHBOARD 6: ORDERS BY DAY OF WEEK
# ============================================================================

def create_dashboard_6(conn):
    """Orders by day of week - Bar chart"""
    print_section("DASHBOARD 6: Orders by Day of Week")
    
    query = """
    SELECT 
        d.day_name,
        d.day_of_week,
        COUNT(DISTINCT f.order_id) AS num_orders,
        ROUND(SUM(f.total_value), 2) AS total_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.order_date_key = d.date_key
    GROUP BY d.day_name, d.day_of_week
    ORDER BY d.day_of_week;
    """
    
    df = execute_query(conn, query, "Orders by day of week")
    if df is None or df.empty:
        return
    
    
    plt.figure(figsize=(12, 7))
    colors = ['#FF6B6B' if i >= 5 else '#4ECDC4' for i in range(len(df))]  # Weekend vs weekday
    bars = plt.bar(df['day_name'], df['num_orders'], color=colors)
    
    
    plt.title('Orders by Day of Week', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Day of Week', fontsize=12, fontweight='bold')
    plt.ylabel('Number of Orders', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='#4ECDC4', label='Weekday'),
                      Patch(facecolor='#FF6B6B', label='Weekend')]
    plt.legend(handles=legend_elements, loc='upper right')
    
    save_plot('06_orders_by_day.png')

# ============================================================================
# DASHBOARD 7: TOP 10 SELLERS BY REVENUE
# ============================================================================

def create_dashboard_7(conn):
    """Top 10 sellers by revenue - Horizontal bar chart"""
    print_section("DASHBOARD 7: Top 10 Sellers by Revenue")
    
    query = """
    SELECT 
        s.seller_id,
        s.seller_state,
        COUNT(f.sales_id) AS num_items_sold,
        ROUND(SUM(f.total_value), 2) AS total_revenue
    FROM fact_sales f
    JOIN dim_seller s ON f.seller_key = s.seller_key
    GROUP BY s.seller_id, s.seller_state
    ORDER BY total_revenue DESC
    LIMIT 10;
    """
    
    df = execute_query(conn, query, "Top 10 sellers")
    if df is None or df.empty:
        return
    
    
    plt.figure(figsize=(12, 8))
    colors = sns.color_palette("Oranges_r", len(df))
    
    
    labels = [f"{row['seller_id'][:8]}... ({row['seller_state']})" for _, row in df.iterrows()]
    
    bars = plt.barh(labels, df['total_revenue'], color=colors)
    
    
    plt.title('Top 10 Sellers by Revenue', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Revenue ($)', fontsize=12, fontweight='bold')
    plt.ylabel('Seller ID (State)', fontsize=12, fontweight='bold')
    plt.gca().invert_yaxis()
    
    
    for bar, value in zip(bars, df['total_revenue']):
        plt.text(value, bar.get_y() + bar.get_height()/2, 
                f'${value/1000:.1f}K', 
                ha='left', va='center', fontsize=10, fontweight='bold')
    
    
    ax = plt.gca()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    save_plot('07_top_sellers_revenue.png')

# ============================================================================
# DASHBOARD 8: QUARTERLY SALES COMPARISON
# ============================================================================

def create_dashboard_8(conn):
    """Quarterly sales comparison - Grouped bar chart"""
    print_section("DASHBOARD 8: Quarterly Sales Comparison")
    
    query = """
    SELECT 
        d.year,
        d.quarter,
        CONCAT('Q', d.quarter) AS quarter_label,
        ROUND(SUM(f.total_value), 2) AS total_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.order_date_key = d.date_key
    GROUP BY d.year, d.quarter
    ORDER BY d.year, d.quarter;
    """
    
    df = execute_query(conn, query, "Quarterly sales")
    if df is None or df.empty:
        return
    
    
    df_pivot = df.pivot(index='quarter_label', columns='year', values='total_revenue')
    
    
    plt.figure(figsize=(12, 7))
    df_pivot.plot(kind='bar', ax=plt.gca(), width=0.8)
    
    
    plt.title('Quarterly Sales Comparison by Year', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Quarter', fontsize=12, fontweight='bold')
    plt.ylabel('Revenue ($)', fontsize=12, fontweight='bold')
    plt.xticks(rotation=0)
    plt.legend(title='Year', fontsize=10, title_fontsize=11)
    plt.grid(axis='y', alpha=0.3)
    
    
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    save_plot('08_quarterly_sales_comparison.png')

# ============================================================================
# DASHBOARD 9: DELIVERY TIME ANALYSIS
# ============================================================================

def create_dashboard_9(conn):
    """Delivery time analysis - Histogram"""
    print_section("DASHBOARD 9: Delivery Time Analysis")
    
    query = """
    SELECT 
        CASE 
            WHEN f.delivery_days IS NULL THEN 'Not Delivered'
            WHEN f.delivery_days <= 7 THEN '1-7 days'
            WHEN f.delivery_days <= 14 THEN '8-14 days'
            WHEN f.delivery_days <= 21 THEN '15-21 days'
            WHEN f.delivery_days <= 30 THEN '22-30 days'
            WHEN f.delivery_days <= 45 THEN '31-45 days'
            ELSE '45+ days'
        END AS delivery_time_range,
        COUNT(f.sales_id) AS num_orders
    FROM fact_sales f
    GROUP BY 
        CASE 
            WHEN f.delivery_days IS NULL THEN 'Not Delivered'
            WHEN f.delivery_days <= 7 THEN '1-7 days'
            WHEN f.delivery_days <= 14 THEN '8-14 days'
            WHEN f.delivery_days <= 21 THEN '15-21 days'
            WHEN f.delivery_days <= 30 THEN '22-30 days'
            WHEN f.delivery_days <= 45 THEN '31-45 days'
            ELSE '45+ days'
        END
    ORDER BY 
        CASE 
            WHEN CASE 
                WHEN f.delivery_days IS NULL THEN 'Not Delivered'
                WHEN f.delivery_days <= 7 THEN '1-7 days'
                WHEN f.delivery_days <= 14 THEN '8-14 days'
                WHEN f.delivery_days <= 21 THEN '15-21 days'
                WHEN f.delivery_days <= 30 THEN '22-30 days'
                WHEN f.delivery_days <= 45 THEN '31-45 days'
                ELSE '45+ days'
            END = '1-7 days' THEN 1
            WHEN CASE 
                WHEN f.delivery_days IS NULL THEN 'Not Delivered'
                WHEN f.delivery_days <= 7 THEN '1-7 days'
                WHEN f.delivery_days <= 14 THEN '8-14 days'
                WHEN f.delivery_days <= 21 THEN '15-21 days'
                WHEN f.delivery_days <= 30 THEN '22-30 days'
                WHEN f.delivery_days <= 45 THEN '31-45 days'
                ELSE '45+ days'
            END = '8-14 days' THEN 2
            WHEN CASE 
                WHEN f.delivery_days IS NULL THEN 'Not Delivered'
                WHEN f.delivery_days <= 7 THEN '1-7 days'
                WHEN f.delivery_days <= 14 THEN '8-14 days'
                WHEN f.delivery_days <= 21 THEN '15-21 days'
                WHEN f.delivery_days <= 30 THEN '22-30 days'
                WHEN f.delivery_days <= 45 THEN '31-45 days'
                ELSE '45+ days'
            END = '15-21 days' THEN 3
            WHEN CASE 
                WHEN f.delivery_days IS NULL THEN 'Not Delivered'
                WHEN f.delivery_days <= 7 THEN '1-7 days'
                WHEN f.delivery_days <= 14 THEN '8-14 days'
                WHEN f.delivery_days <= 21 THEN '15-21 days'
                WHEN f.delivery_days <= 30 THEN '22-30 days'
                WHEN f.delivery_days <= 45 THEN '31-45 days'
                ELSE '45+ days'
            END = '22-30 days' THEN 4
            WHEN CASE 
                WHEN f.delivery_days IS NULL THEN 'Not Delivered'
                WHEN f.delivery_days <= 7 THEN '1-7 days'
                WHEN f.delivery_days <= 14 THEN '8-14 days'
                WHEN f.delivery_days <= 21 THEN '15-21 days'
                WHEN f.delivery_days <= 30 THEN '22-30 days'
                WHEN f.delivery_days <= 45 THEN '31-45 days'
                ELSE '45+ days'
            END = '31-45 days' THEN 5
            WHEN CASE 
                WHEN f.delivery_days IS NULL THEN 'Not Delivered'
                WHEN f.delivery_days <= 7 THEN '1-7 days'
                WHEN f.delivery_days <= 14 THEN '8-14 days'
                WHEN f.delivery_days <= 21 THEN '15-21 days'
                WHEN f.delivery_days <= 30 THEN '22-30 days'
                WHEN f.delivery_days <= 45 THEN '31-45 days'
                ELSE '45+ days'
            END = '45+ days' THEN 6
            ELSE 7
        END;
    """
    
    df = execute_query(conn, query, "Delivery time distribution")
    if df is None or df.empty:
        return
    
    
    plt.figure(figsize=(12, 7))
    colors = sns.color_palette("YlOrRd", len(df))
    bars = plt.bar(df['delivery_time_range'], df['num_orders'], color=colors)
    
    
    plt.title('Delivery Time Distribution', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Delivery Time Range', fontsize=12, fontweight='bold')
    plt.ylabel('Number of Orders', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    save_plot('09_delivery_time_analysis.png')

# ============================================================================
# DASHBOARD 10: REVENUE PER CUSTOMER STATE
# ============================================================================

def create_dashboard_10(conn):
    """Revenue per customer state - Bar chart"""
    print_section("DASHBOARD 10: Revenue per Customer State (Top 15)")
    
    query = """
    SELECT 
        c.customer_state AS state,
        COUNT(DISTINCT c.customer_key) AS num_customers,
        ROUND(SUM(f.total_value), 2) AS total_revenue,
        ROUND(SUM(f.total_value) / COUNT(DISTINCT c.customer_key), 2) AS revenue_per_customer
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    GROUP BY c.customer_state
    ORDER BY total_revenue DESC
    LIMIT 15;
    """
    
    df = execute_query(conn, query, "Revenue per customer by state")
    if df is None or df.empty:
        return
    
    
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    
    color = '#2E86AB'
    ax1.set_xlabel('State', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Total Revenue ($)', color=color, fontsize=12, fontweight='bold')
    bars1 = ax1.bar(df['state'], df['total_revenue'], color=color, alpha=0.7, label='Total Revenue')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    
    for i, (bar, value) in enumerate(zip(bars1, df['total_revenue'])):
        ax1.text(bar.get_x() + bar.get_width()/2., value,
                f'${value/1000:.0f}K',
                ha='center', va='bottom', fontsize=8, fontweight='bold', color=color)
    
    
    ax2 = ax1.twinx()
    color = '#FF6B6B'
    ax2.set_ylabel('Revenue per Customer ($)', color=color, fontsize=12, fontweight='bold')
    line = ax2.plot(df['state'], df['revenue_per_customer'], color=color, marker='o', 
                    linewidth=2, markersize=8, label='Revenue/Customer')
    ax2.tick_params(axis='y', labelcolor=color)
    
    
    for i, (x, y) in enumerate(zip(df['state'], df['revenue_per_customer'])):
        ax2.text(i, y, f'${y:.0f}', 
                ha='center', va='bottom', fontsize=8, fontweight='bold', color=color)
    
    
    plt.title('Total Revenue and Revenue per Customer by State', fontsize=16, fontweight='bold', pad=20)
    ax1.grid(axis='y', alpha=0.3)
    
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    fig.tight_layout()
    save_plot('10_revenue_per_state.png')

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("\n")
    print("=" * 80)
    print(" E-COMMERCE DATA WAREHOUSE - DASHBOARD GENERATION")
    print("=" * 80)
    print(f" Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Output Directory: {OUTPUT_DIR}/")
    print("=" * 80)
    
    start_time = datetime.now()
    
    try:
        
        print_section("CONNECTING TO DATABASE")
        conn = connect_to_database()
        
        
        create_dashboard_1(conn)
        create_dashboard_2(conn)
        create_dashboard_3(conn)
        create_dashboard_4(conn)
        create_dashboard_5(conn)
        create_dashboard_6(conn)
        create_dashboard_7(conn)
        create_dashboard_8(conn)
        create_dashboard_9(conn)
        create_dashboard_10(conn)
        
        
        conn.close()
        
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print_section("DASHBOARD GENERATION COMPLETED SUCCESSFULLY")
        print(f"\n  Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"\n  Dashboards Created: 10")
        print(f"  Output Directory: {OUTPUT_DIR}/")
        print("\n  Generated Files:")
        for i in range(1, 11):
            filename = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(f'{i:02d}_')]
            if filename:
                print(f"    {i:2d}. {filename[0]}")
        
        print("\n" + "=" * 80)
        print(" ✓ ALL DASHBOARDS READY FOR PRESENTATION")
        print("=" * 80)
        print(f"\n  You can find all dashboard images in the '{OUTPUT_DIR}/' folder")
        print("  Each image is saved as high-resolution PNG (300 DPI)")
        print("\n")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(" ✗ ERROR: DASHBOARD GENERATION FAILED")
        print("=" * 80)
        print(f"\n  Error Message: {str(e)}")
        print("\n")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
