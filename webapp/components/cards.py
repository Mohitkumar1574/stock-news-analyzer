import streamlit as st

def metric_card(title, value, delta=None, delta_color="normal"):
    """Custom metric card"""
    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)

def recommendation_card(recommendation, confidence):
    """Display recommendation with color"""
    if recommendation == "BUY":
        st.success(f"✅ **BUY** with {confidence:.1f}% confidence")
    elif recommendation == "DON'T BUY":
        st.error(f"❌ **DON'T BUY** with {confidence:.1f}% confidence")
    else:
        st.warning(f"⚠️ **HOLD** - Market sentiment is neutral")