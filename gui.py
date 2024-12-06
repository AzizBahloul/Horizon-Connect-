# gui.py
import streamlit as st
import requests
import plotly.graph_objects as go
import json
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="La Nuit de l'Info Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stTextInput>div>div>input {
        border-radius: 20px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e6f3ff;
    }
    .bot-message {
        background-color: #f0f2f6;
    }
    .evaluation-metric {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'evaluations' not in st.session_state:
    st.session_state.evaluations = []

# Sidebar
with st.sidebar:
    st.title("🤖 La Nuit de l'Info")
    st.markdown("---")
    st.subheader("About")
    st.write("""
    This chatbot helps with La Nuit de l'Info 2024 competition queries.
    It provides technical guidance and evaluates responses based on:
    - Simplicity
    - Technical Relevance
    - Technical Innovation
    - Creative Approach
    """)
    
    # Statistics
    st.markdown("---")
    st.subheader("Session Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", len(st.session_state.messages))
    with col2:
        st.metric("Technical Score", 
                 sum([1 for e in st.session_state.evaluations if e.get('technical_relevance')]))

# Main chat interface
st.title("La Nuit de l'Info Assistant")

# Chat history
for message in st.session_state.messages:
    with st.container():
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                👤 You: {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message bot-message">
                🤖 Assistant: {message["content"]}
            </div>
            """, unsafe_allow_html=True)

# Input form
with st.form(key="chat_form"):
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("Ask a question:", 
                                  placeholder="e.g., When does the event start?",
                                  label_visibility="collapsed")
    with col2:
        submit_button = st.form_submit_button("Send")

if submit_button and user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Send request to API
    try:
        response = requests.post(
            "http://localhost:8000/chatbot/",
            json={"question": user_input}
        )
        response_data = response.json()
        
        # Add bot response to history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_data["response"]
        })
        
        # Extract evaluation metrics
        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "simplicity": "simple" in response_data["response"].lower(),
            "technical_relevance": any(kw in response_data["response"].lower() 
                                     for kw in ["web", "api", "dashboard"]),
            "technical_bonus": any(kw in response_data["response"].lower() 
                                 for kw in ["algorithm", "optimization"]),
            "creative_bonus": any(kw in response_data["response"].lower() 
                                for kw in ["innovative", "creative"])
        }
        st.session_state.evaluations.append(evaluation)
        
        # Force refresh
        st.experimental_rerun()
        
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Evaluation Dashboard
if st.session_state.evaluations:
    st.markdown("---")
    st.subheader("Response Evaluation Dashboard")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create evaluation metrics chart
        metrics = ['simplicity', 'technical_relevance', 'technical_bonus', 'creative_bonus']
        values = [
            sum([e[metric] for e in st.session_state.evaluations])
            for metric in metrics
        ]
        
        fig = go.Figure(data=[
            go.Bar(
                x=metrics,
                y=values,
                marker_color=['#2ecc71', '#3498db', '#9b59b6', '#e74c3c']
            )
        ])
        
        fig.update_layout(
            title="Evaluation Metrics Distribution",
            xaxis_title="Criteria",
            yaxis_title="Count",
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Latest Evaluation")
        if st.session_state.evaluations:
            latest = st.session_state.evaluations[-1]
            for metric in metrics:
                if latest[metric]:
                    st.markdown(f"""
                    <div class="evaluation-metric" style="background-color: #e8f5e9">
                        ✅ {metric.replace('_', ' ').title()}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="evaluation-metric" style="background-color: #ffebee">
                        ❌ {metric.replace('_', ' ').title()}
                    </div>
                    """, unsafe_allow_html=True)
