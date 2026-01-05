import sqlite3
import pandas as pd
import numpy as np

def create_dummy_db():
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        age INTEGER,
        signup_date DATE
    )
    ''')
    
    # Create Orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_name TEXT,
        amount DECIMAL(10, 2),
        order_date DATE,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Insert dummy data
    users_data = pd.DataFrame({
        'name': [f'User {i}' for i in range(100)],
        'email': [f'user{i}@example.com' for i in range(100)],
        'age': np.random.randint(18, 90, 100),
        'signup_date': pd.date_range(start='2020-01-01', periods=100)
    })
    
    users_data.to_sql('users', conn, if_exists='append', index=False)
    
    orders_data = pd.DataFrame({
        'user_id': np.random.randint(1, 101, 500),
        'product_name': np.random.choice(['Widget A', 'Widget B', 'Gadget X'], 500),
        'amount': np.random.uniform(10.0, 500.0, 500),
        'order_date': pd.date_range(start='2020-01-01', periods=500)
    })
    
    orders_data.to_sql('orders', conn, if_exists='append', index=False)
    
    conn.commit()
    conn.close()
    print("Database 'example.db' created with dummy data.")

if __name__ == '__main__':
    create_dummy_db()
