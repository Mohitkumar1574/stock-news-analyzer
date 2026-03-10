import sqlite3
import pandas as pd
from datetime import datetime
import os
import json

class Database:
    def __init__(self, db_path='data/portfolio.db'):
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Portfolio table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                buy_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                threshold REAL NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (symbol) REFERENCES portfolio(symbol)
            )
        ''')
        
        # Dividends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dividends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                amount_per_share REAL NOT NULL,
                total_amount REAL NOT NULL,
                dividend_date TEXT NOT NULL,
                dividend_type TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (symbol) REFERENCES portfolio(symbol)
            )
        ''')
        
        # Alert history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                message TEXT NOT NULL,
                price_change REAL,
                triggered_at TEXT NOT NULL
            )
        ''')
        
        # ========== PAPER TRADING TABLES ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                buy_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                UNIQUE(user_id, symbol)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                symbol TEXT NOT NULL,
                transaction_type TEXT CHECK(transaction_type IN ('BUY', 'SELL')),
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                transaction_date TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_balance (
                user_id TEXT PRIMARY KEY,
                cash_balance REAL DEFAULT 100000.0,
                initial_balance REAL DEFAULT 100000.0,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ========== PORTFOLIO OPERATIONS ==========
    
    def add_portfolio_item(self, symbol, quantity, buy_price, buy_date, notes=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO portfolio (symbol, quantity, buy_price, buy_date, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol.upper(), quantity, buy_price, buy_date, notes, now, now))
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        return item_id
    
    def get_all_portfolio(self):
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM portfolio ORDER BY created_at DESC", conn)
        conn.close()
        return df
    
    def update_portfolio_item(self, item_id, quantity=None, buy_price=None, notes=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        updates = []
        params = []
        if quantity is not None:
            updates.append("quantity = ?")
            params.append(quantity)
        if buy_price is not None:
            updates.append("buy_price = ?")
            params.append(buy_price)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(item_id)
        
        cursor.execute(f"UPDATE portfolio SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()
    
    def delete_portfolio_item(self, item_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Delete related alerts and dividends first (cascade manually)
        cursor.execute("DELETE FROM alerts WHERE symbol IN (SELECT symbol FROM portfolio WHERE id = ?)", (item_id,))
        cursor.execute("DELETE FROM dividends WHERE symbol IN (SELECT symbol FROM portfolio WHERE id = ?)", (item_id,))
        cursor.execute("DELETE FROM portfolio WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
    
    def delete_all_portfolio(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alerts")
        cursor.execute("DELETE FROM dividends")
        cursor.execute("DELETE FROM portfolio")
        cursor.execute("DELETE FROM alert_history")
        conn.commit()
        conn.close()
    
    # ========== ALERTS OPERATIONS ==========
    
    def set_alert(self, symbol, threshold, enabled=1):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Check if alert exists
        cursor.execute("SELECT id FROM alerts WHERE symbol = ?", (symbol,))
        existing = cursor.fetchone()
        now = datetime.now().isoformat()
        if existing:
            cursor.execute('''
                UPDATE alerts SET threshold = ?, enabled = ?, created_at = ? WHERE symbol = ?
            ''', (threshold, enabled, now, symbol))
        else:
            cursor.execute('''
                INSERT INTO alerts (symbol, threshold, enabled, created_at)
                VALUES (?, ?, ?, ?)
            ''', (symbol, threshold, enabled, now))
        conn.commit()
        conn.close()
    
    def get_alerts(self, symbol=None):
        conn = self.get_connection()
        if symbol:
            df = pd.read_sql_query("SELECT * FROM alerts WHERE symbol = ?", conn, params=(symbol,))
        else:
            df = pd.read_sql_query("SELECT * FROM alerts", conn)
        conn.close()
        return df
    
    def delete_alert(self, alert_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()
    
    def add_alert_history(self, symbol, message, price_change):
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO alert_history (symbol, message, price_change, triggered_at)
            VALUES (?, ?, ?, ?)
        ''', (symbol, message, price_change, now))
        conn.commit()
        conn.close()
    
    def get_alert_history(self, limit=50):
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM alert_history ORDER BY triggered_at DESC LIMIT ?", conn, params=(limit,))
        conn.close()
        return df
    
    # ========== DIVIDENDS OPERATIONS ==========
    
    def add_dividend(self, symbol, amount_per_share, total_amount, dividend_date, dividend_type='Interim', notes=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO dividends (symbol, amount_per_share, total_amount, dividend_date, dividend_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol.upper(), amount_per_share, total_amount, dividend_date, dividend_type, notes, now))
        conn.commit()
        dividend_id = cursor.lastrowid
        conn.close()
        return dividend_id
    
    def get_dividends(self, symbol=None):
        conn = self.get_connection()
        if symbol:
            df = pd.read_sql_query("SELECT * FROM dividends WHERE symbol = ? ORDER BY dividend_date DESC", conn, params=(symbol,))
        else:
            df = pd.read_sql_query("SELECT * FROM dividends ORDER BY dividend_date DESC", conn)
        conn.close()
        return df
    
    def delete_dividend(self, dividend_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dividends WHERE id = ?", (dividend_id,))
        conn.commit()
        conn.close()
    
    # ========== PAPER TRADING OPERATIONS ==========
    
    def get_paper_balance(self, user_id='default'):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT cash_balance, initial_balance FROM paper_balance WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute('INSERT INTO paper_balance (user_id, cash_balance, initial_balance, updated_at) VALUES (?, ?, ?, ?)',
                           (user_id, 100000.0, 100000.0, datetime.now().isoformat()))
            conn.commit()
            cash = 100000.0
            initial = 100000.0
        else:
            cash, initial = row
        conn.close()
        return cash, initial

    def update_paper_balance(self, user_id, new_cash):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE paper_balance SET cash_balance = ?, updated_at = ? WHERE user_id = ?',
                       (new_cash, datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()

    def get_paper_holdings(self, user_id='default'):
        conn = self.get_connection()
        df = pd.read_sql_query('SELECT * FROM paper_portfolio WHERE user_id = ?', conn, params=(user_id,))
        conn.close()
        return df

    def add_paper_transaction(self, user_id, symbol, txn_type, quantity, price, total):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO paper_transactions (user_id, symbol, transaction_type, quantity, price, total, transaction_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, symbol, txn_type, quantity, price, total, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def update_paper_holdings(self, user_id, symbol, quantity, price, is_buy):
        conn = self.get_connection()
        cursor = conn.cursor()
        if is_buy:
            # Check if already have this stock
            cursor.execute('SELECT quantity, buy_price FROM paper_portfolio WHERE user_id = ? AND symbol = ?', (user_id, symbol))
            row = cursor.fetchone()
            if row:
                # Average down/up
                old_qty, old_price = row
                new_qty = old_qty + quantity
                new_avg_price = (old_price * old_qty + price * quantity) / new_qty
                cursor.execute('UPDATE paper_portfolio SET quantity = ?, buy_price = ?, buy_date = ? WHERE user_id = ? AND symbol = ?',
                               (new_qty, new_avg_price, datetime.now().isoformat(), user_id, symbol))
            else:
                cursor.execute('INSERT INTO paper_portfolio (user_id, symbol, quantity, buy_price, buy_date) VALUES (?, ?, ?, ?, ?)',
                               (user_id, symbol, quantity, price, datetime.now().isoformat()))
        else:  # SELL
            cursor.execute('SELECT quantity FROM paper_portfolio WHERE user_id = ? AND symbol = ?', (user_id, symbol))
            row = cursor.fetchone()
            if row:
                old_qty = row[0]
                new_qty = old_qty - quantity
                if new_qty <= 0:
                    cursor.execute('DELETE FROM paper_portfolio WHERE user_id = ? AND symbol = ?', (user_id, symbol))
                else:
                    cursor.execute('UPDATE paper_portfolio SET quantity = ?, buy_date = ? WHERE user_id = ? AND symbol = ?',
                                   (new_qty, datetime.now().isoformat(), user_id, symbol))
        conn.commit()
        conn.close()
        