-- Inventory Management System Database Schema

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Categories table - for grouping products
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table - sources of products
CREATE TABLE suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations table - where items are stored
CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table - core inventory items
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    category_id INTEGER,
    supplier_id INTEGER,
    unit_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    min_stock_level INTEGER DEFAULT 0,
    max_stock_level INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- Inventory table - current stock levels by location
CREATE TABLE inventory (
    inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    last_counted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    UNIQUE(product_id, location_id)
);

-- Transaction types table - for categorizing inventory movements
CREATE TABLE transaction_types (
    transaction_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    affects_inventory INTEGER NOT NULL, -- 1 for increase, -1 for decrease, 0 for no effect
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory transactions table - record of all inventory movements
CREATE TABLE inventory_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    transaction_type_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reference_number TEXT,
    notes TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    FOREIGN KEY (transaction_type_id) REFERENCES transaction_types(transaction_type_id)
);

-- Purchase orders table - for incoming inventory
CREATE TABLE purchase_orders (
    po_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_delivery_date TIMESTAMP,
    status TEXT DEFAULT 'draft', -- draft, submitted, received, cancelled
    total_amount DECIMAL(10, 2) DEFAULT 0.00,
    notes TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- Purchase order items - details of items in purchase orders
CREATE TABLE purchase_order_items (
    po_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    received_quantity INTEGER DEFAULT 0,
    line_total DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Insert default transaction types
INSERT INTO transaction_types (name, affects_inventory, description) VALUES
('Purchase', 1, 'Inventory received from supplier'),
('Sale', -1, 'Inventory sold to customer'),
('Adjustment', 0, 'Manual inventory adjustment'),
('Transfer In', 1, 'Inventory transferred in from another location'),
('Transfer Out', -1, 'Inventory transferred out to another location'),
('Return In', 1, 'Inventory returned from customer'),
('Return Out', -1, 'Inventory returned to supplier'),
('Write Off', -1, 'Inventory written off (damaged, lost, expired)');

-- Create indexes for performance
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_location ON inventory(location_id);
CREATE INDEX idx_transactions_product ON inventory_transactions(product_id);
CREATE INDEX idx_transactions_location ON inventory_transactions(location_id);
CREATE INDEX idx_transactions_type ON inventory_transactions(transaction_type_id);
CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_po_items_po ON purchase_order_items(po_id);
CREATE INDEX idx_po_items_product ON purchase_order_items(product_id);

-- Create views for common queries
-- Current inventory status
CREATE VIEW vw_current_inventory AS
SELECT 
    p.product_id,
    p.sku,
    p.name AS product_name,
    p.description,
    c.name AS category,
    s.name AS supplier,
    l.name AS location,
    i.quantity,
    p.unit_price,
    (p.unit_price * i.quantity) AS inventory_value,
    p.min_stock_level,
    p.max_stock_level,
    CASE 
        WHEN i.quantity <= p.min_stock_level THEN 'Low Stock'
        WHEN i.quantity >= p.max_stock_level THEN 'Overstocked'
        ELSE 'Optimal'
    END AS stock_status,
    i.last_counted_at
FROM 
    inventory i
JOIN 
    products p ON i.product_id = p.product_id
JOIN 
    categories c ON p.category_id = c.category_id
JOIN 
    suppliers s ON p.supplier_id = s.supplier_id
JOIN 
    locations l ON i.location_id = l.location_id
WHERE 
    p.is_active = 1;

-- Products that need reordering
CREATE VIEW vw_reorder_list AS
SELECT 
    p.product_id,
    p.sku,
    p.name,
    c.name AS category,
    s.name AS supplier,
    SUM(i.quantity) AS total_quantity,
    p.min_stock_level,
    p.max_stock_level,
    (p.min_stock_level - SUM(i.quantity)) AS quantity_to_order
FROM 
    products p
JOIN 
    inventory i ON p.product_id = i.product_id
JOIN 
    categories c ON p.category_id = c.category_id
JOIN 
    suppliers s ON p.supplier_id = s.supplier_id
WHERE 
    p.is_active = 1
GROUP BY 
    p.product_id
HAVING 
    SUM(i.quantity) < p.min_stock_level;

-- Recent transactions
CREATE VIEW vw_recent_transactions AS
SELECT 
    t.transaction_id,
    p.sku,
    p.name AS product_name,
    l.name AS location,
    tt.name AS transaction_type,
    t.quantity,
    t.transaction_date,
    t.reference_number,
    t.notes,
    t.created_by
FROM 
    inventory_transactions t
JOIN 
    products p ON t.product_id = p.product_id
JOIN 
    locations l ON t.location_id = l.location_id
JOIN 
    transaction_types tt ON t.transaction_type_id = tt.transaction_type_id
ORDER BY 
    t.transaction_date DESC;