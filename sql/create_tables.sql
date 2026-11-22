
DROP TABLE IF EXISTS fact_sales CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_seller CASCADE;
DROP TABLE IF EXISTS dim_payment CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

COMMIT;


-- ----------------------------------------------------------------------------
-- Dim_Customer: Customer demographic and location information
-- ----------------------------------------------------------------------------


CREATE TABLE dim_customer (
    customer_key            SERIAL PRIMARY KEY,
    customer_id             VARCHAR(50) NOT NULL UNIQUE,
    customer_unique_id      VARCHAR(50),
    customer_city           VARCHAR(100),
    customer_state          VARCHAR(2),
    customer_zip_code_prefix VARCHAR(10),
    customer_region         VARCHAR(20),
    
    
    created_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_customer_state ON dim_customer(customer_state);
CREATE INDEX idx_customer_city ON dim_customer(customer_city);
CREATE INDEX idx_customer_region ON dim_customer(customer_region);

COMMENT ON TABLE dim_customer IS 'Customer dimension - contains customer demographics and location';
COMMENT ON COLUMN dim_customer.customer_key IS 'Surrogate primary key';
COMMENT ON COLUMN dim_customer.customer_id IS 'Natural key from source system';
COMMENT ON COLUMN dim_customer.customer_region IS 'Derived geographic region based on state';

-- ----------------------------------------------------------------------------
-- Dim_Product: Product catalog with categories and attributes
-- ----------------------------------------------------------------------------


CREATE TABLE dim_product (
    product_key                 SERIAL PRIMARY KEY,
    product_id                  VARCHAR(50) NOT NULL UNIQUE,
    product_category_name       VARCHAR(100),
    product_category_english    VARCHAR(100),
    product_name_length         INTEGER,
    product_description_length  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            NUMERIC(10,2),
    product_length_cm           NUMERIC(10,2),
    product_height_cm           NUMERIC(10,2),
    product_width_cm            NUMERIC(10,2),
    product_volume_cm3          NUMERIC(10,2),
    
    
    created_date                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_product_category_english ON dim_product(product_category_english);
CREATE INDEX idx_product_category_name ON dim_product(product_category_name);

COMMENT ON TABLE dim_product IS 'Product dimension - contains product attributes and categories';
COMMENT ON COLUMN dim_product.product_key IS 'Surrogate primary key';
COMMENT ON COLUMN dim_product.product_id IS 'Natural key from source system';
COMMENT ON COLUMN dim_product.product_category_english IS 'English translation of product category';
COMMENT ON COLUMN dim_product.product_volume_cm3 IS 'Calculated volume (length * height * width)';

-- ----------------------------------------------------------------------------
-- Dim_Seller: Seller information and location
-- ----------------------------------------------------------------------------


CREATE TABLE dim_seller (
    seller_key              SERIAL PRIMARY KEY,
    seller_id               VARCHAR(50) NOT NULL UNIQUE,
    seller_city             VARCHAR(100),
    seller_state            VARCHAR(2),
    seller_zip_code_prefix  VARCHAR(10),
    seller_region           VARCHAR(20),
    
    
    created_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_seller_state ON dim_seller(seller_state);
CREATE INDEX idx_seller_city ON dim_seller(seller_city);
CREATE INDEX idx_seller_region ON dim_seller(seller_region);

COMMENT ON TABLE dim_seller IS 'Seller dimension - contains seller location and identification';
COMMENT ON COLUMN dim_seller.seller_key IS 'Surrogate primary key';
COMMENT ON COLUMN dim_seller.seller_id IS 'Natural key from source system';
COMMENT ON COLUMN dim_seller.seller_region IS 'Derived geographic region based on state';

-- ----------------------------------------------------------------------------
-- Dim_Payment: Payment method and installment information
-- ----------------------------------------------------------------------------


CREATE TABLE dim_payment (
    payment_key             SERIAL PRIMARY KEY,
    order_id                VARCHAR(50) NOT NULL,
    payment_sequential      INTEGER,
    payment_type            VARCHAR(50),
    payment_installments    INTEGER,
    payment_value           NUMERIC(10,2),
    
    
    created_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_payment_order_id ON dim_payment(order_id);
CREATE INDEX idx_payment_type ON dim_payment(payment_type);
CREATE INDEX idx_payment_installments ON dim_payment(payment_installments);

COMMENT ON TABLE dim_payment IS 'Payment dimension - contains payment methods and installment details';
COMMENT ON COLUMN dim_payment.payment_key IS 'Surrogate primary key';
COMMENT ON COLUMN dim_payment.order_id IS 'Links payment to order';
COMMENT ON COLUMN dim_payment.payment_sequential IS 'Sequence number for multiple payments on same order';
COMMENT ON COLUMN dim_payment.payment_installments IS 'Number of payment installments';

-- ----------------------------------------------------------------------------
-- Dim_Date: Standard date dimension for time-based analysis
-- ----------------------------------------------------------------------------


CREATE TABLE dim_date (
    date_key                INTEGER PRIMARY KEY,
    full_date               DATE NOT NULL UNIQUE,
    day                     INTEGER NOT NULL,
    month                   INTEGER NOT NULL,
    month_name              VARCHAR(20) NOT NULL,
    quarter                 INTEGER NOT NULL,
    year                    INTEGER NOT NULL,
    day_of_week             INTEGER NOT NULL,
    day_name                VARCHAR(20) NOT NULL,
    is_weekend              BOOLEAN NOT NULL,
    week_of_year            INTEGER NOT NULL,
    
    
    created_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_date_full_date ON dim_date(full_date);
CREATE INDEX idx_date_year_month ON dim_date(year, month);
CREATE INDEX idx_date_year_quarter ON dim_date(year, quarter);

COMMENT ON TABLE dim_date IS 'Date dimension - provides time attributes for temporal analysis';
COMMENT ON COLUMN dim_date.date_key IS 'Primary key in YYYYMMDD format (e.g., 20170515)';
COMMENT ON COLUMN dim_date.full_date IS 'Actual date value';
COMMENT ON COLUMN dim_date.day_of_week IS '1=Monday, 7=Sunday';
COMMENT ON COLUMN dim_date.is_weekend IS 'TRUE for Saturday and Sunday';

-- ============================================================================
-- CREATE FACT TABLE
-- ============================================================================


CREATE TABLE fact_sales (
    sales_id                SERIAL PRIMARY KEY,
    order_id                VARCHAR(50) NOT NULL,
    order_item_id           INTEGER NOT NULL,
    
    
    customer_key            INTEGER NOT NULL,
    product_key             INTEGER NOT NULL,
    seller_key              INTEGER NOT NULL,
    payment_key             INTEGER NOT NULL,
    order_date_key          INTEGER NOT NULL,
    delivery_date_key       INTEGER,
    
    
    price                   NUMERIC(10,2) NOT NULL,
    freight_value           NUMERIC(10,2) NOT NULL,
    total_value             NUMERIC(10,2) NOT NULL,
    quantity                INTEGER DEFAULT 1,
    delivery_days           INTEGER,
    
    
    created_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    
    UNIQUE(order_id, order_item_id),
    
    
    CONSTRAINT fk_sales_customer 
        FOREIGN KEY (customer_key) 
        REFERENCES dim_customer(customer_key)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_sales_product 
        FOREIGN KEY (product_key) 
        REFERENCES dim_product(product_key)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_sales_seller 
        FOREIGN KEY (seller_key) 
        REFERENCES dim_seller(seller_key)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_sales_payment 
        FOREIGN KEY (payment_key) 
        REFERENCES dim_payment(payment_key)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_sales_order_date 
        FOREIGN KEY (order_date_key) 
        REFERENCES dim_date(date_key)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
        
    CONSTRAINT fk_sales_delivery_date 
        FOREIGN KEY (delivery_date_key) 
        REFERENCES dim_date(date_key)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    
    
    CONSTRAINT chk_price_positive 
        CHECK (price >= 0),
        
    CONSTRAINT chk_freight_positive 
        CHECK (freight_value >= 0),
        
    CONSTRAINT chk_total_value_positive 
        CHECK (total_value >= 0),
        
    CONSTRAINT chk_quantity_positive 
        CHECK (quantity > 0),
        
    CONSTRAINT chk_delivery_days_reasonable 
        CHECK (delivery_days IS NULL OR delivery_days >= 0)
);


CREATE INDEX idx_fact_customer_key ON fact_sales(customer_key);
CREATE INDEX idx_fact_product_key ON fact_sales(product_key);
CREATE INDEX idx_fact_seller_key ON fact_sales(seller_key);
CREATE INDEX idx_fact_payment_key ON fact_sales(payment_key);
CREATE INDEX idx_fact_order_date_key ON fact_sales(order_date_key);
CREATE INDEX idx_fact_delivery_date_key ON fact_sales(delivery_date_key);
CREATE INDEX idx_fact_order_id ON fact_sales(order_id);


CREATE INDEX idx_fact_date_customer ON fact_sales(order_date_key, customer_key);
CREATE INDEX idx_fact_date_product ON fact_sales(order_date_key, product_key);
CREATE INDEX idx_fact_date_seller ON fact_sales(order_date_key, seller_key);

COMMENT ON TABLE fact_sales IS 'Sales fact table - one row per order item (grain)';
COMMENT ON COLUMN fact_sales.sales_id IS 'Surrogate primary key';
COMMENT ON COLUMN fact_sales.order_id IS 'Natural key - order identifier from source';
COMMENT ON COLUMN fact_sales.order_item_id IS 'Item sequence number within order';
COMMENT ON COLUMN fact_sales.price IS 'Item price excluding freight';
COMMENT ON COLUMN fact_sales.freight_value IS 'Shipping/freight cost';
COMMENT ON COLUMN fact_sales.total_value IS 'Total value (price + freight_value)';
COMMENT ON COLUMN fact_sales.quantity IS 'Quantity of items (typically 1 per row)';
COMMENT ON COLUMN fact_sales.delivery_days IS 'Days between order date and delivery date';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================


SELECT 
    tablename,
    schemaname
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('dim_customer', 'dim_product', 'dim_seller', 
                      'dim_payment', 'dim_date', 'fact_sales')
ORDER BY tablename;


SELECT 'dim_customer' AS table_name, COUNT(*) AS row_count FROM dim_customer
UNION ALL
SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL
SELECT 'dim_seller', COUNT(*) FROM dim_seller
UNION ALL
SELECT 'dim_payment', COUNT(*) FROM dim_payment
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'fact_sales', COUNT(*) FROM fact_sales
ORDER BY table_name;

COMMIT;


