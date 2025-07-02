import streamlit as st
import os
from dotenv import load_dotenv

import assistant
import strategy
import auto_test
import chart

load_dotenv()
llm_api_endpoint = os.getenv("LLM_API_ENDPOINT")

# Page configuration
st.set_page_config(page_title="IntelliTrade", page_icon="📈", layout="wide")

st.title("📈 IntelliTrade")
st.caption("Your comprehensive trading platform for learning and strategy testing")

# Sidebar with additional info
with st.sidebar:
    st.header("ℹ️ About IntelliTrade")
    st.markdown("""
    **Learning Tab:** 
    Chat with our AI assistant to learn about trading concepts, strategies, and market analysis.
    
    **Strategy Testing Tab:**
    Upload JSON files or paste JSON configurations to test and analyze your trading strategies.
    """)
    
    st.header("🔧 Settings")
    if llm_api_endpoint:
        st.success("✅ LLM API Connected")
    else:
        st.warning("⚠️ LLM API Not Connected")
        st.caption("Set LLM_API_ENDPOINT in your environment variables")
    
    # st.header("📚 Resources")
    # st.markdown("""
    # - [Trading Basics](https://example.com)
    # - [Strategy Development](https://example.com)
    # - [Risk Management](https://example.com)
    # - [Technical Analysis](https://example.com)
    # """)

chart.render()

# Create tabs
tab1, tab2, tab3 = st.tabs(["🎓 Learning", "🧪📊 Grid Search Strategy", "🧪 Custom Strategy Testing"])

# Tab 1: Learning (Chatbot)
with tab1:
    assistant.render()

# # Tab 2: Grid Search Strategy Testing
with tab2:
    auto_test.render()

# # Tab 3: Custom Strategy Testing
with tab3:
    strategy.render()

