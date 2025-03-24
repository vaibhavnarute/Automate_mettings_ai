import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pytz  # Fixed: changed from 'pytzs' to 'pytz'
import uuid
import os

# API endpoint
API_URL = "http://127.0.0.1:8010"  # Changed from localhost to 127.0.0.1

# Add a function to check if the API is available
def is_api_available():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"API connection error: {str(e)}")
        return False

# Set page config
st.set_page_config(
    page_title="AI Business Assistant",
    page_icon="💼",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    # Generate a unique user ID or load from cookies
    st.session_state.user_id = str(uuid.uuid4())

# Helper functions
def send_message(message):
    """Send a message to the API and get a response"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "message": message,
                "user_id": st.session_state.user_id
            }
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error connecting to the API: {str(e)}"

def schedule_meeting(summary, description, start_time, end_time, attendees):
    """Schedule a meeting via the API"""
    try:
        # Print debug information
        print(f"Attempting to connect to {API_URL}/schedule-meeting")
        
        response = requests.post(
            f"{API_URL}/schedule-meeting",
            json={
                "summary": summary,
                "description": description,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "attendees": attendees.split(",") if attendees else None,
                "user_id": st.session_state.user_id
            },
            timeout=10  # Increase timeout to 10 seconds
        )
        
        if response.status_code == 200:
            return response.json()["meeting_link"], True
        else:
            error_text = response.text
            print(f"API error: {response.status_code} - {error_text}")
            if "access_denied" in error_text or "verification" in error_text:
                return "Google API access denied. Please check: 1) Your app is in testing mode, 2) Your email is added as a test user, and 3) The scope 'https://www.googleapis.com/auth/calendar' is added in the OAuth consent screen.", False
            return f"Error: {response.status_code} - {error_text}", False
    except requests.exceptions.ConnectionError as e:
        error_msg = str(e)
        print(f"Connection error: {error_msg}")
        return f"Cannot connect to API server at {API_URL}. Please make sure the server is running.", False
    except Exception as e:
        error_msg = str(e)
        print(f"General error: {error_msg}")
        if "access_denied" in error_msg or "verification" in error_msg:
            return "Google API access denied. Please check: 1) Your app is in testing mode, 2) Your email is added as a test user, and 3) The scope 'https://www.googleapis.com/auth/calendar' is added in the OAuth consent screen.", False
        return f"Error connecting to the API: {error_msg}", False

def get_memories():
    """Get recent memories from the API"""
    try:
        response = requests.get(
            f"{API_URL}/memories/{st.session_state.user_id}"
        )
        
        if response.status_code == 200:
            return response.json()["memories"]
        else:
            return []
    except Exception as e:
        print(f"Error fetching memories: {str(e)}")
        return []

def get_memories():
    """Get recent memories from the API"""
    try:
        response = requests.get(
            f"{API_URL}/memories/{st.session_state.user_id}"
        )
        
        if response.status_code == 200:
            return response.json()["memories"]
        else:
            return []
    except Exception as e:
        print(f"Error fetching memories: {str(e)}")
        return []

# Main UI
st.title("💼 AI Business Assistant")

# Check API connection
api_available = is_api_available()
if not api_available:
    st.error("⚠️ API server is not available. Please make sure it's running at " + API_URL)

# Sidebar
with st.sidebar:
    st.header("Options")
    
    # API status indicator
    if api_available:
        st.success("API Server: Connected")
    else:
        st.error("API Server: Not Connected")
    
    # Meeting scheduler
    st.subheader("Schedule a Meeting")
    with st.form("meeting_form"):
        meeting_title = st.text_input("Meeting Title")
        meeting_desc = st.text_area("Description")
        
        col1, col2 = st.columns(2)
        with col1:
            meeting_date = st.date_input("Date", datetime.now() + timedelta(days=1))
        with col2:
            meeting_time = st.time_input("Time", datetime.now().replace(hour=10, minute=0))
        
        meeting_duration = st.slider("Duration (minutes)", 15, 120, 30, step=15)
        meeting_attendees = st.text_input("Attendees (comma-separated emails)")
        
        submit_meeting = st.form_submit_button("Schedule Meeting")
    
    if submit_meeting:
        if not meeting_title:
            st.error("Please enter a meeting title")
        else:
            # Combine date and time
            start_time = datetime.combine(meeting_date, meeting_time)
            end_time = start_time + timedelta(minutes=meeting_duration)
            
            # Schedule the meeting
            result, success = schedule_meeting(
                meeting_title, 
                meeting_desc, 
                start_time, 
                end_time, 
                meeting_attendees
            )
            
            if success:
                st.success("Meeting scheduled successfully!")
                st.markdown(f"[Open in Google Calendar]({result})")
            else:
                st.error(result)
    
    # Past conversations
    st.subheader("Past Conversations")
    memories = get_memories()
    
    if memories:
        for memory in memories:
            with st.expander(f"{memory['query'][:30]}..."):
                st.write("**You:** " + memory["query"])
                st.write("**Assistant:** " + memory["response"])
    else:
        st.info("No past conversations found")

# Chat interface
st.header("Chat with your AI Assistant")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # Get AI response
    with st.spinner("Thinking..."):
        ai_response = send_message(user_input)
    
    # Add AI response to chat
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    with st.chat_message("assistant"):
        st.write(ai_response)