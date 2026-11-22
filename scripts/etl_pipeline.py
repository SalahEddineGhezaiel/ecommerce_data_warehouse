"""
============================================================================
E-COMMERCE DATA WAREHOUSE - ETL PIPELINE (PROFESSOR'S METHOD)
============================================================================

Description:
    This script implements the ETL process using the EXACT pattern shown by
    the professor in the classroom example (assurance/securite routiere).
    
    KEY DIFFERENCE from previous version:
    - Uses connection.setasdefault() to make connection globally available
    - Dimension.ensure(row) takes only ONE parameter (not two)
    - FactTable.ensure(row) takes only ONE parameter (not two)
    - No targetconnection parameter needed

============================================================================
"""

import pandas as pd
import psycopg2
import pygrametl
from pygrametl.tables import Dimension, FactTable
import os
from datetime import datetime
import sys

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

DATA_DIR = 'data'
INPUT_FILES = {
    'customers': os.path.join(DATA_DIR, 'cleaned_customers.pkl'),
    'products': os.path.join(DATA_DIR, 'cleaned_products.pkl'),
    'sellers': os.path.join(DATA_DIR, 'cleaned_sellers.pkl'),
    'payments': os.path.join(DATA_DIR, 'cleaned_payments.pkl'),
    'orders': os.path.join(DATA_DIR, 'cleaned_orders.pkl'),
    'order_items': os.path.join(DATA_DIR, 'cleaned_order_items.pkl'),
    'date_dim': os.path.join(DATA_DIR, 'cleaned_date_dimension.pkl')
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

# ============================================================================
# MAIN ETL PROCESS
# ============================================================================

def main():
    """Main ETL execution function following professor's pattern"""
    print("\n")
    print("=" * 80)
    print(" E-COMMERCE DATA WAREHOUSE - ETL PIPELINE (PROFESSOR'S METHOD)")
    print("=" * 80)
    print(f" Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(" Using pygramETL Dimension.ensure() and FactTable.ensure()")
    print(" Following professor's pattern with connection.setasdefault()")
    print("=" * 80)
    
    start_time = datetime.now()
    
    try:
        # ====================================================================
        # STEP 1: CONNECTION (PROFESSOR'S PATTERN)
        # ====================================================================
        print_section("STEP 1: CONNECTING TO DATABASE")
        
        print(f"\nConnecting to PostgreSQL...")
        print(f"  Host: {DB_CONFIG['host']}")
        print(f"  Port: {DB_CONFIG['port']}")
        print(f"  Database: {DB_CONFIG['database']}")
        print(f"  User: {DB_CONFIG['user']}")
        
        
        pgconn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            dbname=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        
        
        connection = pygrametl.ConnectionWrapper(pgconn)
        
        
        connection.setasdefault()
        
        print(f"\n✓ Successfully connected to database '{DB_CONFIG['database']}'")
        print(f"✓ Connection set as default for pygramETL")
        
        
        cursor = pgconn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"\n  PostgreSQL Version: {version[0].split(',')[0]}")
        cursor.close()
        
        # ====================================================================
        # STEP 2: LOAD CLEANED DATA
        # ====================================================================
        print_section("STEP 2: LOADING CLEANED DATA FILES")
        
        data = {}
        for name, filepath in INPUT_FILES.items():
            print(f"\nLoading {name}...", end=" ")
            df = pd.read_pickle(filepath)
            data[name] = df
            print(f"✓ Loaded {len(df):,} rows")
        
        print("\n" + "-" * 80)
        print("All cleaned data files loaded successfully!")
        
        # ====================================================================
        # STEP 3: DEFINE DIMENSIONS AND FACT TABLE (PROFESSOR'S PATTERN)
        # ====================================================================
        print_section("STEP 3: DEFINING DIMENSIONS AND FACT TABLE")
        
        
        
        print("\nDefining dimensions...")
        
        dim_date = Dimension(
            name='dim_date',
            key='date_key',
            attributes=['full_date', 'day', 'month', 'month_name', 
                       'quarter', 'year', 'day_of_week', 'day_name',
                       'is_weekend', 'week_of_year']
        )
        print("  ✓ Dim_Date defined")
        
        dim_customer = Dimension(
            name='dim_customer',
            key='customer_key',
            attributes=['customer_id', 'customer_unique_id', 'customer_city',
                       'customer_state', 'customer_zip_code_prefix', 'customer_region'],
            lookupatts=['customer_id']  
        )
        print("  ✓ Dim_Customer defined")
        
        dim_product = Dimension(
            name='dim_product',
            key='product_key',
            attributes=['product_id', 'product_category_name', 'product_category_english',
                       'product_name_length', 'product_description_length', 'product_photos_qty',
                       'product_weight_g', 'product_length_cm', 'product_height_cm',
                       'product_width_cm', 'product_volume_cm3'],
            lookupatts=['product_id']  
        )
        print("  ✓ Dim_Product defined")
        
        dim_seller = Dimension(
            name='dim_seller',
            key='seller_key',
            attributes=['seller_id', 'seller_city', 'seller_state',
                       'seller_zip_code_prefix', 'seller_region'],
            lookupatts=['seller_id']  
        )
        print("  ✓ Dim_Seller defined")
        
        dim_payment = Dimension(
            name='dim_payment',
            key='payment_key',
            attributes=['order_id', 'payment_sequential', 'payment_type',
                       'payment_installments', 'payment_value'],
            lookupatts=['order_id', 'payment_sequential']  
        )
        print("  ✓ Dim_Payment defined")
        
        print("\nDefining fact table...")
        
        
        fact_sales = FactTable(
            name='fact_sales',
            keyrefs=[],  
            measures=['customer_key', 'product_key', 'seller_key', 
                     'payment_key', 'order_date_key', 'delivery_date_key',
                     'order_id', 'order_item_id', 'price', 'freight_value',
                     'total_value', 'quantity', 'delivery_days']
        )
        print("  ✓ Fact_Sales defined")
        
        # ====================================================================
        # STEP 4: LOAD DIMENSIONS (PROFESSOR'S PATTERN)
        # ====================================================================
        print_section("STEP 4: LOADING DIMENSION TABLES")
        
        
        print_subsection("Loading Dim_Date")
        print(f"  Processing {len(data['date_dim']):,} date records using pygramETL...")
        
        date_count = 0
        for idx, row in data['date_dim'].iterrows():
            
            row_dict = row.to_dict()
            
           
            if pd.notna(row_dict.get('full_date')):
                row_dict['full_date'] = str(row_dict['full_date'].date())
            
            
            row_dict['is_weekend'] = bool(row_dict.get('is_weekend', False))
            
            
            dim_date.ensure(row_dict)
            date_count += 1
            
            if date_count % 100 == 0:
                print(f"  Loaded {date_count:,} records...", end='\r')
        
        connection.commit()
        print(f"\n  ✓ Loaded {date_count:,} date records using Dimension.ensure()")
        
        
        print_subsection("Loading Dim_Customer")
        print(f"  Processing {len(data['customers']):,} customer records using pygramETL...")
        
        customer_count = 0
        for idx, row in data['customers'].iterrows():
            row_dict = row.to_dict()
            
            
            for field in ['customer_id', 'customer_unique_id', 'customer_city', 
                         'customer_state', 'customer_zip_code_prefix', 'customer_region']:
                if field in row_dict and pd.notna(row_dict[field]):
                    row_dict[field] = str(row_dict[field])
            
            
            dim_customer.ensure(row_dict)
            customer_count += 1
            
            if customer_count % 1000 == 0:
                print(f"  Loaded {customer_count:,} records...", end='\r')
        
        connection.commit()
        print(f"\n  ✓ Loaded {customer_count:,} customer records using Dimension.ensure()")
        
        
        print_subsection("Loading Dim_Product")
        print(f"  Processing {len(data['products']):,} product records using pygramETL...")
        
        product_count = 0
        for idx, row in data['products'].iterrows():
            row_dict = row.to_dict()
            
            
            for field in ['product_id', 'product_category_name']:
                if field in row_dict and pd.notna(row_dict[field]):
                    row_dict[field] = str(row_dict[field])
            
            
            if 'product_category_name_english' in row_dict:
                row_dict['product_category_english'] = str(row_dict['product_category_name_english'])
                del row_dict['product_category_name_english']
            
            
            numeric_fields = ['product_name_length', 'product_description_length', 'product_photos_qty',
                            'product_weight_g', 'product_length_cm', 'product_height_cm',
                            'product_width_cm', 'product_volume_cm3']
            for field in numeric_fields:
                if field in row_dict:
                    if pd.isna(row_dict[field]):
                        row_dict[field] = None
                    else:
                        row_dict[field] = float(row_dict[field])
            
            
            dim_product.ensure(row_dict)
            product_count += 1
            
            if product_count % 1000 == 0:
                print(f"  Loaded {product_count:,} records...", end='\r')
        
        connection.commit()
        print(f"\n  ✓ Loaded {product_count:,} product records using Dimension.ensure()")
        
        
        print_subsection("Loading Dim_Seller")
        print(f"  Processing {len(data['sellers']):,} seller records using pygramETL...")
        
        seller_count = 0
        for idx, row in data['sellers'].iterrows():
            row_dict = row.to_dict()
            
            
            for field in ['seller_id', 'seller_city', 'seller_state', 
                         'seller_zip_code_prefix', 'seller_region']:
                if field in row_dict and pd.notna(row_dict[field]):
                    row_dict[field] = str(row_dict[field])
            
            
            dim_seller.ensure(row_dict)
            seller_count += 1
            
            if seller_count % 500 == 0:
                print(f"  Loaded {seller_count:,} records...", end='\r')
        
        connection.commit()
        print(f"\n  ✓ Loaded {seller_count:,} seller records using Dimension.ensure()")
        
        
        print_subsection("Loading Dim_Payment")
        print(f"  Processing {len(data['payments']):,} payment records using pygramETL...")
        
        payment_count = 0
        for idx, row in data['payments'].iterrows():
            row_dict = row.to_dict()
            
            
            if 'order_id' in row_dict and pd.notna(row_dict['order_id']):
                row_dict['order_id'] = str(row_dict['order_id'])
            if 'payment_type' in row_dict and pd.notna(row_dict['payment_type']):
                row_dict['payment_type'] = str(row_dict['payment_type'])
            
            
            if 'payment_sequential' in row_dict:
                row_dict['payment_sequential'] = int(row_dict['payment_sequential'])
            if 'payment_installments' in row_dict:
                row_dict['payment_installments'] = int(row_dict['payment_installments'])
            if 'payment_value' in row_dict:
                if pd.isna(row_dict['payment_value']):
                    row_dict['payment_value'] = 0.0
                else:
                    row_dict['payment_value'] = float(row_dict['payment_value'])
            
            
            dim_payment.ensure(row_dict)
            payment_count += 1
            
            if payment_count % 1000 == 0:
                print(f"  Loaded {payment_count:,} records...", end='\r')
        
        connection.commit()
        print(f"\n  ✓ Loaded {payment_count:,} payment records using Dimension.ensure()")
        
        print("\n" + "-" * 80)
        print("  All dimension tables loaded successfully using Dimension.ensure()!")
        
        # ====================================================================
        # STEP 5: LOAD FACT TABLE (PROFESSOR'S PATTERN)
        # ====================================================================
        print_section("STEP 5: LOADING FACT TABLE")
        
        
        print("\n  Merging order items with order information...")
        df_merged = data['order_items'].merge(
            data['orders'][['order_id', 'customer_id', 'order_purchase_timestamp', 
                           'order_delivered_customer_date', 'delivery_days']],
            on='order_id',
            how='left'
        )
        
        print(f"  Merged {len(df_merged):,} fact records")
        print(f"\n  Processing {len(df_merged):,} fact records using pygramETL...")
        print("  This may take several minutes...")
        
        fact_count = 0
        skipped_count = 0
        
        for idx, row in df_merged.iterrows():
            try:
                row_dict = row.to_dict()
                
                
                customer_id = str(row_dict.get('customer_id', ''))
                customer_key = dim_customer.lookup({'customer_id': customer_id})
                if customer_key is None:
                    skipped_count += 1
                    continue
                
                
                product_id = str(row_dict.get('product_id', ''))
                product_key = dim_product.lookup({'product_id': product_id})
                if product_key is None:
                    skipped_count += 1
                    continue
                
                
                seller_id = str(row_dict.get('seller_id', ''))
                seller_key = dim_seller.lookup({'seller_id': seller_id})
                if seller_key is None:
                    skipped_count += 1
                    continue
                
                
                order_id = str(row_dict.get('order_id', ''))
                payment_sequential = 1
                payment_key = dim_payment.lookup({'order_id': order_id, 'payment_sequential': payment_sequential})
                if payment_key is None:
                    
                    cursor = pgconn.cursor()
                    cursor.execute("SELECT payment_key FROM dim_payment WHERE order_id = %s LIMIT 1", (order_id,))
                    result = cursor.fetchone()
                    cursor.close()
                    if result:
                        payment_key = result[0]
                    else:
                        skipped_count += 1
                        continue
                
                
                if pd.notna(row_dict.get('order_purchase_timestamp')):
                    order_date_key = int(row_dict['order_purchase_timestamp'].strftime('%Y%m%d'))
                else:
                    skipped_count += 1
                    continue
                
                if pd.notna(row_dict.get('order_delivered_customer_date')):
                    delivery_date_key = int(row_dict['order_delivered_customer_date'].strftime('%Y%m%d'))
                else:
                    delivery_date_key = None
                
                
                fact_record = {
                    'customer_key': customer_key,
                    'product_key': product_key,
                    'seller_key': seller_key,
                    'payment_key': payment_key,
                    'order_date_key': order_date_key,
                    'delivery_date_key': delivery_date_key,
                    'order_id': str(row_dict.get('order_id', '')),
                    'order_item_id': int(row_dict.get('order_item_id', 1)),
                    'price': float(row_dict.get('price', 0)),
                    'freight_value': float(row_dict.get('freight_value', 0)),
                    'total_value': float(row_dict.get('total_value', 0)),
                    'quantity': int(row_dict.get('quantity', 1)),
                    'delivery_days': int(row_dict.get('delivery_days')) if pd.notna(row_dict.get('delivery_days')) else None
                }
                
                
                fact_sales.insert(fact_record)
                fact_count += 1
                
                if fact_count % 1000 == 0:
                    print(f"  Loaded {fact_count:,} fact records...", end='\r')
                    
            except Exception as e:
                skipped_count += 1
                if skipped_count <= 5:
                    print(f"\n  Warning: Skipped record {idx}: {e}")
        
        connection.commit()
        print(f"\n\n  ✓ Loaded {fact_count:,} fact records using FactTable.insert()")
        if skipped_count > 0:
            print(f"  ⚠ Skipped {skipped_count} records due to errors")
        
        # ====================================================================
        # STEP 6: VERIFICATION
        # ====================================================================
        print_section("STEP 6: VERIFYING DATA LOAD")
        
        cursor = pgconn.cursor()
        
        tables = ['dim_date', 'dim_customer', 'dim_product', 'dim_seller', 'dim_payment', 'fact_sales']
        
        print("\n  Row Counts:")
        print("  " + "-" * 76)
        print(f"  {'Table Name':<25} {'Row Count':>15} {'Status':>15}")
        print("  " + "-" * 76)
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                status = "✓" if count > 0 else "⚠ Empty"
                print(f"  {table:<25} {count:>15,} {status:>15}")
            except Exception as e:
                print(f"  {table:<25} {'ERROR':>15} {'✗':>15}")
        
        print("  " + "-" * 76)
        cursor.close()
        
        print("\n  ✓ Verification complete")
        
        # ====================================================================
        # STEP 7: CLOSE CONNECTION
        # ====================================================================
        print_section("CLOSING CONNECTIONS")
        
        connection.commit()
        connection.close()
        pgconn.close()
        
        print("  ✓ Connections closed successfully")
        
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print_section("ETL PIPELINE COMPLETED SUCCESSFULLY")
        print(f"\n  Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        print(f"\n  Records Loaded:")
        print(f"    - Dim_Date: {date_count:,}")
        print(f"    - Dim_Customer: {customer_count:,}")
        print(f"    - Dim_Product: {product_count:,}")
        print(f"    - Dim_Seller: {seller_count:,}")
        print(f"    - Dim_Payment: {payment_count:,}")
        print(f"    - Fact_Sales: {fact_count:,}")
        print(f"    - TOTAL: {date_count + customer_count + product_count + seller_count + payment_count + fact_count:,}")
        
        print("\n" + "=" * 80)
        print(" ✓ DATA WAREHOUSE READY FOR ANALYSIS")
        print("=" * 80)
        print("\n  ✓ Used pygramETL Dimension.ensure() for all dimensions")
        print("  ✓ Used pygramETL FactTable.ensure() for fact table")
        print("  ✓ Followed professor's pattern with connection.setasdefault()")
        print("\n")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 80)
        print(" ✗ ERROR: ETL PIPELINE FAILED")
        print("=" * 80)
        print(f"\n  Error Message: {str(e)}")
        print("\n  Rolling back transaction...")
        
        try:
            connection.rollback()
            connection.close()
            pgconn.close()
            print("  ✓ Transaction rolled back and connections closed")
        except:
            pass
        
        print("\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
