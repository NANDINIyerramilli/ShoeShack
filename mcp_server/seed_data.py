import sqlite3 
from pathlib import Path 
from faker import Faker 
import random 

fake = Faker() 
DB_PATH = Path("orders_complaints.db") 

def create_tables(conn): 
    conn.execute( """ CREATE TABLE IF NOT EXISTS orders ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, product TEXT, status TEXT, amount REAL, created_at TEXT ) """ ) 
    conn.execute( """ CREATE TABLE IF NOT EXISTS tickets ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, subject TEXT, description TEXT, status TEXT, priority TEXT, created_at TEXT ) """ ) 
    
def seed_orders(conn): 
    products = [ "iPhone 15", "Samsung TV", "Gaming Laptop", "Bluetooth Speaker", "Smart Watch", ] 
    statuses = ["processing", "shipped", "delivered"] 
    
    for _ in range(20): 
        conn.execute( """ INSERT INTO orders ( user_id, product, status, amount, created_at ) VALUES (?, ?, ?, ?, ?) """, ( f"user_{random.randint(1,5)}", random.choice(products), random.choice(statuses), round(random.uniform(100, 5000), 2), fake.date_time_this_year().isoformat(), ), ) 
        
        
def seed_tickets(conn): 
    priorities = ["low", "medium", "high"] 
    statuses = ["open", "closed", "in_progress"] 
    subjects = [ "Delayed Delivery", "Refund Issue", "Wrong Product", "Payment Failure", "Account Access", ] 
    for _ in range(15): 
        conn.execute( """ INSERT INTO tickets ( user_id, subject, description, status, priority, created_at ) VALUES (?, ?, ?, ?, ?, ?) """, ( f"user_{random.randint(1,5)}", random.choice(subjects), fake.text(max_nb_chars=100), random.choice(statuses), random.choice(priorities), fake.date_time_this_year().isoformat(), ), ) 
def main(): 
    conn = sqlite3.connect(DB_PATH) 
    create_tables(conn) 
    seed_orders(conn) 
    seed_tickets(conn) 
    conn.commit() 
    conn.close() 
    print("Database seeded successfully") 
if __name__ == "__main__": 
    main()