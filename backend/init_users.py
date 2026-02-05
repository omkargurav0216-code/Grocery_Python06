from db import get_connection, create_tables
from werkzeug.security import generate_password_hash

def init_users():
    create_tables()
    conn = get_connection()
    cursor = conn.cursor()
    
    users = [
        ('admin', 'admin123', 'admin'),
        ('customer', 'custom123', 'customer')
    ]
    
    for username, password, role in users:
        try:
            password_hash = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                           (username, password_hash, role))
            print(f"User '{username}' added successfully.")
        except Exception as e:
            print(f"Error adding user '{username}': {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_users()