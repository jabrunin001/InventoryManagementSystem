"""
Simple Inventory Management System
----------------------------------
A Python implementation for interacting with the inventory database.
Provides core functionality for managing products, inventory, and transactions.
"""

import sqlite3
import os
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from dataclasses import dataclass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("inventory_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("inventory_system")

# Database configuration
DB_FILE = "inventory.db"

# Data classes for type safety and better code organization
@dataclass
class Product:
    product_id: Optional[int] = None
    sku: str = ""
    name: str = ""
    description: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    unit_price: float = 0.0
    min_stock_level: int = 0
    max_stock_level: Optional[int] = None
    is_active: bool = True

@dataclass
class InventoryTransaction:
    product_id: int
    location_id: int
    transaction_type_id: int
    quantity: int
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    transaction_id: Optional[int] = None
    transaction_date: Optional[str] = None

class DatabaseManager:
    """Manages database connections and provides utility methods"""
    
    def __init__(self, db_file: str = DB_FILE):
        """Initialize the database manager"""
        self.db_file = db_file
        self.conn = None
        self.initialize_db()
        
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection to the database"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return self.conn
    
    def close_connection(self) -> None:
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def initialize_db(self) -> None:
        """Initialize the database if it doesn't exist"""
        if not os.path.exists(self.db_file):
            logger.info(f"Creating new database file: {self.db_file}")
            
            # Create a connection
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Read and execute the schema SQL file
            try:
                with open("inventory_schema.sql", "r") as f:
                    schema_sql = f.read()
                    cursor.executescript(schema_sql)
                conn.commit()
                logger.info("Database schema created successfully")
            except Exception as e:
                logger.error(f"Error creating database schema: {str(e)}")
                conn.rollback()
                raise
            finally:
                cursor.close()
        else:
            logger.info(f"Using existing database file: {self.db_file}")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return the results as a list of dictionaries"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            # Convert sqlite3.Row objects to dictionaries
            result = [dict(row) for row in rows]
            return result
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        finally:
            cursor.close()
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the ID of the inserted row"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error executing insert: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            conn.rollback()
            raise
        finally:
            cursor.close()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an UPDATE query and return the number of affected rows"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing update: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            conn.rollback()
            raise
        finally:
            cursor.close()


class CategoryManager:
    """Manages categories in the inventory system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def add_category(self, name: str, description: Optional[str] = None) -> int:
        """Add a new category"""
        query = """
        INSERT INTO categories (name, description) 
        VALUES (?, ?)
        """
        params = (name, description)
        try:
            category_id = self.db_manager.execute_insert(query, params)
            logger.info(f"Added new category: {name} (ID: {category_id})")
            return category_id
        except Exception as e:
            logger.error(f"Failed to add category {name}: {str(e)}")
            raise
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        query = "SELECT * FROM categories ORDER BY name"
        return self.db_manager.execute_query(query)
    
    def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get a category by ID"""
        query = "SELECT * FROM categories WHERE category_id = ?"
        params = (category_id,)
        results = self.db_manager.execute_query(query, params)
        return results[0] if results else None
    
    def update_category(self, category_id: int, name: str, description: Optional[str] = None) -> bool:
        """Update a category"""
        query = """
        UPDATE categories 
        SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE category_id = ?
        """
        params = (name, description, category_id)
        try:
            rows_affected = self.db_manager.execute_update(query, params)
            success = rows_affected > 0
            if success:
                logger.info(f"Updated category ID {category_id}: {name}")
            else:
                logger.warning(f"No category found with ID {category_id} to update")
            return success
        except Exception as e:
            logger.error(f"Failed to update category {category_id}: {str(e)}")
            raise


class SupplierManager:
    """Manages suppliers in the inventory system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def add_supplier(self, name: str, contact_person: Optional[str] = None, 
                    email: Optional[str] = None, phone: Optional[str] = None, 
                    address: Optional[str] = None) -> int:
        """Add a new supplier"""
        query = """
        INSERT INTO suppliers (name, contact_person, email, phone, address) 
        VALUES (?, ?, ?, ?, ?)
        """
        params = (name, contact_person, email, phone, address)
        try:
            supplier_id = self.db_manager.execute_insert(query, params)
            logger.info(f"Added new supplier: {name} (ID: {supplier_id})")
            return supplier_id
        except Exception as e:
            logger.error(f"Failed to add supplier {name}: {str(e)}")
            raise
    
    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """Get all suppliers"""
        query = "SELECT * FROM suppliers WHERE is_active = 1 ORDER BY name"
        return self.db_manager.execute_query(query)
    
    def get_supplier(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """Get a supplier by ID"""
        query = "SELECT * FROM suppliers WHERE supplier_id = ?"
        params = (supplier_id,)
        results = self.db_manager.execute_query(query, params)
        return results[0] if results else None
    
    def update_supplier(self, supplier_id: int, name: str, contact_person: Optional[str] = None,
                       email: Optional[str] = None, phone: Optional[str] = None,
                       address: Optional[str] = None, is_active: bool = True) -> bool:
        """Update a supplier"""
        query = """
        UPDATE suppliers 
        SET name = ?, contact_person = ?, email = ?, phone = ?, 
            address = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE supplier_id = ?
        """
        params = (name, contact_person, email, phone, address, 1 if is_active else 0, supplier_id)
        try:
            rows_affected = self.db_manager.execute_update(query, params)
            success = rows_affected > 0
            if success:
                logger.info(f"Updated supplier ID {supplier_id}: {name}")
            else:
                logger.warning(f"No supplier found with ID {supplier_id} to update")
            return success
        except Exception as e:
            logger.error(f"Failed to update supplier {supplier_id}: {str(e)}")
            raise


class LocationManager:
    """Manages locations in the inventory system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def add_location(self, name: str, description: Optional[str] = None) -> int:
        """Add a new location"""
        query = """
        INSERT INTO locations (name, description) 
        VALUES (?, ?)
        """
        params = (name, description)
        try:
            location_id = self.db_manager.execute_insert(query, params)
            logger.info(f"Added new location: {name} (ID: {location_id})")
            return location_id
        except Exception as e:
            logger.error(f"Failed to add location {name}: {str(e)}")
            raise
    
    def get_all_locations(self) -> List[Dict[str, Any]]:
        """Get all locations"""
        query = "SELECT * FROM locations WHERE is_active = 1 ORDER BY name"
        return self.db_manager.execute_query(query)
    
    def get_location(self, location_id: int) -> Optional[Dict[str, Any]]:
        """Get a location by ID"""
        query = "SELECT * FROM locations WHERE location_id = ?"
        params = (location_id,)
        results = self.db_manager.execute_query(query, params)
        return results[0] if results else None


class ProductManager:
    """Manages products in the inventory system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def add_product(self, product: Product) -> int:
        """Add a new product"""
        query = """
        INSERT INTO products (
            sku, name, description, category_id, supplier_id, 
            unit_price, min_stock_level, max_stock_level, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            product.sku, product.name, product.description, product.category_id,
            product.supplier_id, product.unit_price, product.min_stock_level,
            product.max_stock_level, 1 if product.is_active else 0
        )
        try:
            product_id = self.db_manager.execute_insert(query, params)
            logger.info(f"Added new product: {product.name} (ID: {product_id})")
            return product_id
        except Exception as e:
            logger.error(f"Failed to add product {product.name}: {str(e)}")
            raise
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products"""
        query = """
        SELECT p.*, c.name as category_name, s.name as supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.is_active = 1
        ORDER BY p.name
        """
        return self.db_manager.execute_query(query)
    
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a product by ID"""
        query = """
        SELECT p.*, c.name as category_name, s.name as supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.product_id = ?
        """
        params = (product_id,)
        results = self.db_manager.execute_query(query, params)
        return results[0] if results else None
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get a product by SKU"""
        query = """
        SELECT p.*, c.name as category_name, s.name as supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.sku = ?
        """
        params = (sku,)
        results = self.db_manager.execute_query(query, params)
        return results[0] if results else None
    
    def update_product(self, product: Product) -> bool:
        """Update a product"""
        query = """
        UPDATE products 
        SET sku = ?, name = ?, description = ?, category_id = ?,
            supplier_id = ?, unit_price = ?, min_stock_level = ?,
            max_stock_level = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
        WHERE product_id = ?
        """
        params = (
            product.sku, product.name, product.description, product.category_id,
            product.supplier_id, product.unit_price, product.min_stock_level,
            product.max_stock_level, 1 if product.is_active else 0, product.product_id
        )
        try:
            rows_affected = self.db_manager.execute_update(query, params)
            success = rows_affected > 0
            if success:
                logger.info(f"Updated product ID {product.product_id}: {product.name}")
            else:
                logger.warning(f"No product found with ID {product.product_id} to update")
            return success
        except Exception as e:
            logger.error(f"Failed to update product {product.product_id}: {str(e)}")
            raise
    
    def search_products(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for products by name or SKU"""
        query = """
        SELECT p.*, c.name as category_name, s.name as supplier_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE (p.name LIKE ? OR p.sku LIKE ?) AND p.is_active = 1
        ORDER BY p.name
        """
        search_pattern = f"%{search_term}%"
        params = (search_pattern, search_pattern)
        return self.db_manager.execute_query(query, params)


class InventoryManager:
    """Manages inventory levels and transactions"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_inventory_levels(self, product_id: Optional[int] = None, 
                             location_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get current inventory levels, optionally filtered by product or location"""
        query_parts = [
            "SELECT i.*, p.name as product_name, p.sku, l.name as location_name",
            "FROM inventory i",
            "JOIN products p ON i.product_id = p.product_id",
            "JOIN locations l ON i.location_id = l.location_id",
            "WHERE 1=1"
        ]
        params = []
        
        if product_id is not None:
            query_parts.append("AND i.product_id = ?")
            params.append(product_id)
        
        if location_id is not None:
            query_parts.append("AND i.location_id = ?")
            params.append(location_id)
        
        query_parts.append("ORDER BY p.name, l.name")
        query = " ".join(query_parts)
        
        return self.db_manager.execute_query(query, tuple(params))
    
    def get_product_quantity(self, product_id: int, location_id: int) -> int:
        """Get the current quantity of a product at a specific location"""
        query = """
        SELECT quantity FROM inventory
        WHERE product_id = ? AND location_id = ?
        """
        params = (product_id, location_id)
        results = self.db_manager.execute_query(query, params)
        return results[0]["quantity"] if results else 0
    
    def update_inventory_quantity(self, product_id: int, location_id: int, 
                                 new_quantity: int, counted_at: Optional[str] = None) -> bool:
        """Update the inventory quantity for a product at a specific location"""
        # Check if record exists
        current_quantity = self.get_product_quantity(product_id, location_id)
        
        if counted_at is None:
            counted_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if current_quantity > 0:  # Record exists, update it
            query = """
            UPDATE inventory
            SET quantity = ?, last_counted_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE product_id = ? AND location_id = ?
            """
            params = (new_quantity, counted_at, product_id, location_id)
            try:
                self.db_manager.execute_update(query, params)
                logger.info(f"Updated inventory for product ID {product_id} at location {location_id}: {new_quantity}")
                return True
            except Exception as e:
                logger.error(f"Failed to update inventory quantity: {str(e)}")
                raise
        else:  # Record doesn't exist, insert new one
            query = """
            INSERT INTO inventory (product_id, location_id, quantity, last_counted_at)
            VALUES (?, ?, ?, ?)
            """
            params = (product_id, location_id, new_quantity, counted_at)
            try:
                self.db_manager.execute_insert(query, params)
                logger.info(f"Created inventory record for product ID {product_id} at location {location_id}: {new_quantity}")
                return True
            except Exception as e:
                logger.error(f"Failed to create inventory record: {str(e)}")
                raise
    
    def record_transaction(self, transaction: InventoryTransaction) -> int:
        """Record an inventory transaction and update inventory levels"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Start a transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Get the transaction type and its effect on inventory
            cursor.execute(
                "SELECT affects_inventory FROM transaction_types WHERE transaction_type_id = ?", 
                (transaction.transaction_type_id,)
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Invalid transaction type ID: {transaction.transaction_type_id}")
            
            affects_inventory = result["affects_inventory"]
            
            # Insert the transaction record
            if transaction.transaction_date is None:
                transaction.transaction_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            cursor.execute(
                """
                INSERT INTO inventory_transactions (
                    product_id, location_id, transaction_type_id, quantity,
                    transaction_date, reference_number, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction.product_id, transaction.location_id, 
                    transaction.transaction_type_id, transaction.quantity,
                    transaction.transaction_date, transaction.reference_number,
                    transaction.notes, transaction.created_by
                )
            )
            
            transaction_id = cursor.lastrowid
            
            # Update inventory levels if the transaction affects inventory
            if affects_inventory != 0:
                # Calculate the inventory change (positive for increase, negative for decrease)
                inventory_change = transaction.quantity * affects_inventory
                
                # Check if there's an existing inventory record
                cursor.execute(
                    "SELECT inventory_id, quantity FROM inventory WHERE product_id = ? AND location_id = ?",
                    (transaction.product_id, transaction.location_id)
                )
                inventory_record = cursor.fetchone()
                
                if inventory_record:
                    # Update existing inventory record
                    new_quantity = inventory_record["quantity"] + inventory_change
                    
                    # Prevent negative inventory if configured to do so
                    # For this simple implementation, we'll allow negative inventory
                    cursor.execute(
                        """
                        UPDATE inventory
                        SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE product_id = ? AND location_id = ?
                        """,
                        (new_quantity, transaction.product_id, transaction.location_id)
                    )
                else:
                    # Create a new inventory record
                    cursor.execute(
                        """
                        INSERT INTO inventory (product_id, location_id, quantity)
                        VALUES (?, ?, ?)
                        """,
                        (transaction.product_id, transaction.location_id, inventory_change)
                    )
            
            # Commit the transaction
            conn.commit()
            
            logger.info(f"Recorded transaction ID {transaction_id} for product {transaction.product_id}")
            return transaction_id
        
        except Exception as e:
            # Rollback in case of error
            conn.rollback()
            logger.error(f"Failed to record transaction: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def get_transaction_history(self, product_id: Optional[int] = None, 
                               location_id: Optional[int] = None,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history, optionally filtered by product, location, and date range"""
        query_parts = [
            "SELECT t.*, p.name as product_name, p.sku, l.name as location_name, tt.name as transaction_type",
            "FROM inventory_transactions t",
            "JOIN products p ON t.product_id = p.product_id",
            "JOIN locations l ON t.location_id = l.location_id",
            "JOIN transaction_types tt ON t.transaction_type_id = tt.transaction_type_id",
            "WHERE 1=1"
        ]
        params = []
        
        if product_id is not None:
            query_parts.append("AND t.product_id = ?")
            params.append(product_id)
        
        if location_id is not None:
            query_parts.append("AND t.location_id = ?")
            params.append(location_id)
        
        if start_date is not None:
            query_parts.append("AND t.transaction_date >= ?")
            params.append(start_date)
        
        if end_date is not None:
            query_parts.append("AND t.transaction_date <= ?")
            params.append(end_date)
        
        query_parts.append("ORDER BY t.transaction_date DESC")
        query_parts.append(f"LIMIT {limit}")
        
        query = " ".join(query_parts)
        
        return self.db_manager.execute_query(query, tuple(params))
    
    def get_low_stock_items(self) -> List[Dict[str, Any]]:
        """Get products that are below their minimum stock level"""
        query = """
        SELECT * FROM vw_reorder_list
        ORDER BY quantity_to_order DESC
        """
        return self.db_manager.execute_query(query)


class InventorySystem:
    """Main class for the inventory management system"""
    
    def __init__(self, db_file: str = DB_FILE):
        """Initialize the inventory system"""
        self.db_manager = DatabaseManager(db_file)
        self.category_manager = CategoryManager(self.db_manager)
        self.supplier_manager = SupplierManager(self.db_manager)
        self.location_manager = LocationManager(self.db_manager)
        self.product_manager = ProductManager(self.db_manager)
        self.inventory_manager = InventoryManager(self.db_manager)
        logger.info("Inventory Management System initialized")
    
    def close(self):
        """Close the inventory system and release resources"""
        self.db_manager.close_connection()
        logger.info("Inventory Management System closed")


# Example usage of the inventory system
def demo_inventory_system():
    """Demonstrate the functionality of the inventory system"""
    # Initialize the system
    inventory_system = InventorySystem()
    
    try:
        # Add some categories
        electronics_id = inventory_system.category_manager.add_category(
            "Electronics", "Electronic devices and components"
        )
        office_id = inventory_system.category_manager.add_category(
            "Office Supplies", "Office stationery and supplies"
        )
        
        # Add a supplier
        supplier_id = inventory_system.supplier_manager.add_supplier(
            "Tech Supplies Inc.", "John Doe", "john@techsupplies.com", "555-1234", "123 Tech St."
        )
        
        # Add locations
        warehouse_id = inventory_system.location_manager.add_location(
            "Main Warehouse", "Main storage facility"
        )
        store_id = inventory_system.location_manager.add_location(
            "Retail Store", "Customer-facing store"
        )
        
        # Add products
        laptop = Product(
            sku="TECH-001",
            name="Laptop Computer",
            description="High-performance laptop",
            category_id=electronics_id,
            supplier_id=supplier_id,
            unit_price=999.99,
            min_stock_level=5,
            max_stock_level=20
        )
        laptop_id = inventory_system.product_manager.add_product(laptop)
        
        paper = Product(
            sku="OFF-001",
            name="Printer Paper",
            description="A4 printer paper, 500 sheets",
            category_id=office_id,
            supplier_id=supplier_id,
            unit_price=4.99,
            min_stock_level=10,
            max_stock_level=100
        )
        paper_id = inventory_system.product_manager.add_product(paper)
        
        # Record inventory transactions
        # Initial stock receipt for laptops
        laptop_receipt = InventoryTransaction(
            product_id=laptop_id,
            location_id=warehouse_id,
            transaction_type_id=1,  # Purchase
            quantity=10,
            reference_number="PO-12345",
            notes="Initial stock",
            created_by="System"
        )
        inventory_system.inventory_manager.record_transaction(laptop_receipt)
        
        # Initial stock receipt for paper
        paper_receipt = InventoryTransaction(
            product_id=paper_id,
            location_id=warehouse_id,
            transaction_type_id=1,  # Purchase
            quantity=50,
            reference_number="PO-12345",
            notes="Initial stock",
            created_by="System"
        )
        inventory_system.inventory_manager.record_transaction(paper_receipt)
        
        # Transfer some laptops to the store
        laptop_transfer = InventoryTransaction(
            product_id=laptop_id,
            location_id=warehouse_id,
            transaction_type_id=5,  # Transfer Out
            quantity=3,
            reference_number="TRF-001",
            notes="Transfer to store",
            created_by="System"
        )
        inventory_system.inventory_manager.record_transaction(laptop_transfer)
        
        laptop_receive = InventoryTransaction(
            product_id=laptop_id,
            location_id=store_id,
            transaction_type_id=4,  # Transfer In
            quantity=3,
            reference_number="TRF-001",
            notes="Transfer from warehouse",
            created_by="System"
        )
        inventory_system.inventory_manager.record_transaction(laptop_receive)
        
        # Sell a laptop
        laptop_sale = InventoryTransaction(
            product_id=laptop_id,
            location_id=store_id,
            transaction_type_id=2,  # Sale
            quantity=1,
            reference_number="SALE-001",
            notes="Customer purchase",
            created_by="System"
        )
        inventory_system.inventory_manager.record_transaction(laptop_sale)
        
        # Check current inventory levels
        inventory_levels = inventory_system.inventory_manager.get_inventory_levels()
        print("\nCurrent Inventory Levels:")
        for item in inventory_levels:
            print(f"{item['product_name']} at {item['location_name']}: {item['quantity']} units")
        
        # Check transaction history for laptops
        laptop_transactions = inventory_system.inventory_manager.get_transaction_history(product_id=laptop_id)
        print("\nLaptop Transaction History:")
        for tx in laptop_transactions:
            print(f"{tx['transaction_date']} - {tx['transaction_type']}: {tx['quantity']} units")
        
    finally:
        # Close the system
        inventory_system.close()


if __name__ == "__main__":
    demo_inventory_system()