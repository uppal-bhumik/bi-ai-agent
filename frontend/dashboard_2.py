import streamlit as st
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
import base64

# --- CONFIGURATION ---
st.set_page_config(
    page_title="BI-AI Agent",
    page_icon="🤖",
    layout="wide"
)

BACKEND_URL = "https://bi-ai-agent.onrender.com"


# --- STYLING ---
def load_css():
    st.markdown("""
    <style>
        /* Main App background */
        .main {
            background-color: #f5f5f5;
        }

        /* Chat bubble styles */
        .st-emotion-cache-1c7y2kd { /* AI message container */
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        /* Custom Title Styles */
        .big-title {
            font-size: 44px;
            font-weight: 800;
            background: linear-gradient(to right, #4facfe, #00f2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }
        .subtitle {
            font-size: 18px;
            font-weight: 500;
            color: #4a4a4a;
            margin-bottom: 25px;
        }
        
        /* Sidebar styling */
        .st-emotion-cache-16txtl3 {
             padding: 20px 20px 0px;
        }
        
        /* Button in sidebar */
        .stButton>button {
            width: 100%;
            background-color: #4facfe;
            color: white;
            padding: 0.5em 1em;
            border-radius: 8px;
            font-weight: bold;
            border: none;
            transition: 0.3s;
            font-size: 16px;
        }
        .stButton>button:hover {
            background-color: #00c6ff;
            transform: scale(1.02);
        }

        /* Chart type selection buttons */
        .chart-option-button {
            display: inline-block;
            margin: 5px;
            padding: 8px 16px;
            background-color: #f0f9ff;
            border: 2px solid #4facfe;
            border-radius: 8px;
            cursor: pointer;
            transition: 0.3s;
            font-weight: 500;
            text-align: center;
        }
        .chart-option-button:hover {
            background-color: #4facfe;
            color: white;
        }

        /* Chart type selection area */
        .chart-selection-area {
            background-color: #f8fafc;
            border: 2px dashed #4facfe;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            text-align: center;
        }

        /* Database config section */
        .db-config-section {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=80)
    st.title("🔍 BI-AI Agent")
    
    role = st.selectbox(
        "🧑‍💼 Select your role",
        ["Sales Employee", "Data Engineer"],
        key="role_selector"
    )
    
    st.markdown("---")
    st.markdown("Ask me anything about your sales data!")
    st.markdown("For example: `Which is the most selling product`")

    if st.button("Clear Chat History"):
        st.session_state.messages = []
        if 'awaiting_response' in st.session_state:
            del st.session_state.awaiting_response
        if 'conversation_context' in st.session_state:
            del st.session_state.conversation_context
        st.rerun()

# --- MAIN APP ---

# Title and Subheading
st.markdown('<div class="big-title">BI-AI Agent Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask questions in plain English and get data-driven insights ⚡</div>', unsafe_allow_html=True)

# Database Configuration Section
st.markdown('<div class="db-config-section">', unsafe_allow_html=True)
st.markdown("### 🗄️ Database Configuration")

# Create two columns for database config
db_col1, db_col2 = st.columns(2)

with db_col1:
    db_type = st.selectbox(
        "Database Type",
        ["MySQL", "PostgreSQL", "SQLite", "Oracle"],
        index=0,
        key="db_type"
    )
    
    host = st.text_input(
        "Host",
        value="localhost",
        placeholder="Database host address",
        key="db_host"
    )
    
    port = st.number_input(
        "Port",
        value=3306,
        min_value=1,
        max_value=65535,
        key="db_port"
    )

with db_col2:
    username = st.text_input(
        "Username",
        value="root",
        placeholder="Database username",
        key="db_username"
    )
    
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Database password",
        key="db_password"
    )
    
    database_name = st.text_input(
        "Database Name",
        value="",
        placeholder="Database name",
        key="db_name"
    )

st.markdown('</div>', unsafe_allow_html=True)

# Table Name Input Field
table_name = st.text_input(
    "📊 Enter table name:",
    value="",
    placeholder="Enter the table name to query",
    key="table_name_input"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False

if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = None

def render_message_content(content):
    """Enhanced helper function to render message content uniformly"""
    if isinstance(content, str):
        st.markdown(content)
        return
    
    # Handle simple message text
    if "message" in content:
        st.markdown(content["message"])
    
    # Handle SQL query display (if present)
    if "sql_query" in content:
        with st.expander("Show Generated SQL Query"):
            st.code(content["sql_query"], language="sql")
    
    # Handle data and charts - check for all possible combinations
    has_data = False
    has_chart = False
    
    # Check for data in various formats
    data_to_display = None
    if "result" in content and content["result"]:
        data_to_display = content["result"]
        has_data = True
    elif "data" in content and content["data"]:
        data_to_display = content["data"]
        has_data = True
    
    # Check for chart
    chart_to_display = None
    if "chart" in content and content["chart"]:
        chart_to_display = content["chart"]
        has_chart = True
    
    # Display data and chart based on what we have
    if has_data and has_chart:
        # Both data and chart - use two columns
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            st.subheader("📊 Data")
            if isinstance(data_to_display, list) and len(data_to_display) > 0:
                df = pd.DataFrame(data_to_display)
                st.dataframe(df, use_container_width=True, height=400)
            else:
                st.write("No data to display")
        
        with col2:
            st.subheader("📈 Visualization")
            try:
                img_bytes = base64.b64decode(chart_to_display)
                img = Image.open(BytesIO(img_bytes))
                st.image(img, use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying chart: {str(e)}")
    
    elif has_data and not has_chart:
        # Only data - full width
        st.subheader("📊 Results")
        if isinstance(data_to_display, list) and len(data_to_display) > 0:
            df = pd.DataFrame(data_to_display)
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.write("No data to display")
    
    elif has_chart and not has_data:
        # Only chart - full width
        st.subheader("📈 Visualization")
        try:
            img_bytes = base64.b64decode(chart_to_display)
            img = Image.open(BytesIO(img_bytes))
            st.image(img, use_container_width=True)
        except Exception as e:
            st.error(f"Error displaying chart: {str(e)}")
    
    # Handle errors
    if "error" in content:
        st.error(f"❌ {content['error']}")

def send_query_to_backend(query):
    """Send query to backend and handle response"""
    try:
        with st.spinner("🤔 Processing your question..."):
            # Create database config dictionary
            database_config = {
                "db_type": st.session_state.db_type,
                "host": st.session_state.db_host,
                "port": st.session_state.db_port,
                "username": st.session_state.db_username,
                "password": st.session_state.db_password,
                "database": st.session_state.db_name
            }
            
            payload = {
                "query": query, 
                "role": st.session_state.role_selector,
                "table_name": table_name,
                "database_config": database_config  # NEW addition
            }
            
            response = requests.post(BACKEND_URL, json=payload, timeout=50)
            response.raise_for_status()
            response_data = response.json()
            
            print(f"Backend Response: {response_data}")  # Debug logging
            
            # Check if backend is asking for chart type
            if response_data.get("awaiting_chart_type"):
                st.session_state.awaiting_response = True
                st.session_state.conversation_context = response_data
            else:
                st.session_state.awaiting_response = False
                st.session_state.conversation_context = None
            
            # Add AI response to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_data
            })
            
            return True
            
    except requests.exceptions.Timeout:
        error_msg = "Request timeout. The backend might be processing a complex query. Please try again."
        st.error(f"⏰ {error_msg}")
        st.session_state.messages.append({
            "role": "assistant", 
            "content": {"error": error_msg}
        })
        return False
        
    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to backend server. Please ensure the backend is running on http://127.0.0.1:5050"
        st.error(f"🔌 {error_msg}")
        st.session_state.messages.append({
            "role": "assistant", 
            "content": {"error": error_msg}
        })
        return False
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Backend connection error: {str(e)}"
        st.error(f"🔥 {error_msg}")
        st.session_state.messages.append({
            "role": "assistant", 
            "content": {"error": error_msg}
        })
        return False
        
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        st.error(f"💥 {error_msg}")
        st.session_state.messages.append({
            "role": "assistant", 
            "content": {"error": error_msg}
        })
        return False

def handle_chart_type_selection(chart_type):
    """Handle chart type selection and send follow-up request"""
    try:
        with st.spinner(f"🎨 Generating {chart_type} chart..."):
            # Create database config dictionary
            database_config = {
                "db_type": st.session_state.db_type,
                "host": st.session_state.db_host,
                "port": st.session_state.db_port,
                "username": st.session_state.db_username,
                "password": st.session_state.db_password,
                "database": st.session_state.db_name
            }
            
            payload = {
                "query": chart_type, 
                "role": st.session_state.role_selector,
                "table_name": table_name,
                "database_config": database_config  # NEW addition
            }
            
            response = requests.post(BACKEND_URL, json=payload, timeout=50)
            response.raise_for_status()
            response_data = response.json()
            
            # Add the AI's final chart response to the history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response_data
            })
            
            # Clear the conversation state
            st.session_state.awaiting_response = False
            st.session_state.conversation_context = None
            
            # Force the UI to refresh and display the new message
            st.rerun() 
            
    except Exception as e:
        error_msg = f"Error generating chart: {str(e)}"
        st.error(f"🎨 {error_msg}")
        st.session_state.messages.append({
            "role": "assistant", 
            "content": {"error": error_msg}
        })
        # Clear the state even if there's an error
        st.session_state.awaiting_response = False
        st.session_state.conversation_context = None
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_message_content(message["content"])

# Handle chart type selection if we're awaiting a response
if st.session_state.awaiting_response and st.session_state.conversation_context:
    st.markdown("---")
    st.markdown('<div class="chart-selection-area">', unsafe_allow_html=True)
    st.markdown("### 📊 Please select a chart type:")
    
    # First row: Basic chart types
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🥧 Pie Chart", key="pie_button", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "pie"})
            handle_chart_type_selection("pie")
            st.rerun()

    with col2:
        if st.button("🍩 Donut Chart", key="donut_button", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "donut"})
            handle_chart_type_selection("donut")
            st.rerun()

    with col3:
        if st.button("📊 Bar Chart", key="bar_button", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "bar"})
            handle_chart_type_selection("bar")
            st.rerun()

    # Second row: Advanced chart types
    col4, col5, col6 = st.columns(3)
    
    with col4:
        if st.button("📈 Line Chart", key="line_button", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "line"})
            handle_chart_type_selection("line")
            st.rerun()

    with col5:
        if st.button("🏛️ Column Chart", key="column_button", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "column"})
            handle_chart_type_selection("column")
            st.rerun()

    with col6:
        if st.button("🌄 Area Chart", key="area_button", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "area"})
            handle_chart_type_selection("area")
            st.rerun()
    
    # Third row: Special area chart variants (if needed)
    st.markdown("#### 🔄 Advanced Area Charts:")
    col7, col8, col9 = st.columns(3)
    
    with col7:
        if st.button("📊 Stacked Area", key="stacked_area_button", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "stacked area"})
            handle_chart_type_selection("stacked_area")
            st.rerun()

    with col8:
        if st.button("📈 Percentage Area", key="percentage_area_button", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "percentage area"})
            handle_chart_type_selection("percentage_area")
            st.rerun()

    with col9:
        # Empty column or add another chart type if needed
        pass
    
    st.markdown('</div>', unsafe_allow_html=True)

# Handle regular chat input (only if not awaiting chart type selection)
if not st.session_state.awaiting_response:
    if prompt := st.chat_input("What would you like to know about your sales data?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Send query to backend
        success = send_query_to_backend(prompt)
        
        # Rerun to update the interface
        if success:
            st.rerun()

# Display helpful message if awaiting response
if st.session_state.awaiting_response:
    st.info("👆 Please select a chart type above to continue with your visualization.")

# Add some helpful examples at the bottom if no messages exist
if not st.session_state.messages:
    st.markdown("---")
    st.markdown("### 💡 Try asking questions like:")
    
    example_col1, example_col2 = st.columns(2)
    
    with example_col1:
        st.markdown("""
        **📈 Sales & Revenue:**
        - "What's our total revenue this year?"
        - "Show me sales by product category"
        - "Which region has the highest sales?"
        - "Show me a donut chart of revenue by region"
        """)
        
    with example_col2:
        st.markdown("""
        **📊 Product Analysis:**
        - "Most selling product last quarter"
        - "Show me a column chart of product performance"  
        - "Average order value by customer"
        - "Line chart of monthly sales trend"
        """)
