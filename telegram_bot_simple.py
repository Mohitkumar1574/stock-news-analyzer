import os
import time
import sqlite3
import threading
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load token from .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN not found in .env file")

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.scrapers.stock_data_fetcher import StockDataFetcher
from src.analysis.technical_indicators import TechnicalIndicators

DB_PATH = "data/portfolio.db"

# ========== TELEGRAM BOT CLASS ==========
class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.fetcher = StockDataFetcher()
        self.running = True
        
    def send_message(self, chat_id, text, parse_mode="HTML"):
        """Send message via Telegram API"""
        url = f"{self.base_url}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Send error: {e}")
    
    def get_updates(self, offset=None):
        """Get new messages"""
        url = f"{self.base_url}/getUpdates"
        params = {"timeout": 30, "offset": offset} if offset else {"timeout": 30}
        try:
            res = requests.get(url, params=params)
            return res.json().get("result", [])
        except:
            return []
    
    def get_db(self):
        return sqlite3.connect(DB_PATH)
    
    def save_chat_id(self, chat_id):
        """Save user chat ID to database"""
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                       (f"chat_id_{chat_id}", str(chat_id)))
        conn.commit()
        conn.close()
    
    def get_all_chat_ids(self):
        """Get all registered chat IDs"""
        conn = self.get_db()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        cursor.execute("SELECT value FROM settings WHERE key LIKE 'chat_id_%'")
        rows = cursor.fetchall()
        conn.close()
        return [int(r[0]) for r in rows]
    
    # ===== COMMAND HANDLERS =====
    def handle_start(self, chat_id):
        self.save_chat_id(chat_id)
        msg = (
            "👋 Bot started!\n"
            "Commands:\n"
            "/status - Portfolio status\n"
            "/alerts - Active alerts\n"
            "/buy - Check buy signals\n"
            "/help - Help"
        )
        self.send_message(chat_id, msg)
    
    def handle_status(self, chat_id):
        self.save_chat_id(chat_id)
        conn = self.get_db()
        portfolio_df = pd.read_sql_query("SELECT * FROM portfolio", conn)
        conn.close()
        
        if portfolio_df.empty:
            self.send_message(chat_id, "📭 Portfolio empty. Add stocks in web app first.")
            return
        
        lines = ["<b>📊 Portfolio Status</b>\n"]
        total_investment = 0
        total_current = 0
        
        for _, item in portfolio_df.iterrows():
            stock_data = self.fetcher.get_stock_data(item['symbol'], period="1d")
            if stock_data:
                current_price = stock_data['current_price']
                investment = item['quantity'] * item['buy_price']
                current_value = item['quantity'] * current_price
                pl = current_value - investment
                pl_pct = (pl / investment) * 100 if investment else 0
                total_investment += investment
                total_current += current_value
                emoji = "🟢" if pl >= 0 else "🔴"
                lines.append(f"{emoji} <b>{item['symbol']}</b>: ₹{current_price:.2f} | {pl:+.2f} ({pl_pct:+.1f}%)")
        
        total_pl = total_current - total_investment
        total_pl_pct = (total_pl / total_investment) * 100 if total_investment else 0
        lines.append(f"\n<b>Total:</b> ₹{total_investment:,.0f} → ₹{total_current:,.0f} ({total_pl_pct:+.1f}%)")
        self.send_message(chat_id, "\n".join(lines))
    
    def handle_alerts(self, chat_id):
        self.save_chat_id(chat_id)
        conn = self.get_db()
        alerts_df = pd.read_sql_query("SELECT * FROM alerts WHERE enabled=1", conn)
        conn.close()
        
        if alerts_df.empty:
            self.send_message(chat_id, "🔕 No active alerts.")
        else:
            lines = ["<b>🔔 Active Alerts</b>\n"]
            for _, row in alerts_df.iterrows():
                lines.append(f"• {row['symbol']}: {row['threshold']}%")
            self.send_message(chat_id, "\n".join(lines))
    
    def handle_buy(self, chat_id):
        self.save_chat_id(chat_id)
        self.send_message(chat_id, "🔍 Checking buy signals...")
        
        conn = self.get_db()
        portfolio_df = pd.read_sql_query("SELECT * FROM portfolio", conn)
        conn.close()
        
        if portfolio_df.empty:
            self.send_message(chat_id, "📭 Portfolio empty.")
            return
        
        buy_signals = []
        for _, item in portfolio_df.iterrows():
            stock_data = self.fetcher.get_stock_data(item['symbol'], period="1mo")
            if not stock_data:
                continue
            
            day_change = stock_data.get('day_change', 0)
            hist = stock_data.get('historical', pd.DataFrame())
            
            # Price-based logic (same as analysis page)
            if day_change > 1.0:
                buy_score = 0.7
            elif day_change < -0.5:
                buy_score = 0.3
            else:
                buy_score = 0.5
            
            if not hist.empty and 'RSI' in hist.columns:
                rsi = hist['RSI'].iloc[-1]
                if rsi < 30:
                    buy_score += 0.05
                elif rsi > 70:
                    buy_score -= 0.05
            
            if buy_score > 0.6:
                buy_signals.append((item['symbol'], buy_score, stock_data['current_price']))
        
        if not buy_signals:
            self.send_message(chat_id, "📉 No buy signals.")
        else:
            lines = ["<b>🟢 BUY SIGNALS</b>\n"]
            for sym, score, price in buy_signals:
                lines.append(f"• {sym}: ₹{price:.2f} ({score*100:.1f}% confidence)")
            self.send_message(chat_id, "\n".join(lines))
    
    def handle_help(self, chat_id):
        self.handle_start(chat_id)
    
    # ===== BACKGROUND ALERT CHECKER =====
    def check_alerts_background(self):
        """Run in separate thread every 5 minutes"""
        while self.running:
            try:
                time.sleep(300)  # 5 minutes
                chat_ids = self.get_all_chat_ids()
                if not chat_ids:
                    continue
                
                conn = self.get_db()
                alerts_df = pd.read_sql_query("SELECT * FROM alerts WHERE enabled=1", conn)
                conn.close()
                
                for _, alert in alerts_df.iterrows():
                    symbol = alert['symbol']
                    threshold = alert['threshold']
                    stock_data = self.fetcher.get_stock_data(symbol, period="2d")
                    if not stock_data:
                        continue
                    
                    hist = stock_data.get('historical', pd.DataFrame())
                    if hist.empty or len(hist) < 2:
                        continue
                    
                    current = stock_data['current_price']
                    prev = hist['Close'].iloc[-2]
                    change = ((current - prev) / prev) * 100
                    
                    if abs(change) >= threshold:
                        direction = "📈 UP" if change > 0 else "📉 DOWN"
                        msg = (
                            f"🚨 <b>PRICE ALERT</b>\n"
                            f"{symbol}: ₹{current:.2f} ({change:+.2f}%) {direction}\n"
                            f"Threshold: {threshold}%"
                        )
                        for cid in chat_ids:
                            self.send_message(cid, msg)
            except Exception as e:
                print(f"Background error: {e}")
    
    # ===== MAIN POLLING LOOP =====
    def run(self):
        print("🤖 Bot started...")
        # Start background thread
        bg_thread = threading.Thread(target=self.check_alerts_background, daemon=True)
        bg_thread.start()
        
        offset = 0
        while self.running:
            try:
                updates = self.get_updates(offset)
                for update in updates:
                    offset = update['update_id'] + 1
                    if 'message' not in update:
                        continue
                    
                    msg = update['message']
                    chat_id = msg['chat']['id']
                    text = msg.get('text', '')
                    
                    if text.startswith('/start'):
                        self.handle_start(chat_id)
                    elif text.startswith('/status'):
                        self.handle_status(chat_id)
                    elif text.startswith('/alerts'):
                        self.handle_alerts(chat_id)
                    elif text.startswith('/buy'):
                        self.handle_buy(chat_id)
                    elif text.startswith('/help'):
                        self.handle_help(chat_id)
                time.sleep(1)
            except KeyboardInterrupt:
                self.running = False
                print("\nBot stopped.")
            except Exception as e:
                print(f"Polling error: {e}")
                time.sleep(5)

# ========== MAIN ==========
if __name__ == "__main__":
    bot = TelegramBot(TOKEN)
    bot.run()