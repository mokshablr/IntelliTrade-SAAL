import streamlit as st
import random
import time
import requests
import os
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
llm_api_endpoint = os.getenv("LLM_API_ENDPOINT")

# Page configuration
st.set_page_config(page_title="IntelliTrade", page_icon="📈", layout="wide")

st.title("📈 IntelliTrade")
st.caption("Your comprehensive trading platform for learning and strategy testing")

# Create tabs
tab1, tab2 = st.tabs(["🎓 Learning", "🧪 Strategy Testing"])

# Tab 1: Learning (Chatbot)
with tab1:
    st.header("Trading Learning Assistant")
    st.write("Use this chatbot to learn about trading and get assistance with your trading questions.")
    
    # Initialize chat history for learning tab
    if "learning_messages" not in st.session_state:
        st.session_state.learning_messages = [{"role": "assistant", "content": "Let's start learning about trading! 👇"}]
    
    # Initialize streaming state
    if "is_streaming" not in st.session_state:
        st.session_state.is_streaming = False
        st.session_state.full_response_text = "" # Store the full response from LLM
        st.session_state.current_display_length = 0 # How much of the full response to display
    
    # Create a container with fixed height to prevent layout shifts
    chat_container = st.container(height=500)
    
    with chat_container:
        # Display chat messages from history on app rerun
        for message in st.session_state.learning_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Show streaming message if currently streaming
        if st.session_state.is_streaming:
            with st.chat_message("assistant"):
                # Display a progressively longer substring of the full response
                display_content = st.session_state.full_response_text[:st.session_state.current_display_length]
                st.markdown(display_content + "▌") # Add the typing indicator
            
            # Increment the display length
            if st.session_state.current_display_length < len(st.session_state.full_response_text):
                # Adjust sleep time to control typing speed
                time.sleep(0.005) # Slower for better readability
                st.session_state.current_display_length += 1 # Reveal one character at a time
                st.rerun()
            else:
                # Streaming finished
                st.session_state.learning_messages.append({"role": "assistant", "content": st.session_state.full_response_text})
                st.session_state.is_streaming = False
                st.session_state.full_response_text = ""
                st.session_state.current_display_length = 0
                st.rerun()
    
    # Accept user input - this stays outside the container so it's always at bottom
    if prompt := st.chat_input("Ask me anything about trading..."):
        # Only process if not currently streaming
        if not st.session_state.is_streaming:
            # Add user message to chat history
            st.session_state.learning_messages.append({"role": "user", "content": prompt})
            
            # Get LLM response
            payload = {
                "user_input": prompt
            }
            try: 
                if llm_api_endpoint == None or llm_api_endpoint == "":
                    assistant_response = "This chatbot is not connected to an LLM."
                else:
                    response = requests.post(llm_api_endpoint, json=payload)
                    data = response.json()
                
                    if "message" in data:
                        assistant_response = data["message"]
                    elif "error" in data:
                        assistant_response = f"Error from LLM: {data['error']}"
                    else:
                        assistant_response = "Unexpected response format."
            except requests.exceptions.RequestException as e:
                assistant_response = f"❌ Failed to reach the server: {str(e)}"
            except ValueError:
                assistant_response = "❌ Received non-JSON response from LLM."
            
            # Start streaming
            st.session_state.is_streaming = True
            st.session_state.full_response_text = assistant_response
            st.session_state.current_display_length = 0
            st.rerun()

# # Tab 2: Strategy Testing
with tab2:
    st.header("Strategy Testing")
    st.write("Upload and test your trading strategies using JSON configuration files.")
    
    # Create columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📁 Strategy Configuration")
        
        # File uploader for JSON
        uploaded_file = st.file_uploader(
            "Upload Strategy JSON", 
            type=['json'],
            help="Upload a JSON file containing your trading strategy configuration"
        )
        
        # Manual JSON input
        st.subheader("✏️ Manual JSON Input")
        json_input = st.text_area(
            "Or paste your JSON strategy here:",
            height=200,
            placeholder="""{
  "strategy_name": "Example Strategy",
  "parameters": {
    "entry_signal": "RSI < 30",
    "exit_signal": "RSI > 70",
    "stop_loss": 0.05,
    "take_profit": 0.10
  },
  "timeframe": "1h",
  "instruments": ["EURUSD", "GBPUSD"]
}"""
        )
        
        # Sample strategy templates
        st.subheader("📋 Sample Templates")
        template_options = {
            "RSI Strategy": {
                "strategy_name": "RSI Reversal Strategy",
                "parameters": {
                    "entry_signal": "RSI < 30",
                    "exit_signal": "RSI > 70",
                    "stop_loss": 0.05,
                    "take_profit": 0.10,
                    "position_size": 0.01
                },
                "timeframe": "1h",
                "instruments": ["EURUSD", "GBPUSD", "USDJPY"]
            },
            "Moving Average Crossover": {
                "strategy_name": "MA Crossover Strategy",
                "parameters": {
                    "fast_ma": 20,
                    "slow_ma": 50,
                    "entry_signal": "fast_ma crosses above slow_ma",
                    "exit_signal": "fast_ma crosses below slow_ma",
                    "stop_loss": 0.03,
                    "take_profit": 0.08
                },
                "timeframe": "4h",
                "instruments": ["BTCUSD", "ETHUSD"]
            }
        }
        
        selected_template = st.selectbox("Choose a template:", ["None"] + list(template_options.keys()))
        
        if selected_template != "None":
            if st.button("Load Template"):
                st.session_state.strategy_json = json.dumps(template_options[selected_template], indent=2)
                st.rerun()
    
    with col2:
        st.subheader("🔍 Strategy Analysis")
        
        # Initialize strategy_json in session state
        if "strategy_json" not in st.session_state:
            st.session_state.strategy_json = ""
        
        # Process uploaded file
        strategy_data = None
        if uploaded_file is not None:
            try:
                strategy_data = json.load(uploaded_file)
                st.success("✅ JSON file loaded successfully!")
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON format: {str(e)}")
        
        # Process manual JSON input
        elif json_input.strip():
            try:
                strategy_data = json.loads(json_input)
                st.success("✅ JSON parsed successfully!")
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON format: {str(e)}")
        
        # Process template JSON
        elif hasattr(st.session_state, 'strategy_json') and st.session_state.strategy_json:
            try:
                strategy_data = json.loads(st.session_state.strategy_json)
                st.text_area("Loaded Template:", value=st.session_state.strategy_json, height=200, disabled=True)
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON format: {str(e)}")
        
        # Display strategy analysis
        if strategy_data:
            st.subheader("📊 Strategy Overview")
            
            # Basic info
            if "strategy_name" in strategy_data:
                st.metric("Strategy Name", strategy_data["strategy_name"])
            
            if "timeframe" in strategy_data:
                st.metric("Timeframe", strategy_data["timeframe"])
            
            # Parameters
            if "parameters" in strategy_data:
                st.subheader("⚙️ Parameters")
                params_df = pd.DataFrame(list(strategy_data["parameters"].items()), 
                                       columns=["Parameter", "Value"])
                st.dataframe(params_df, use_container_width=True)
            
            # Instruments
            if "instruments" in strategy_data:
                st.subheader("📈 Trading Instruments")
                instruments = strategy_data["instruments"]
                st.write(", ".join(instruments) if isinstance(instruments, list) else str(instruments))
            
            # Backtesting section
            st.subheader("🔬 Backtesting")
            
            backtest_col1, backtest_col2 = st.columns(2)
            
            with backtest_col1:
                start_date = st.date_input("Start Date")
                capital = st.number_input("Initial Capital ($)", value=10000, min_value=100)
            
            with backtest_col2:
                end_date = st.date_input("End Date")
                risk_per_trade = st.slider("Risk per Trade (%)", 1, 10, 2)
            
            if st.button("🚀 Run Backtest", type="primary"):
                with st.spinner("Running backtest..."):
                    # Simulate backtesting process
                    progress_bar = st.progress(0)
                    for i in range(100):
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    # Generate mock results
                    total_return = random.uniform(-20, 50)
                    win_rate = random.uniform(40, 80)
                    max_drawdown = random.uniform(5, 25)
                    sharpe_ratio = random.uniform(0.5, 2.5)
                    
                    st.success("✅ Backtest completed!")
                    
                    # Display results
                    result_col1, result_col2, result_col3, result_col4 = st.columns(4)
                    
                    with result_col1:
                        st.metric("Total Return", f"{total_return:.2f}%", 
                                delta=f"{total_return:.2f}%")
                    
                    with result_col2:
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    
                    with result_col3:
                        st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
                    
                    with result_col4:
                        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
        
        else:
            st.info("👆 Upload a JSON file or paste JSON content to analyze your strategy")
            
            # Show JSON format example
            with st.expander("📖 JSON Format Guide"):
                st.markdown("""
                **Required Fields:**
                - `strategy_name`: Name of your strategy
                - `parameters`: Object containing strategy parameters
                - `timeframe`: Trading timeframe (e.g., "1h", "4h", "1d")
                - `instruments`: Array of trading instruments
                
                **Example Structure:**
                ```json
                {
                    "strategy_name": "Your Strategy Name",
                    "parameters": {
                        "entry_signal": "Entry condition",
                        "exit_signal": "Exit condition",
                        "stop_loss": 0.05,
                        "take_profit": 0.10
                    },
                    "timeframe": "1h",
                    "instruments": ["EURUSD", "GBPUSD"]
                }
                ```
                """)

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
