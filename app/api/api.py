from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

from app.api.groq_client import GroqClient
from app.memory.faiss_memory import FaissMemory
from app.calendar.google_calendar import GoogleCalendar
from fastapi.responses import RedirectResponse

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Business Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
groq_client = GroqClient(api_key=os.getenv("GROQ_API_KEY"))
memory = FaissMemory()
calendar = GoogleCalendar()

# Define request and response models
class ChatRequest(BaseModel):
    message: str
    user_id: str

class MeetingRequest(BaseModel):
    summary: str
    description: Optional[str] = None
    start_time: str
    end_time: str
    attendees: Optional[List[str]] = None
    user_id: str

class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"message": "Business Assistant API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Retrieve relevant memories
    relevant_memories = memory.search(request.message, request.user_id)
    
    # Generate AI response
    response = groq_client.generate_response(
        request.message, 
        context=relevant_memories
    )
    
    # Store the interaction in memory
    memory.add(request.user_id, request.message, response)
    
    return ChatResponse(
        response=response,
        context={"memories": relevant_memories}
    )

@app.post("/schedule-meeting")
async def schedule_meeting(request: MeetingRequest):
    try:
        meeting_link = calendar.create_event(
            summary=request.summary,
            description=request.description,
            start_time=request.start_time,
            end_time=request.end_time,
            attendees=request.attendees,
            user_id=request.user_id
        )
        return {"meeting_link": meeting_link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/{user_id}")
async def get_memories(user_id: str, query: Optional[str] = None, limit: int = 10):
    if query:
        memories = memory.search(query, user_id, limit)
    else:
        memories = memory.get_recent(user_id, limit)
    return {"memories": memories}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/google-auth")
async def google_auth():
    """Initialize Google OAuth flow"""
    return RedirectResponse(calendar.get_authorization_url())