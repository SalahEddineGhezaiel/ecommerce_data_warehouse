"""
============================================================================
E-COMMERCE DATA WAREHOUSE - DATA CLEANING SCRIPT
============================================================================

Description:
    This script performs comprehensive data cleaning and preparation:
    1. Loads all 7 CSV files from the data/ directory
    2. Handles missing values appropriately
    3. Converts date columns to proper datetime format
    4. Merges products with English category translations
    5. Creates comprehensive date dimension
    6. Derives calculated fields (regions, volume, etc.)
    7. Validates data quality and prints statistics
    8. Saves cleaned dataframes as pickle files for ETL


============================================================================
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = 'data'
CLEANED_DATA_DIR = 'data'


INPUT_FILES = {
    'orders': os.path.join(DATA_DIR, 'olist_orders_dataset.csv'),
    'order_items': os.path.join(DATA_DIR, 'olist_order_items_dataset.csv'),
    'customers': os.path.join(DATA_DIR, 'olist_customers_dataset.csv'),
    'products': os.path.join(DATA_DIR, 'olist_products_dataset.csv'),
    'categories': os.path.join(DATA_DIR, 'product_category_name_translation.csv'),
    'payments': os.path.join(DATA_DIR, 'olist_order_payments_dataset.csv'),
    'sellers': os.path.join(DATA_DIR, 'olist_sellers_dataset.csv')
}

OUTPUT_FILES = {
    'customers': os.path.join(CLEANED_DATA_DIR, 'cleaned_customers.pkl'),
    'products': os.path.join(CLEANED_DATA_DIR, 'cleaned_products.pkl'),
    'sellers': os.path.join(CLEANED_DATA_DIR, 'cleaned_sellers.pkl'),
    'payments': os.path.join(CLEANED_DATA_DIR, 'cleaned_payments.pkl'),
    'orders': os.path.join(CLEANED_DATA_DIR, 'cleaned_orders.pkl'),
    'order_items': os.path.join(CLEANED_DATA_DIR, 'cleaned_order_items.pkl'),
    'date_dim': os.path.join(CLEANED_DATA_DIR, 'cleaned_date_dimension.pkl')
}


STATE_TO_REGION = {
    'AC': 'North', 'AP': 'North', 'AM': 'North', 'PA': 'North', 'RO': 'North', 
    'RR': 'North', 'TO': 'North',
    'AL': 'Northeast', 'BA': 'Northeast', 'CE': 'Northeast', 'MA': 'Northeast', 
    'PB': 'Northeast', 'PE': 'Northeast', 'PI': 'Northeast', 'RN': 'Northeast', 
    'SE': 'Northeast',
    'DF': 'Central-West', 'GO': 'Central-West', 'MT': 'Central-West', 'MS': 'Central-West',
    'ES': 'Southeast', 'MG': 'Southeast', 'RJ': 'Southeast', 'SP': 'Southeast',
    'PR': 'South', 'RS': 'South', 'SC': 'South'
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_subsection(title):
    """Print a formatted subsection header"""
    print(f"\n{title}")
    print("-" * 80)

def print_dataframe_info(df, name):
    """Print comprehensive information about a dataframe"""
    print(f"\n{name} Information:")
    print(f"  Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Memory Usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print(f"\n  Missing Values:")
        for col in missing[missing > 0].index:
            pct = (missing[col] / len(df)) * 100
            print(f"    - {col}: {missing[col]:,} ({pct:.2f}%)")
    else:
        print(f"  Missing Values: None")
    
    
    print(f"\n  Data Types:")
    for dtype in df.dtypes.value_counts().items():
        print(f"    - {dtype[0]}: {dtype[1]} columns")

def map_state_to_region(state):
    """Map Brazilian state code to geographic region"""
    return STATE_TO_REGION.get(state, 'Unknown')

# ============================================================================
# LOADING FUNCTIONS
# ============================================================================

def load_csv_files():
    """Load all CSV files into pandas DataFrames"""
    print_section("STEP 1: LOADING CSV FILES")
    
    dataframes = {}
    
    for name, filepath in INPUT_FILES.items():
        try:
            print(f"\nLoading {name}...", end=" ")
            df = pd.read_csv(filepath, low_memory=False)
            dataframes[name] = df
            print(f"✓ Loaded {len(df):,} rows")
        except FileNotFoundError:
            print(f"✗ ERROR: File not found - {filepath}")
            raise
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            raise
    
    print("\n" + "-" * 80)
    print("All CSV files loaded successfully!")
    
    return dataframes

# ============================================================================
# CLEANING FUNCTIONS
# ============================================================================

def clean_customers(df):
    """Clean and prepare customer data"""
    print_section("STEP 2: CLEANING CUSTOMER DATA")
    
    df_clean = df.copy()
    
    
    initial_rows = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['customer_id'], keep='first')
    duplicates_removed = initial_rows - len(df_clean)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed:,} duplicate customer records")
    
    
    text_columns = ['customer_id', 'customer_unique_id', 'customer_city', 'customer_state']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
    
    
    df_clean['customer_state'] = df_clean['customer_state'].str.upper()
    
    
    df_clean['customer_region'] = df_clean['customer_state'].apply(map_state_to_region)
    
    
    df_clean['customer_zip_code_prefix'] = df_clean['customer_zip_code_prefix'].astype(str).str.strip()
    
    
    df_clean['customer_city'] = df_clean['customer_city'].fillna('Unknown')
    df_clean['customer_state'] = df_clean['customer_state'].fillna('UNK')
    df_clean['customer_region'] = df_clean['customer_region'].fillna('Unknown')
    
    print_dataframe_info(df_clean, "Cleaned Customers")
    
    return df_clean

def clean_products(df_products, df_categories):
    """Clean and prepare product data with category translations"""
    print_section("STEP 3: CLEANING PRODUCT DATA")
    
    df_clean = df_products.copy()
    
    
    initial_rows = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['product_id'], keep='first')
    duplicates_removed = initial_rows - len(df_clean)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed:,} duplicate product records")
    
    
    df_clean['product_id'] = df_clean['product_id'].astype(str).str.strip()
    
    
    df_clean['product_category_name'] = df_clean['product_category_name'].astype(str).str.strip().str.lower()
    
    
    df_clean['product_category_name'] = df_clean['product_category_name'].replace('nan', pd.NA)
    
    
    df_categories_clean = df_categories.copy()
    df_categories_clean['product_category_name'] = df_categories_clean['product_category_name'].astype(str).str.strip().str.lower()
    df_categories_clean['product_category_name_english'] = df_categories_clean['product_category_name_english'].astype(str).str.strip().str.lower()
    
    print(f"\nMerging products with category translations...")
    print(f"  Products before merge: {len(df_clean)}")
    print(f"  Available translations: {len(df_categories_clean)}")
    print(f"  Products with NULL category: {df_clean['product_category_name'].isna().sum()}")
    
    df_clean = df_clean.merge(
        df_categories_clean,
        on='product_category_name',
        how='left'
    )
    
    
    df_clean['product_category_name_english'] = df_clean['product_category_name_english'].fillna('uncategorized')
    
    
    categorized = (df_clean['product_category_name_english'] != 'uncategorized').sum()
    uncategorized = (df_clean['product_category_name_english'] == 'uncategorized').sum()
    print(f"  Products with valid category: {categorized} ({categorized/len(df_clean)*100:.1f}%)")
    print(f"  Products uncategorized: {uncategorized} ({uncategorized/len(df_clean)*100:.1f}%)")
    
    print(f"Merged {len(df_categories_clean):,} category translations")
    
    
    numeric_columns = [
        'product_name_lenght', 'product_description_lenght', 
        'product_photos_qty', 'product_weight_g', 
        'product_length_cm', 'product_height_cm', 'product_width_cm'
    ]
    
    for col in numeric_columns:
        if col in df_clean.columns:
            
            median_value = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_value)
            
            df_clean[col] = df_clean[col].clip(lower=0)
    
    
    df_clean['product_volume_cm3'] = (
        df_clean['product_length_cm'] * 
        df_clean['product_height_cm'] * 
        df_clean['product_width_cm']
    )
    df_clean['product_volume_cm3'] = df_clean['product_volume_cm3'].fillna(0)
    
    print(f"Calculated product_volume_cm3 for all products")
    
    
    if 'product_name_lenght' in df_clean.columns:
        df_clean = df_clean.rename(columns={'product_name_lenght': 'product_name_length'})
    if 'product_description_lenght' in df_clean.columns:
        df_clean = df_clean.rename(columns={'product_description_lenght': 'product_description_length'})
    
    print_dataframe_info(df_clean, "Cleaned Products")
    
    return df_clean

def clean_sellers(df):
    """Clean and prepare seller data"""
    print_section("STEP 4: CLEANING SELLER DATA")
    
    df_clean = df.copy()
    
    
    initial_rows = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['seller_id'], keep='first')
    duplicates_removed = initial_rows - len(df_clean)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed:,} duplicate seller records")
    
    
    text_columns = ['seller_id', 'seller_city', 'seller_state']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
    
    
    df_clean['seller_state'] = df_clean['seller_state'].str.upper()
    
    
    df_clean['seller_region'] = df_clean['seller_state'].apply(map_state_to_region)
    
    
    df_clean['seller_zip_code_prefix'] = df_clean['seller_zip_code_prefix'].astype(str).str.strip()
    
    
    df_clean['seller_city'] = df_clean['seller_city'].fillna('Unknown')
    df_clean['seller_state'] = df_clean['seller_state'].fillna('UNK')
    df_clean['seller_region'] = df_clean['seller_region'].fillna('Unknown')
    
    print_dataframe_info(df_clean, "Cleaned Sellers")
    
    return df_clean

def clean_payments(df):
    """Clean and prepare payment data"""
    print_section("STEP 5: CLEANING PAYMENT DATA")
    
    df_clean = df.copy()
    
    
    df_clean['order_id'] = df_clean['order_id'].astype(str).str.strip()
    df_clean['payment_type'] = df_clean['payment_type'].astype(str).str.strip()
    
    
    df_clean['payment_type'] = df_clean['payment_type'].str.lower()
    
    
    df_clean['payment_sequential'] = df_clean['payment_sequential'].fillna(1).astype(int)
    
    
    df_clean['payment_installments'] = df_clean['payment_installments'].fillna(1).astype(int)
    
    
    df_clean['payment_value'] = df_clean['payment_value'].fillna(0)
    df_clean['payment_value'] = df_clean['payment_value'].clip(lower=0)
    
    print_dataframe_info(df_clean, "Cleaned Payments")
    
    return df_clean

def clean_orders(df):
    """Clean and prepare orders data"""
    print_section("STEP 6: CLEANING ORDERS DATA")
    
    df_clean = df.copy()
    
    
    initial_rows = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['order_id'], keep='first')
    duplicates_removed = initial_rows - len(df_clean)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed:,} duplicate order records")
    
    
    df_clean['order_id'] = df_clean['order_id'].astype(str).str.strip()
    df_clean['customer_id'] = df_clean['customer_id'].astype(str).str.strip()
    df_clean['order_status'] = df_clean['order_status'].astype(str).str.strip()
    
    
    date_columns = [
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
            missing_dates = df_clean[col].isnull().sum()
            if missing_dates > 0:
                print(f"  {col}: {missing_dates:,} missing dates converted to NaT")
    
    
    df_clean['delivery_days'] = (
        df_clean['order_delivered_customer_date'] - df_clean['order_purchase_timestamp']
    ).dt.days
    
    
    df_clean.loc[df_clean['order_status'] != 'delivered', 'delivery_days'] = np.nan
    df_clean.loc[df_clean['delivery_days'] < 0, 'delivery_days'] = np.nan
    
    print(f"\nCalculated delivery_days for {df_clean['delivery_days'].notna().sum():,} delivered orders")
    
    print_dataframe_info(df_clean, "Cleaned Orders")
    
    return df_clean

def clean_order_items(df):
    """Clean and prepare order items data"""
    print_section("STEP 7: CLEANING ORDER ITEMS DATA")
    
    df_clean = df.copy()
    
    
    initial_rows = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['order_id', 'order_item_id'], keep='first')
    duplicates_removed = initial_rows - len(df_clean)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed:,} duplicate order item records")
    
    
    text_columns = ['order_id', 'product_id', 'seller_id']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
    
    
    if 'shipping_limit_date' in df_clean.columns:
        df_clean['shipping_limit_date'] = pd.to_datetime(df_clean['shipping_limit_date'], errors='coerce')
    
    
    df_clean['price'] = df_clean['price'].fillna(0).clip(lower=0)
    df_clean['freight_value'] = df_clean['freight_value'].fillna(0).clip(lower=0)
    
    
    df_clean['total_value'] = df_clean['price'] + df_clean['freight_value']
    
    
    df_clean['quantity'] = 1
    
    print(f"Calculated total_value for all {len(df_clean):,} order items")
    
    print_dataframe_info(df_clean, "Cleaned Order Items")
    
    return df_clean

# ============================================================================
# DATE DIMENSION CREATION
# ============================================================================

def create_date_dimension(df_orders):
    """Create comprehensive date dimension from order dates"""
    print_section("STEP 8: CREATING DATE DIMENSION")
    
    
    order_dates = df_orders['order_purchase_timestamp'].dropna()
    delivery_dates = df_orders['order_delivered_customer_date'].dropna()
    
    
    all_dates = pd.concat([order_dates, delivery_dates]).unique()
    all_dates = pd.to_datetime(all_dates)
    
    
    min_date = all_dates.min().date()
    max_date = all_dates.max().date()
    
    print(f"\nDate Range: {min_date} to {max_date}")
    print(f"Total Days: {(max_date - min_date).days + 1}")
    
    
    start_date = min_date - timedelta(days=365)  
    end_date = max_date + timedelta(days=365)    
    
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    print(f"Date Dimension Range: {start_date} to {end_date}")
    print(f"Total Rows: {len(date_range):,}")
    
    
    date_dim = pd.DataFrame({
        'full_date': date_range
    })
    
    
    date_dim['date_key'] = date_dim['full_date'].dt.strftime('%Y%m%d').astype(int)
    date_dim['day'] = date_dim['full_date'].dt.day
    date_dim['month'] = date_dim['full_date'].dt.month
    date_dim['month_name'] = date_dim['full_date'].dt.strftime('%B')
    date_dim['quarter'] = date_dim['full_date'].dt.quarter
    date_dim['year'] = date_dim['full_date'].dt.year
    date_dim['day_of_week'] = date_dim['full_date'].dt.dayofweek + 1  
    date_dim['day_name'] = date_dim['full_date'].dt.strftime('%A')
    date_dim['is_weekend'] = date_dim['day_of_week'].isin([6, 7])  
    date_dim['week_of_year'] = date_dim['full_date'].dt.isocalendar().week
    
    print("\nDate Dimension Attributes:")
    print(f"  - Unique Years: {date_dim['year'].nunique()}")
    print(f"  - Unique Months: {date_dim['month'].nunique()}")
    print(f"  - Unique Quarters: {date_dim['quarter'].nunique()}")
    print(f"  - Weekend Days: {date_dim['is_weekend'].sum():,}")
    print(f"  - Weekdays: {(~date_dim['is_weekend']).sum():,}")
    
    print_dataframe_info(date_dim, "Date Dimension")
    
    return date_dim

# ============================================================================
# DATA QUALITY VALIDATION
# ============================================================================

def validate_data_quality(dataframes):
    """Perform data quality checks on all cleaned dataframes"""
    print_section("STEP 9: DATA QUALITY VALIDATION")
    
    print("\n" + "=" * 80)
    print("DATA QUALITY SUMMARY")
    print("=" * 80)
    
    for name, df in dataframes.items():
        print(f"\n{name.upper()}")
        print("-" * 80)
        print(f"  Total Rows: {len(df):,}")
        print(f"  Total Columns: {len(df.columns)}")
        
        
        key_columns = {
            'customers': ['customer_id'],
            'products': ['product_id'],
            'sellers': ['seller_id'],
            'payments': ['order_id', 'payment_sequential'],
            'orders': ['order_id'],
            'order_items': ['order_id', 'order_item_id'],
            'date_dim': ['date_key']
        }
        
        if name in key_columns:
            dup_count = df.duplicated(subset=key_columns[name]).sum()
            print(f"  Duplicate Keys: {dup_count}")
        
        
        missing_total = df.isnull().sum().sum()
        print(f"  Total Missing Values: {missing_total:,}")
        
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        text_cols = df.select_dtypes(include=['object']).columns
        date_cols = df.select_dtypes(include=['datetime64']).columns
        
        print(f"  Numeric Columns: {len(numeric_cols)}")
        print(f"  Text Columns: {len(text_cols)}")
        print(f"  Date Columns: {len(date_cols)}")
    
    print("\n" + "=" * 80)
    print("✓ Data Quality Validation Complete")
    print("=" * 80)

# ============================================================================
# SAVE CLEANED DATA
# ============================================================================

def save_cleaned_data(dataframes):
    """Save all cleaned dataframes as pickle files"""
    print_section("STEP 10: SAVING CLEANED DATA")
    
    
    os.makedirs(CLEANED_DATA_DIR, exist_ok=True)
    
    saved_files = []
    
    for name, filepath in OUTPUT_FILES.items():
        if name in dataframes:
            try:
                print(f"\nSaving {name}...", end=" ")
                dataframes[name].to_pickle(filepath)
                file_size = os.path.getsize(filepath) / 1024 / 1024  
                print(f"✓ Saved to {filepath} ({file_size:.2f} MB)")
                saved_files.append(filepath)
            except Exception as e:
                print(f"✗ ERROR: {str(e)}")
                raise
    
    print("\n" + "-" * 80)
    print(f"All {len(saved_files)} cleaned datasets saved successfully!")
    
    return saved_files

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("\n")
    print("=" * 80)
    print(" E-COMMERCE DATA WAREHOUSE - DATA CLEANING PIPELINE")
    print("=" * 80)
    print(f" Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    start_time = datetime.now()
    
    try:
       
        raw_data = load_csv_files()
        
        
        cleaned_data = {}
        cleaned_data['customers'] = clean_customers(raw_data['customers'])
        cleaned_data['products'] = clean_products(raw_data['products'], raw_data['categories'])
        cleaned_data['sellers'] = clean_sellers(raw_data['sellers'])
        cleaned_data['payments'] = clean_payments(raw_data['payments'])
        cleaned_data['orders'] = clean_orders(raw_data['orders'])
        cleaned_data['order_items'] = clean_order_items(raw_data['order_items'])
        
        
        cleaned_data['date_dim'] = create_date_dimension(cleaned_data['orders'])
        
        
        validate_data_quality(cleaned_data)
        
        
        saved_files = save_cleaned_data(cleaned_data)
        
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print_section("CLEANING PIPELINE COMPLETED SUCCESSFULLY")
        print(f"\n  Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"\n  Files Processed: {len(INPUT_FILES)}")
        print(f"  Files Generated: {len(saved_files)}")
        print(f"\n  Output Directory: {CLEANED_DATA_DIR}/")
        
        print("\n" + "=" * 80)
        print(" ✓ DATA IS READY FOR ETL PROCESS")
        print("=" * 80)
        print("\n  Next Step: Run scripts/etl_pipeline.py to load data into warehouse")
        print("\n")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(" ✗ ERROR: DATA CLEANING FAILED")
        print("=" * 80)
        print(f"\n  Error Message: {str(e)}")
        print("\n  Please check the error message above and fix the issue.")
        print("\n")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
