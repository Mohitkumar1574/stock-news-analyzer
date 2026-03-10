import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os
import numpy as np
from sklearn.linear_model import LinearRegression

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.scrapers.stock_data_fetcher import StockDataFetcher
from src.utils.database import Database
from src.utils.helpers import setup_logger

logger = setup_logger(__name__)

def show_portfolio():
    # Page header with fade-in animation
    st.markdown("""
    <div class="fade-in">
        <h2 style="color: #333; margin-bottom: 1.5rem;">📁 Portfolio Tracker</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database and fetcher
    db = Database()
    fetcher = StockDataFetcher()
    
    # Create tabs (5 tabs)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Portfolio Overview", 
        "🔔 Price Alerts", 
        "📈 Performance Analytics",
        "💰 Dividend Tracker",
        "📝 Paper Trading"
    ])
    
    # ==================== TAB 1: PORTFOLIO OVERVIEW ====================
    with tab1:
        st.markdown("### Your Portfolio")
        
        # Add stock section
        with st.expander("➕ Add Stock to Portfolio", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                new_symbol = st.text_input("Stock Symbol", "RELIANCE.NS", key="add_symbol").upper()
            with col2:
                new_quantity = st.number_input("Quantity", min_value=1, value=10, step=1, key="add_qty")
            with col3:
                new_buy_price = st.number_input("Buy Price (₹)", min_value=0.0, value=2500.0, step=10.0, key="add_price")
            with col4:
                new_buy_date = st.date_input("Purchase Date", datetime.now(), key="add_date")
            
            notes = st.text_input("Notes (optional)", key="add_notes")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add to Portfolio", type="primary", use_container_width=True):
                    db.add_portfolio_item(
                        symbol=new_symbol,
                        quantity=new_quantity,
                        buy_price=new_buy_price,
                        buy_date=new_buy_date.strftime("%Y-%m-%d"),
                        notes=notes
                    )
                    st.success(f"✅ Added {new_symbol} to portfolio!")
                    st.rerun()
            with col2:
                if st.button("🔄 Refresh Prices", use_container_width=True):
                    st.rerun()
        
        # Load portfolio from database
        portfolio_df = db.get_all_portfolio()
        
        if not portfolio_df.empty:
            # Fetch current prices for all stocks
            portfolio_data = []
            total_investment = 0
            total_current = 0
            total_dividends = 0
            stock_details = {}
            
            for _, item in portfolio_df.iterrows():
                stock_data = fetcher.get_stock_data(item['symbol'], period="1mo")
                if stock_data:
                    current_price = stock_data['current_price']
                    hist = stock_data.get('historical', pd.DataFrame())
                    
                    investment = item['quantity'] * item['buy_price']
                    current_value = item['quantity'] * current_price
                    profit_loss = current_value - investment
                    profit_loss_pct = (profit_loss / investment) * 100 if investment > 0 else 0
                    
                    if not hist.empty and len(hist) >= 2:
                        prev_close = hist['Close'].iloc[-2]
                        day_change_pct = ((current_price - prev_close) / prev_close) * 100
                    else:
                        day_change_pct = 0
                    
                    alerts_df = db.get_alerts(item['symbol'])
                    alert_enabled = not alerts_df.empty and alerts_df.iloc[0]['enabled'] == 1
                    alert_threshold = alerts_df.iloc[0]['threshold'] if not alerts_df.empty else 5.0
                    
                    if alert_enabled and abs(day_change_pct) >= alert_threshold:
                        alert_msg = f"⚠️ {item['symbol']} moved {day_change_pct:.1f}% (threshold: {alert_threshold}%)"
                        db.add_alert_history(item['symbol'], alert_msg, day_change_pct)
                    
                    div_df = db.get_dividends(item['symbol'])
                    total_dividend = div_df['total_amount'].sum() if not div_df.empty else 0
                    total_dividends += total_dividend
                    
                    total_investment += investment
                    total_current += current_value
                    
                    stock_details[item['symbol']] = {
                        'current_price': current_price,
                        'hist': hist,
                        'quantity': item['quantity']
                    }
                    
                    portfolio_data.append({
                        'ID': item['id'],
                        'Symbol': item['symbol'],
                        'Quantity': item['quantity'],
                        'Buy Price (₹)': item['buy_price'],
                        'Current Price (₹)': round(current_price, 2),
                        'Day Change %': round(day_change_pct, 2),
                        'Investment (₹)': round(investment, 2),
                        'Current Value (₹)': round(current_value, 2),
                        'P/L (₹)': round(profit_loss, 2),
                        'P/L (%)': round(profit_loss_pct, 2),
                        'Dividends (₹)': round(total_dividend, 2),
                        'Alert': '🔔 ON' if alert_enabled else '🔕 OFF',
                        'Threshold %': alert_threshold
                    })
            
            # ----- Summary Cards -----
            st.markdown("### Portfolio Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">Total Investment</div>
                    <div class="card-value">₹{total_investment:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">Current Value</div>
                    <div class="card-value">₹{total_current:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                total_pl = total_current - total_investment
                total_pl_pct = (total_pl / total_investment) * 100 if total_investment > 0 else 0
                delta_color = "green" if total_pl >= 0 else "red"
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">Total P/L</div>
                    <div class="card-value" style="color: {delta_color};">₹{total_pl:+,.0f}</div>
                    <div class="card-delta" style="color: {delta_color};">{total_pl_pct:+.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">Dividends</div>
                    <div class="card-value">₹{total_dividends:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # ----- Holdings Table -----
            st.markdown("### Holdings")
            df_display = pd.DataFrame(portfolio_data)
            
            def color_pl(val):
                if isinstance(val, (int, float)):
                    if val > 0:
                        return 'color: green'
                    elif val < 0:
                        return 'color: red'
                return ''
            
            styled_df = df_display.style.map(color_pl, subset=['P/L (₹)', 'P/L (%)', 'Day Change %'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # ----- Charts -----
            col1, col2 = st.columns(2)
            with col1:
                if not df_display.empty and df_display['Current Value (₹)'].sum() > 0:
                    fig = go.Figure(data=[go.Pie(
                        labels=df_display['Symbol'],
                        values=df_display['Current Value (₹)'],
                        hole=0.4,
                        textinfo='label+percent',
                        marker_colors=px.colors.qualitative.Set3
                    )])
                    fig.update_layout(title="Portfolio Distribution", height=400)
                    st.plotly_chart(fig, use_container_width=True)
            with col2:
                if not df_display.empty:
                    colors = ['green' if x > 0 else 'red' for x in df_display['P/L (₹)']]
                    fig = go.Figure(data=[go.Bar(
                        x=df_display['Symbol'],
                        y=df_display['P/L (₹)'],
                        marker_color=colors,
                        text=df_display['P/L (₹)'].apply(lambda x: f'₹{x:,.0f}'),
                        textposition='outside'
                    )])
                    fig.update_layout(title="Profit/Loss by Stock", height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            # ----- Future Projection -----
            st.markdown("### 🔮 Future Value Projection")
            col1, col2, col3 = st.columns(3)
            with col1:
                projection_amount = st.number_input("Investment Amount (₹)", min_value=100, value=1000, step=100, key="proj_amount")
            with col2:
                projection_days = st.number_input("Days in Future", min_value=1, max_value=365, value=20, step=1, key="proj_days")
            with col3:
                projection_method = st.selectbox("Projection Method", ["Average Daily Return", "Linear Regression"], key="proj_method")
            
            if st.button("Calculate Projection", key="calc_proj"):
                projection_results = []
                total_projected = 0
                for symbol, details in stock_details.items():
                    hist = details['hist']
                    if hist.empty or len(hist) < 5:
                        st.warning(f"Not enough historical data for {symbol}")
                        continue
                    current_price = details['current_price']
                    daily_returns = hist['Close'].pct_change().dropna()
                    
                    if projection_method == "Average Daily Return":
                        avg_daily_return = daily_returns.mean()
                        projected_price = current_price * ((1 + avg_daily_return) ** projection_days)
                        shares_bought = projection_amount / current_price
                        projected_value = shares_bought * projected_price
                    else:
                        recent = hist.tail(30)
                        X = np.arange(len(recent)).reshape(-1,1)
                        y = recent['Close'].values
                        model = LinearRegression().fit(X, y)
                        future_X = np.arange(len(recent), len(recent) + projection_days).reshape(-1,1)
                        projected_price = model.predict(future_X)[-1]
                        shares_bought = projection_amount / current_price
                        projected_value = shares_bought * projected_price
                    
                    projected_value = max(0, projected_value)
                    total_projected += projected_value
                    expected_return = ((projected_value - projection_amount) / projection_amount) * 100
                    
                    projection_results.append({
                        'Symbol': symbol,
                        'Current Price': f"₹{current_price:,.2f}",
                        'Projected Price': f"₹{projected_price:,.2f}",
                        f'Projected Value (₹{projection_amount})': f"₹{projected_value:,.2f}",
                        'Expected Return': f"{expected_return:.1f}%"
                    })
                
                if projection_results:
                    proj_df = pd.DataFrame(projection_results)
                    st.dataframe(proj_df, use_container_width=True, hide_index=True)
                    
                    st.metric(
                        "Total Projected Value",
                        f"₹{total_projected:,.2f}",
                        delta=f"{((total_projected - projection_amount*len(projection_results)) / (projection_amount*len(projection_results)) * 100):.1f}%"
                    )
                    
                    value_col = f'Projected Value (₹{projection_amount})'
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=[r['Symbol'] for r in projection_results],
                        y=[float(r[value_col].replace('₹','').replace(',','')) for r in projection_results],
                        name='Projected Value',
                        marker_color='blue'
                    ))
                    fig.add_hline(y=projection_amount, line_dash="dash", line_color="green", annotation_text="Initial Investment")
                    fig.update_layout(
                        title=f"Projected Value after {projection_days} days",
                        xaxis_title="Stock",
                        yaxis_title="Value (₹)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # ----- Management -----
            with st.expander("⚙️ Portfolio Management"):
                col1, col2 = st.columns(2)
                with col1:
                    symbols = df_display['Symbol'].tolist()
                    if symbols:
                        remove_symbol = st.selectbox("Select stock to remove", symbols, key="remove_symbol")
                        if st.button("🗑️ Remove Selected", use_container_width=True):
                            item_id = df_display[df_display['Symbol'] == remove_symbol]['ID'].values[0]
                            db.delete_portfolio_item(item_id)
                            st.success(f"Removed {remove_symbol}")
                            st.rerun()
                with col2:
                    if st.button("🗑️ Clear All Portfolio", use_container_width=True):
                        db.delete_all_portfolio()
                        st.success("All portfolio data cleared")
                        st.rerun()
        else:
            st.info("📌 Your portfolio is empty. Add some stocks to get started!")
    
    # ==================== TAB 2: PRICE ALERTS ====================
    with tab2:
        st.markdown("### 🔔 Price Alerts")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### Set New Alert")
            portfolio_df = db.get_all_portfolio()
            if not portfolio_df.empty:
                symbols = portfolio_df['symbol'].tolist()
                alert_symbol = st.selectbox("Select Stock", symbols, key="alert_symbol")
                
                alerts_df = db.get_alerts(alert_symbol)
                current_threshold = alerts_df.iloc[0]['threshold'] if not alerts_df.empty else 5.0
                current_enabled = alerts_df.iloc[0]['enabled'] == 1 if not alerts_df.empty else False
                
                col_a, col_b = st.columns(2)
                with col_a:
                    enabled = st.checkbox("Enable Alert", value=current_enabled, key="alert_enabled")
                with col_b:
                    threshold = st.number_input("Alert Threshold (%)", 1.0, 20.0, value=current_threshold, step=0.5, key="alert_threshold")
                
                if st.button("Save Alert Settings", type="primary"):
                    db.set_alert(alert_symbol, threshold, 1 if enabled else 0)
                    st.success("Alert settings saved!")
                    st.rerun()
            else:
                st.warning("Add stocks to portfolio first.")
        
        with col2:
            st.markdown("#### Active Alerts")
            alerts_df = db.get_alerts()
            active = alerts_df[alerts_df['enabled'] == 1]
            for _, row in active.iterrows():
                st.write(f"- {row['symbol']}: {row['threshold']}%")
        
        st.markdown("#### Alert History")
        history_df = db.get_alert_history(limit=50)
        if not history_df.empty:
            st.dataframe(history_df[['triggered_at', 'symbol', 'message']], use_container_width=True, hide_index=True)
            if st.button("Clear History"):
                conn = db.get_connection()
                conn.execute("DELETE FROM alert_history")
                conn.commit()
                conn.close()
                st.rerun()
        else:
            st.info("No alerts triggered yet.")
    
    # ==================== TAB 3: PERFORMANCE ANALYTICS ====================
    with tab3:
        st.markdown("### 📈 Performance Analytics")
        portfolio_df = db.get_all_portfolio()
        if not portfolio_df.empty:
            period = st.selectbox(
                "Select Time Period",
                ["1 Week", "1 Month", "3 Months", "6 Months", "1 Year", "YTD", "All Time"],
                index=1,
                key="perf_period"
            )
            
            period_days = {
                "1 Week": 7,
                "1 Month": 30,
                "3 Months": 90,
                "6 Months": 180,
                "1 Year": 365,
                "YTD": (datetime.now() - datetime(datetime.now().year, 1, 1)).days,
                "All Time": 9999
            }
            days = period_days[period]
            
            all_hist = {}
            for _, item in portfolio_df.iterrows():
                hist = fetcher.get_historical_data(
                    item['symbol'],
                    start_date=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                    end_date=datetime.now().strftime('%Y-%m-%d')
                )
                if not hist.empty:
                    all_hist[item['symbol']] = hist
            
            if all_hist:
                fig = go.Figure()
                for symbol, hist in all_hist.items():
                    start = hist['Close'].iloc[0]
                    norm = (hist['Close'] / start - 1) * 100
                    fig.add_trace(go.Scatter(x=hist.index, y=norm, mode='lines', name=symbol))
                
                try:
                    nifty = fetcher.get_historical_data(
                        '^NSEI',
                        start_date=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                        end_date=datetime.now().strftime('%Y-%m-%d')
                    )
                    if not nifty.empty:
                        nifty_norm = (nifty['Close'] / nifty['Close'].iloc[0] - 1) * 100
                        fig.add_trace(go.Scatter(
                            x=nifty.index, y=nifty_norm, mode='lines', name='Nifty 50',
                            line=dict(color='black', dash='dash')
                        ))
                except:
                    pass
                
                fig.update_layout(
                    title=f"Performance ({period}) - Normalized Returns",
                    xaxis_title="Date",
                    yaxis_title="Return (%)",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Metrics table
                st.markdown("#### Performance Metrics")
                metrics = []
                for _, item in portfolio_df.iterrows():
                    if item['symbol'] in all_hist:
                        hist = all_hist[item['symbol']]
                        start = hist['Close'].iloc[0]
                        end = hist['Close'].iloc[-1]
                        total_return = ((end - item['buy_price']) / item['buy_price']) * 100
                        period_return = ((end - start) / start) * 100
                        daily_ret = hist['Close'].pct_change().dropna()
                        volatility = daily_ret.std() * (252**0.5) * 100
                        sharpe = (period_return - 6) / volatility if volatility > 0 else 0
                        max_dd = (hist['Close'].min() / hist['Close'].max() - 1) * 100
                        
                        metrics.append({
                            'Symbol': item['symbol'],
                            'Total Return %': round(total_return, 2),
                            f'{period} Return %': round(period_return, 2),
                            'Volatility %': round(volatility, 2),
                            'Sharpe Ratio': round(sharpe, 2),
                            'Max DD %': round(max_dd, 2)
                        })
                
                if metrics:
                    st.dataframe(pd.DataFrame(metrics), use_container_width=True, hide_index=True)
        else:
            st.info("Add stocks to portfolio to view performance analytics.")
    
    # ==================== TAB 4: DIVIDEND TRACKER ====================
    with tab4:
        st.markdown("### 💰 Dividend Tracker")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Add Dividend")
            portfolio_df = db.get_all_portfolio()
            if not portfolio_df.empty:
                symbols = portfolio_df['symbol'].tolist()
                div_symbol = st.selectbox("Select Stock", symbols, key="div_symbol")
                
                qty = portfolio_df[portfolio_df['symbol'] == div_symbol]['quantity'].values[0]
                amount_per_share = st.number_input("Dividend per Share (₹)", min_value=0.0, value=10.0, step=1.0, key="div_amt")
                div_date = st.date_input("Payment Date", datetime.now(), key="div_date")
                div_type = st.selectbox("Dividend Type", ["Interim", "Final", "Special"], key="div_type")
                notes = st.text_input("Notes", key="div_notes")
                
                total_amount = amount_per_share * qty
                st.write(f"**Total Amount:** ₹{total_amount:,.2f}")
                
                if st.button("➕ Record Dividend", type="primary"):
                    db.add_dividend(
                        symbol=div_symbol,
                        amount_per_share=amount_per_share,
                        total_amount=total_amount,
                        dividend_date=div_date.strftime("%Y-%m-%d"),
                        dividend_type=div_type,
                        notes=notes
                    )
                    st.success("Dividend recorded!")
                    st.rerun()
            else:
                st.warning("Add stocks to portfolio first.")
        
        with col2:
            st.markdown("#### Dividend Summary")
            div_df = db.get_dividends()
            if not div_df.empty:
                total_div = div_df['total_amount'].sum()
                st.metric("Total Dividends Received", f"₹{total_div:,.2f}")
                st.markdown("**By Stock:**")
                by_stock = div_df.groupby('symbol')['total_amount'].sum().reset_index()
                for _, row in by_stock.iterrows():
                    st.write(f"- {row['symbol']}: ₹{row['total_amount']:,.2f}")
            else:
                st.info("No dividends recorded yet.")
        
        div_df = db.get_dividends()
        if not div_df.empty:
            st.markdown("#### Dividend History")
            st.dataframe(
                div_df[['dividend_date', 'symbol', 'amount_per_share', 'total_amount', 'dividend_type', 'notes']],
                use_container_width=True,
                hide_index=True
            )
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=div_df['dividend_date'],
                y=div_df['total_amount'],
                marker_color='green',
                text=div_df['total_amount'].apply(lambda x: f'₹{x:,.0f}'),
                textposition='outside'
            ))
            fig.update_layout(title="Dividend Timeline", height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            if st.button("Clear All Dividends"):
                conn = db.get_connection()
                conn.execute("DELETE FROM dividends")
                conn.commit()
                conn.close()
                st.rerun()
    
    # ==================== TAB 5: PAPER TRADING ====================
    with tab5:
        st.markdown("### 📝 Paper Trading (Virtual Money)")
        st.markdown("Trade with virtual money – practice without risk!")
        
        user_id = 'default'
        cash_balance, initial_balance = db.get_paper_balance(user_id)
        holdings_df = db.get_paper_holdings(user_id)
        
        holdings_value = 0
        for _, row in holdings_df.iterrows():
            stock_data = fetcher.get_stock_data(row['symbol'], period="1d")
            if stock_data:
                holdings_value += row['quantity'] * stock_data['current_price']
        
        total_value = cash_balance + holdings_value
        total_pl = total_value - initial_balance
        total_pl_pct = (total_pl / initial_balance) * 100
        
        # Metrics cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">Cash Balance</div>
                <div class="card-value">₹{cash_balance:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">Holdings Value</div>
                <div class="card-value">₹{holdings_value:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            color = "green" if total_pl >= 0 else "red"
            st.markdown(f"""
            <div class="card">
                <div class="card-title">Total P/L</div>
                <div class="card-value" style="color: {color};">₹{total_pl:+,.0f}</div>
                <div class="card-delta" style="color: {color};">{total_pl_pct:+.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        with st.expander("🛒 Place Order", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                symbol = st.text_input("Symbol", "RELIANCE.NS", key="paper_symbol").upper()
            with col2:
                action = st.selectbox("Action", ["BUY", "SELL"], key="paper_action")
            with col3:
                quantity = st.number_input("Quantity", min_value=1, value=1, step=1, key="paper_qty")
            
            stock_data = fetcher.get_stock_data(symbol, period="1d")
            if stock_data:
                current_price = stock_data['current_price']
                st.write(f"**Current Price:** ₹{current_price:.2f}")
                total_cost = current_price * quantity
                st.write(f"**Total:** ₹{total_cost:,.2f}")
                
                if st.button("Place Order", type="primary"):
                    if action == "BUY":
                        if cash_balance >= total_cost:
                            db.update_paper_balance(user_id, cash_balance - total_cost)
                            db.update_paper_holdings(user_id, symbol, quantity, current_price, is_buy=True)
                            db.add_paper_transaction(user_id, symbol, 'BUY', quantity, current_price, total_cost)
                            st.success("✅ Bought!")
                            st.rerun()
                        else:
                            st.error("❌ Insufficient balance!")
                    else:  # SELL
                        holding = holdings_df[holdings_df['symbol'] == symbol]
                        if not holding.empty and holding.iloc[0]['quantity'] >= quantity:
                            db.update_paper_balance(user_id, cash_balance + total_cost)
                            db.update_paper_holdings(user_id, symbol, quantity, current_price, is_buy=False)
                            db.add_paper_transaction(user_id, symbol, 'SELL', quantity, current_price, total_cost)
                            st.success("✅ Sold!")
                            st.rerun()
                        else:
                            st.error("❌ Not enough shares!")
            else:
                st.warning("Symbol not found.")
        
        st.markdown("#### Current Holdings")
        if not holdings_df.empty:
            holdings_list = []
            for _, row in holdings_df.iterrows():
                stock_data = fetcher.get_stock_data(row['symbol'], period="1d")
                if stock_data:
                    cp = stock_data['current_price']
                    inv = row['quantity'] * row['buy_price']
                    cv = row['quantity'] * cp
                    pl = cv - inv
                    pl_pct = (pl / inv) * 100 if inv else 0
                    holdings_list.append({
                        'Symbol': row['symbol'],
                        'Qty': row['quantity'],
                        'Avg Buy': f"₹{row['buy_price']:.2f}",
                        'Current': f"₹{cp:.2f}",
                        'Investment': f"₹{inv:,.0f}",
                        'Current Value': f"₹{cv:,.0f}",
                        'P/L': f"₹{pl:+,.0f}",
                        'P/L %': f"{pl_pct:+.1f}%"
                    })
            st.dataframe(pd.DataFrame(holdings_list), use_container_width=True, hide_index=True)
        else:
            st.info("No holdings yet. Buy some stocks to start paper trading!")
        
        st.markdown("#### Transaction History")
        conn = db.get_connection()
        txn_df = pd.read_sql_query("SELECT * FROM paper_transactions WHERE user_id = ? ORDER BY transaction_date DESC LIMIT 20", conn, params=(user_id,))
        conn.close()
        if not txn_df.empty:
            txn_df['transaction_date'] = pd.to_datetime(txn_df['transaction_date']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(txn_df[['transaction_date', 'symbol', 'transaction_type', 'quantity', 'price', 'total']],
                         use_container_width=True, hide_index=True)
        else:
            st.info("No transactions yet.")
        
        if st.button("🔄 Reset Paper Trading (Start Over)"):
            conn = db.get_connection()
            conn.execute("DELETE FROM paper_portfolio WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM paper_transactions WHERE user_id = ?", (user_id,))
            conn.execute("UPDATE paper_balance SET cash_balance = ?, initial_balance = ?, updated_at = ? WHERE user_id = ?",
                         (100000.0, 100000.0, datetime.now().isoformat(), user_id))
            conn.commit()
            conn.close()
            st.success("Paper trading reset to ₹1,00,000!")
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.caption(f"Data stored in SQLite database: `{db.db_path}`")

if __name__ == "__main__":
    show_portfolio()

    