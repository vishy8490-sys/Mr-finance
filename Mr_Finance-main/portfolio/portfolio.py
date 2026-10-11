from database.models import get_db

def get_portfolio(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM portfolios WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_stock(user_id, symbol, quantity):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM portfolios WHERE user_id=? AND symbol=?", (user_id, symbol))
    if c.fetchone():
        c.execute("UPDATE portfolios SET quantity=? WHERE user_id=? AND symbol=?",
                  (quantity, user_id, symbol))
    else:
        c.execute("INSERT INTO portfolios (user_id, symbol, quantity) VALUES (?,?,?)",
                  (user_id, symbol, quantity))
    conn.commit()
    conn.close()

def delete_stock(user_id, symbol):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM portfolios WHERE user_id=? AND symbol=?", (user_id, symbol))
    conn.commit()
    conn.close()
