import os
import json
from typing import List, Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime
import pytz

class GoogleCalendar:
    def __init__(self):
        # Make sure to use the correct scope for Google Calendar
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.credentials_dir = os.path.join(os.path.dirname(__file__), "credentials")
        
        # Create credentials directory if it doesn't exist
        os.makedirs(self.credentials_dir, exist_ok=True)
        
        # Path to client secrets file
        self.client_secrets_file = os.path.join(self.credentials_dir, "client_secret.json")
    
    def _get_credentials(self, user_id: str) -> Credentials:
        """Get or refresh credentials for a user"""
        token_file = os.path.join(self.credentials_dir, f"{user_id}_token.json")
        creds = None
        
        # Load existing credentials
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_info(
                json.load(open(token_file))
            )
        
        # If credentials don't exist or are invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"Client secrets file not found at {self.client_secrets_file}. "
                        "Please download it from Google Cloud Console."
                    )
                
                # Update the SCOPES and add redirect URI
                SCOPES = [
                    'https://www.googleapis.com/auth/calendar',
                    'openid',
                    'https://www.googleapis.com/auth/userinfo.email',
                    'https://www.googleapis.com/auth/userinfo.profile'
                ]
                
                REDIRECT_URI = 'http://localhost:8010/google-auth'  # Match your API port
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes
                )
                # Add localhost to the redirect URI for testing
                flow.redirect_uri = 'http://localhost:8501/'
                creds = flow.run_local_server(port=8501)
                
            # Save credentials
            with open(token_file, "w") as token:
                token.write(creds.to_json())
        
        return creds
    
    def create_event(
        self, 
        summary: str, 
        start_time: str, 
        end_time: str, 
        user_id: str,
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> str:
        """
        Create a calendar event
        
        Args:
            summary: Event title
            start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
            end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
            user_id: User ID for authentication
            description: Optional event description
            attendees: Optional list of attendee email addresses
            
        Returns:
            The event link/URL
        """
        try:
            # Get credentials
            creds = self._get_credentials(user_id)
            
            # Build the service
            service = build('calendar', 'v3', credentials=creds)
            
            # Format attendees
            formatted_attendees = None
            if attendees:
                formatted_attendees = [{'email': email} for email in attendees]
            
            # Create event body
            event_body = {
                'summary': summary,
                'description': description or '',
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': True,
                },
            }
            
            # Add attendees if provided
            if formatted_attendees:
                event_body['attendees'] = formatted_attendees
            
            # Create the event
            event = service.events().insert(calendarId='primary', body=event_body).execute()
            
            # Return the event link
            return event.get('htmlLink', '')
            
        except Exception as e:
            print(f"Error creating calendar event: {str(e)}")
            raise