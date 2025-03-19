"""
Inventory Management System - Command Line Interface
---------------------------------------------------
A simple CLI for interacting with the inventory system.
"""

import os
import sys
import cmd
import textwrap
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import the inventory system
from inventory_system import (
    InventorySystem, Product, InventoryTransaction,
    logger
)

class InventoryCLI(cmd.Cmd):
    """Command-line interface for the Inventory Management System"""
    
    intro = textwrap.dedent("""
    =====================================
    Inventory Management System
    =====================================
    Type 'help' or '?' to list commands.
    Type 'exit' or 'quit' to exit.
    """)
    
    prompt = "inventory> "
    
    def __init__(self):
        super().__init__()
        self.inventory_system = InventorySystem()
        self.current_product_id = None
        self.current_location_id = None
    
    def do_exit(self, arg):
        """Exit the program"""
        self.inventory_system.close()
        print("Goodbye!")
        return True
    
    def do_quit(self, arg):
        """Exit the program"""
        return self.do_exit(arg)
    
    def do_categories(self, arg):
        """List all categories"""
        categories = self.inventory_system.category_manager.get_all_categories()
        if not categories:
            print("No categories found.")
            return
        
        print("\nCategories:")
        print("-" * 50)
        print(f"{'ID':<5} {'Name':<30} {'Description':<40}")
        print("-" * 50)
        for category in categories:
            print(f"{category['category_id']:<5} {category['name']:<30} {category['description'] or '':<40}")
    
    def do_add_category(self, arg):
        """Add a new category"""
        name = input("Category name: ")
        description = input("Description (optional): ")
        
        try:
            category_id = self.inventory_system.category_manager.add_category(name, description)
            print(f"Category added with ID: {category_id}")
        except Exception as e:
            print(f"Error adding category: {str(e)}")
    
    def do_suppliers(self, arg):
        """List all suppliers"""
        suppliers = self.inventory_system.supplier_manager.get_all_suppliers()
        if not suppliers:
            print("No suppliers found.")
            return
        
        print("\nSuppliers:")
        print("-" * 80)
        print(f"{'ID':<5} {'Name':<30} {'Contact':<20} {'Email':<25}")
        print("-" * 80)
        for supplier in suppliers:
            print(f"{supplier['supplier_id']:<5} {supplier['name']:<30} {supplier['contact_person'] or '':<20} {supplier['email'] or '':<25}")
    
    def do_add_supplier(self, arg):
        """Add a new supplier"""
        name = input("Supplier name: ")
        contact = input("Contact person (optional): ")
        email = input("Email (optional): ")
        phone = input("Phone (optional): ")
        address = input("Address (optional): ")
        
        try:
            supplier_id = self.inventory_system.supplier_manager.add_supplier(name, contact, email, phone, address)
            print(f"Supplier added with ID: {supplier_id}")
        except Exception as e:
            print(f"Error adding supplier: {str(e)}")
    
    def do_locations(self, arg):
        """List all locations"""
        locations = self.inventory_system.location_manager.get_all_locations()
        if not locations:
            print("No locations found.")
            return
        
        print("\nLocations:")
        print("-" * 60)
        print(f"{'ID':<5} {'Name':<30} {'Description':<40}")
        print("-" * 60)
        for location in locations:
            print(f"{location['location_id']:<5} {location['name']:<30} {location['description'] or '':<40}")
    
    def do_add_location(self, arg):
        """Add a new location"""
        name = input("Location name: ")
        description = input("Description (optional): ")
        
        try:
            location_id = self.inventory_system.location_manager.add_location(name, description)
            print(f"Location added with ID: {location_id}")
        except Exception as e:
            print(f"Error adding location: {str(e)}")
    
    def do_products(self, arg):
        """List all products"""
        products = self.inventory_system.product_manager.get_all_products()
        if not products:
            print("No products found.")
            return
        
        print("\nProducts:")
        print("-" * 100)
        print(f"{'ID':<5} {'SKU':<10} {'Name':<30} {'Category':<15} {'Price':<10} {'Min Stock':<10}")
        print("-" * 100)
        for product in products:
            print(f"{product['product_id']:<5} {product['sku']:<10} {product['name']:<30} {product['category_name'] or 'N/A':<15} ${product['unit_price']:<9.2f} {product['min_stock_level']:<10}")
    
    def do_product(self, arg):
        """Show details for a specific product. Usage: product <id>"""
        try:
            product_id = int(arg.strip())
            product = self.inventory_system.product_manager.get_product(product_id)
            if not product:
                print(f"Product with ID {product_id} not found.")
                return
            
            print("\nProduct Details:")
            print("-" * 60)
            print(f"ID:          {product['product_id']}")
            print(f"SKU:         {product['sku']}")
            print(f"Name:        {product['name']}")
            print(f"Description: {product['description'] or 'N/A'}")
            print(f"Category:    {product['category_name'] or 'N/A'}")
            print(f"Supplier:    {product['supplier_name'] or 'N/A'}")
            print(f"Price:       ${product['unit_price']:.2f}")
            print(f"Min Stock:   {product['min_stock_level']}")
            print(f"Max Stock:   {product['max_stock_level'] or 'N/A'}")
            print("-" * 60)
            
            # Also show inventory levels for this product
            self.do_inventory(str(product_id))
            
            # Set as current product for easier transactions
            self.current_product_id = product_id
            print(f"Set {product['name']} as the current product.")
        except ValueError:
            print("Please provide a valid product ID.")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_add_product(self, arg):
        """Add a new product"""
        print("\nAdding a new product:")
        print("-" * 30)
        
        # Show categories for reference
        self.do_categories('')
        category_id = input("\nCategory ID (optional): ")
        category_id = int(category_id) if category_id.strip() else None
        
        # Show suppliers for reference
        self.do_suppliers('')
        supplier_id = input("\nSupplier ID (optional): ")
        supplier_id = int(supplier_id) if supplier_id.strip() else None
        
        sku = input("SKU: ")
        name = input("Name: ")
        description = input("Description (optional): ")
        
        unit_price = input("Unit price: ")
        unit_price = float(unit_price) if unit_price.strip() else 0.0
        
        min_stock = input("Minimum stock level: ")
        min_stock = int(min_stock) if min_stock.strip() else 0
        
        max_stock = input("Maximum stock level (optional): ")
        max_stock = int(max_stock) if max_stock.strip() else None
        
        product = Product(
            sku=sku,
            name=name,
            description=description,
            category_id=category_id,
            supplier_id=supplier_id,
            unit_price=unit_price,
            min_stock_level=min_stock,
            max_stock_level=max_stock
        )
        
        try:
            product_id = self.inventory_system.product_manager.add_product(product)
            print(f"Product added with ID: {product_id}")
            
            # Ask if they want to add initial inventory
            add_inventory = input("Add initial inventory? (y/n): ").lower().strip()
            if add_inventory == 'y':
                self.do_locations('')
                location_id = input("\nLocation ID: ")
                try:
                    location_id = int(location_id)
                    quantity = int(input("Quantity: "))
                    ref_number = input("Reference number (optional): ")
                    notes = input("Notes (optional): ")
                    
                    transaction = InventoryTransaction(
                        product_id=product_id,
                        location_id=location_id,
                        transaction_type_id=1,  # Purchase
                        quantity=quantity,
                        reference_number=ref_number,
                        notes=notes,
                        created_by="CLI User"
                    )
                    
                    self.inventory_system.inventory_manager.record_transaction(transaction)
                    print(f"Added initial inventory of {quantity} units.")
                except ValueError:
                    print("Invalid input. Initial inventory not added.")
        except Exception as e:
            print(f"Error adding product: {str(e)}")
    
    def do_inventory(self, arg):
        """Show inventory levels, optionally filtered by product ID"""
        product_id = None
        
        if arg.strip():
            try:
                product_id = int(arg.strip())
            except ValueError:
                print("Invalid product ID. Showing all inventory.")
        
        inventory = self.inventory_system.inventory_manager.get_inventory_levels(product_id=product_id)
        
        if not inventory:
            print("No inventory records found.")
            return
        
        print("\nCurrent Inventory Levels:")
        print("-" * 80)
        print(f"{'Product':<30} {'SKU':<10} {'Location':<20} {'Quantity':<10}")
        print("-" * 80)
        for item in inventory:
            print(f"{item['product_name']:<30} {item['sku']:<10} {item['location_name']:<20} {item['quantity']:<10}")
    
    def do_low_stock(self, arg):
        """Show products with low stock levels"""
        low_stock = self.inventory_system.inventory_manager.get_low_stock_items()
        
        if not low_stock:
            print("No low stock items found.")
            return
        
        print("\nLow Stock Items:")
        print("-" * 90)
        print(f"{'Product':<30} {'SKU':<10} {'Category':<15} {'Current':<10} {'Min':<10} {'To Order':<10}")
        print("-" * 90)
        for item in low_stock:
            print(f"{item['name']:<30} {item['sku']:<10} {item['category']:<15} {item['total_quantity']:<10} {item['min_stock_level']:<10} {item['quantity_to_order']:<10}")
    
    def do_transaction(self, arg):
        """Record a new inventory transaction"""
        print("\nRecording a new inventory transaction:")
        print("-" * 40)
        
        # If no current product, ask for one
        if self.current_product_id is None:
            self.do_products('')
            product_id = input("\nProduct ID: ")
            try:
                product_id = int(product_id)
                product = self.inventory_system.product_manager.get_product(product_id)
                if not product:
                    print(f"Product with ID {product_id} not found.")
                    return
                self.current_product_id = product_id
            except ValueError:
                print("Invalid product ID.")
                return
        else:
            product = self.inventory_system.product_manager.get_product(self.current_product_id)
            print(f"Using current product: {product['name']} (ID: {self.current_product_id})")
            change_product = input("Change product? (y/n): ").lower().strip()
            if change_product == 'y':
                self.do_products('')
                product_id = input("\nProduct ID: ")
                try:
                    product_id = int(product_id)
                    product = self.inventory_system.product_manager.get_product(product_id)
                    if not product:
                        print(f"Product with ID {product_id} not found.")
                        return
                    self.current_product_id = product_id
                except ValueError:
                    print("Invalid product ID.")
                    return
        
        # Get location
        self.do_locations('')
        location_id = input("\nLocation ID: ")
        try:
            location_id = int(location_id)
            location = self.inventory_system.location_manager.get_location(location_id)
            if not location:
                print(f"Location with ID {location_id} not found.")
                return
        except ValueError:
            print("Invalid location ID.")
            return
        
        # Get transaction type
        print("\nTransaction Types:")
        print("1: Purchase (Increase)")
        print("2: Sale (Decrease)")
        print("3: Adjustment")
        print("4: Transfer In (Increase)")
        print("5: Transfer Out (Decrease)")
        print("6: Return In (Increase)")
        print("7: Return Out (Decrease)")
        print("8: Write Off (Decrease)")
        
        transaction_type_id = input("\nTransaction Type ID: ")
        try:
            transaction_type_id = int(transaction_type_id)
            if transaction_type_id < 1 or transaction_type_id > 8:
                print("Invalid transaction type ID.")
                return
        except ValueError:
            print("Invalid transaction type ID.")
            return
        
        # Get quantity
        quantity = input("Quantity: ")
        try:
            quantity = int(quantity)
            if quantity <= 0:
                print("Quantity must be positive.")
                return
        except ValueError:
            print("Invalid quantity.")
            return
        
        # Get additional details
        reference_number = input("Reference Number (optional): ")
        notes = input("Notes (optional): ")
        
        # Create and record the transaction
        transaction = InventoryTransaction(
            product_id=self.current_product_id,
            location_id=location_id,
            transaction_type_id=transaction_type_id,
            quantity=quantity,
            reference_number=reference_number,
            notes=notes,
            created_by="CLI User"
        )
        
        try:
            transaction_id = self.inventory_system.inventory_manager.record_transaction(transaction)
            print(f"Transaction recorded with ID: {transaction_id}")
            
            # Show updated inventory
            self.do_inventory(str(self.current_product_id))
        except Exception as e:
            print(f"Error recording transaction: {str(e)}")
    
    def do_history(self, arg):
        """Show transaction history. Usage: history [product_id] [limit]"""
        args = arg.strip().split()
        product_id = None
        limit = 10
        
        if len(args) >= 1:
            try:
                product_id = int(args[0])
            except ValueError:
                print("Invalid product ID. Showing all transactions.")
        
        if len(args) >= 2:
            try:
                limit = int(args[1])
            except ValueError:
                print("Invalid limit. Using default limit of 10.")
        
        transactions = self.inventory_system.inventory_manager.get_transaction_history(
            product_id=product_id, limit=limit
        )
        
        if not transactions:
            print("No transactions found.")
            return
        
        print("\nTransaction History:")
        print("-" * 100)
        print(f"{'ID':<5} {'Date':<20} {'Product':<25} {'Location':<15} {'Type':<12} {'Qty':<5} {'Ref':<10}")
        print("-" * 100)
        for tx in transactions:
            print(f"{tx['transaction_id']:<5} {tx['transaction_date']:<20} {tx['product_name'][:25]:<25} {tx['location_name'][:15]:<15} {tx['transaction_type']:<12} {tx['quantity']:<5} {tx['reference_number'] or '':<10}")
    
    def do_search(self, arg):
        """Search for products. Usage: search <term>"""
        if not arg.strip():
            print("Please provide a search term.")
            return
        
        search_term = arg.strip()
        results = self.inventory_system.product_manager.search_products(search_term)
        
        if not results:
            print(f"No products found matching '{search_term}'.")
            return
        
        print(f"\nSearch results for '{search_term}':")
        print("-" * 80)
        print(f"{'ID':<5} {'SKU':<10} {'Name':<30} {'Category':<15} {'Price':<10}")
        print("-" * 80)
        for product in results:
            print(f"{product['product_id']:<5} {product['sku']:<10} {product['name']:<30} {product['category_name'] or 'N/A':<15} ${product['unit_price']:<9.2f}")
    
    def do_help(self, arg):
        """List available commands with brief descriptions"""
        cmd.Cmd.do_help(self, arg)


if __name__ == "__main__":
    InventoryCLI().cmdloop()