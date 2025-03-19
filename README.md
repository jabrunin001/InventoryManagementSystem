# Inventory Management System

## Introduction
The Inventory Management System is a command-line application built in Python that allows users to manage inventory effectively. It provides functionalities to handle products, suppliers, categories, locations, and inventory transactions using an SQLite database.

## Key Features
- **Product Management**: Add, update, and view products with details like SKU, name, description, price, and stock levels.
- **Category Management**: Create and manage product categories.
- **Supplier Management**: Add and manage suppliers for products.
- **Location Management**: Track different storage locations for inventory.
- **Transaction Recording**: Record various inventory transactions (purchases, sales, transfers).
- **Low Stock Monitoring**: Identify products that are below their minimum stock levels.

## Requirements
- Python 3.x
- SQLite3

## Getting Started

### Installation
1. **Clone the Repository**:
   ```bash
   git clone 
   cd InventorySystemArchitectureProblem
   ```

2. **Install Dependencies** (if applicable):
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up the Database**:
   Run the following command to create the SQLite database schema:
   ```bash
   python inventory_system.py
   ```

### Running the Application
To start the command-line interface, execute:
```bash
python inventory_cli.py
```

### Available Commands
- `categories`: Display all categories.
- `add_category`: Add a new category.
- `suppliers`: Display all suppliers.
- `add_supplier`: Add a new supplier.
- `locations`: Display all locations.
- `add_location`: Add a new location.
- `products`: Display all products.
- `add_product`: Add a new product.
- `inventory`: Show current inventory levels.
- `low_stock`: List products with low stock levels.
- `transaction`: Record a new inventory transaction.
- `history`: View transaction history for a specific product.
- `search`: Search for products by name or SKU.
- `exit` or `quit`: Exit the application.

## Logging
The application logs important events and errors to `inventory_system.log`, which can be useful for monitoring and debugging.


## Contributing
Contributions are welcome! Feel free to submit a pull request or open an issue for suggestions or improvements.

## Contact
For questions or feedback, please contact [Your Name] at [Your Email].
