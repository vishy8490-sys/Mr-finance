import hashlib, os
from database.models import get_db

def hash_password(password):
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password, stored_hash):
    try:
        salt, hashed = stored_hash.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == hashed
    except:
        return False

def register_user(username, password, email=''):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, email) VALUES (?,?,?)",
                  (username, hash_password(password), email))
        conn.commit()
        return True, "Registration successful"
    except:
        return False, "Username already exists"
    finally:
        conn.close()

def login_user(username, password):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user and verify_password(password, user['password_hash']):
        return True, dict(user)
    return False, None
