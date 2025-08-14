import sqlite3

# Initialize the database
def init_db():
    conn = sqlite3.connect("blacklist.db")
    c = conn.cursor()
    
    # Customers table
    c.execute('''CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    reason TEXT
                )''')

    # Appointments table
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    appointment_date TEXT,
                    status TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )''')

    # Calls table
    c.execute('''CREATE TABLE IF NOT EXISTS calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    call_date TEXT,
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )''')

    conn.commit()
    conn.close()

# Add new customer
def add_customer(name, phone, reason):
    conn = sqlite3.connect("blacklist.db")
    c = conn.cursor()
    c.execute("INSERT INTO customers (name, phone, reason) VALUES (?, ?, ?)", (name, phone, reason))
    conn.commit()
    conn.close()

# Fetch customers
def get_customers():
    conn = sqlite3.connect("blacklist.db")
    c = conn.cursor()
    c.execute("SELECT * FROM customers")
    rows = c.fetchall()
    conn.close()
    return rows
