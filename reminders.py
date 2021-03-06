from __future__ import print_function
import datetime
from dateutil.parser import parse, isoparse
from dateutil import tz
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from app import app
from dotenv import load_dotenv
from app.models import Student
from app.email import send_reminder_email, weekly_report_email
import requests

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    flow = Flow.from_client_secrets_file(
                os.path.join(basedir, 'credentials.json'), SCOPES)

    authorization_url, state = flow.authorization_url(
    # Enable offline access so that you can refresh an access token without
    # re-prompting the user for permission. Recommended for web server apps.
    access_type='offline',
    # Enable incremental authorization. Recommended as a best practice.
    include_granted_scopes='true')

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(basedir, 'credentials.json'), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    today = datetime.datetime.strptime(now, "%Y-%m-%dT%H:%M:%S.%fZ")
    upcoming_start = (today + datetime.timedelta(hours=44)).isoformat() + 'Z'
    upcoming_end = (today + datetime.timedelta(hours=68)).isoformat() + 'Z'
    print("Session reminders for " + datetime.datetime.strftime(parse(upcoming_start), format="%A, %b %-d") + ":")
    events_result = service.events().list(calendarId='primary', timeMin=upcoming_start,
                                        timeMax=upcoming_end, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    students = Student.query.order_by(-Student.id).all()
    reminder_list = []

    # Use fallback quote if request fails
    quote = None
    quote = requests.get("https://zenquotes.io/api/today")

    for event in events:
        for student in students:
            if " " + student.student_name + " " in event.get('summary'):
                reminder_list.append(student.student_name)
                send_reminder_email(event, student, quote)

    if len(reminder_list) is 0:
        print("No reminders sent.")


    day_of_week = datetime.datetime.strftime(parse(now), format="%A")
    week_end = (today + datetime.timedelta(days=7, hours=31)).isoformat() + 'Z'
    week_events_result = service.events().list(calendarId='primary', timeMin=upcoming_start,
                                        timeMax=week_end, singleEvents=True,
                                        orderBy='startTime').execute()
    week_events = week_events_result.get('items', [])
    week_events_list = []
    session_count = 0
    tutoring_hours = 0
    active_students = []
    unscheduled_students = []

    if day_of_week == "Friday":
        for e in week_events:
            week_events_list.append(e.get('summary'))

            # Get total duration of week's tutoring
            for s in students:
                if " " + s.student_name + " " in e.get('summary'):
                    start = isoparse(e['start'].get('dateTime'))
                    end = isoparse(e['end'].get('dateTime'))
                    duration = str(end - start)
                    (h, m, s) = duration.split(':')
                    hours = int(h) + int(m) / 60 + int(s) / 3600
                    tutoring_hours += hours

        #Get number of sessions and lists of active and unscheduled students
        for s in students:
            if s.active:
                active_students.append(s.student_name)
                count = sum(" " + s.student_name + " " in e for e in week_events_list)
                session_count += count
                if count is 0:
                    unscheduled_students.append(s.student_name)
        weekly_report_email(str(session_count), str(tutoring_hours), str(len(active_students)), unscheduled_students, today, quote)


if __name__ == '__main__':
    main()
