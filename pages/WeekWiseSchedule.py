import streamlit as st
from PyPDF2 import PdfReader
from fpdf import FPDF
import unicodedata
import base64
import os
import google.generativeai as genai
from google.generativeai import GenerativeModel
from dotenv import load_dotenv
from prompts.dictator_prompt import DICTATOR_PROMPT
from prompts.tabler_prompt import TABLER_PROMPT
from prompts.week_prompt import WEEK_PROMPT
import json
from datetime import datetime, timedelta
import re

# Load API key from environment
load_dotenv()
geminiAPIKey = os.getenv("API_KEY")

# Configure the Generative AI model
try:
    genai.configure(api_key=geminiAPIKey)
    model = GenerativeModel()
    chat = model.start_chat(history=[])
except Exception as e:
    st.error(f"Unable to setup generative model: {e}")

def parse_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

def generate_pdf(content, filename):
    content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode('ascii')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    
    sections = content.split('\n\n')
    for section in sections:
        if section.startswith('**') or section.startswith('Week'):
            pdf.set_font('Arial', 'B', 12)
            pdf.multi_cell(0, 10, section)
        else:
            pdf.set_font('Arial', '', 12)
            pdf.multi_cell(0, 10, section)
    
    pdf.output(filename, 'F')
    return pdf

def download_pdf(pdf_filename):
    with open(pdf_filename, "rb") as pdf_file:
        pdf_data = pdf_file.read()
        st.download_button(
            label="Download Schedule PDF",
            data=pdf_data,
            file_name=pdf_filename,
            mime="application/pdf"
        )

def extract_json_from_response(response_text):
    """Extract JSON from model response text."""
    # Try to find JSON-like structure in the text
    try:
        # First, try to find content between triple backticks
        match = re.search(r'```(?:json|python)?\s*({[\s\S]*?})\s*```', response_text)
        if match:
            json_str = match.group(1)
        else:
            # If no backticks, try to find first { and last }
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
            else:
                return None
        
        # Clean up the string and parse JSON
        json_str = json_str.strip()
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Error extracting JSON: {str(e)}")
        return None

def generate_week_schedule(module_content, module_duration, start_date):
    """Generate weekly schedule for a module."""
    schedule_prompt = f"""
    Create a detailed week-by-week schedule for the following module:
    
    Module Content: {module_content}
    Hours allocated: {module_duration}
    Starting from: {start_date}
    
    Format your response as a JSON object with weeks as keys and details as values. Example:
    {{
        "Week 1": {{
            "dates": "Start - End",
            "topics": ["topic1", "topic2"],
            "activities": ["activity1", "activity2"],
            "objectives": ["objective1", "objective2"]
        }},
        "Week 2": {{
            ...
        }}
    }}
    """
    
    try:
        response = chat.send_message(schedule_prompt)
        schedule_data = extract_json_from_response(response.text)
        if schedule_data:
            return schedule_data
        else:
            st.warning("Could not parse schedule data, using simple format instead.")
            return {
                "Week 1": {
                    "dates": f"{start_date} - {start_date + timedelta(days=7)}",
                    "topics": module_content if isinstance(module_content, list) else [module_content],
                    "activities": ["Lecture", "Discussion"],
                    "objectives": ["Understand basic concepts"]
                }
            }
    except Exception as e:
        st.error(f"Error generating schedule: {e}")
        return None

# Set up the Streamlit page
st.set_page_config(page_title="Course Schedule Generator", layout="wide")
st.title("Course Schedule Generator 📅")

# PDF file upload
uploaded_file = st.file_uploader("Upload Course Syllabus PDF", type=["pdf"])
if uploaded_file is not None:
    parsed_text = parse_pdf(uploaded_file)
    st.session_state["parsed_text"] = parsed_text
    st.success("PDF parsed successfully!")

    # Get course duration and start date
    with st.expander("Schedule Parameters"):
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Course Start Date", min_value=datetime.today())
        with col2:
            total_weeks = st.number_input("Total Course Duration (weeks)", min_value=1, max_value=52, value=15)

    # Generate initial course structure
    if st.button("Generate Schedule"):
        with st.spinner("Generating course schedule..."):
            try:
                # Get module durations
                duration_prompt = f"""
                Analyze the following syllabus and return a JSON object with module names as keys and 
                their duration in hours as values. Include only the JSON object in your response:
                
                {st.session_state["parsed_text"]}
                """
                week_response = chat.send_message(duration_prompt)
                
                # Get module contents
                content_prompt = f"""
                Analyze the following syllabus and return a JSON object with module names as keys and 
                their content as arrays of topics. Include only the JSON object in your response:
                
                {st.session_state["parsed_text"]}
                """
                content_response = chat.send_message(content_prompt)
                
                # Parse responses
                week_data = extract_json_from_response(week_response.text)
                content_data = extract_json_from_response(content_response.text)
                
                if week_data and content_data:
                    # Generate week-wise schedule
                    full_schedule = {}
                    current_date = start_date
                    
                    for module, duration in week_data.items():
                        if module in content_data:
                            module_schedule = generate_week_schedule(
                                content_data[module],
                                duration,
                                current_date
                            )
                            if module_schedule:
                                full_schedule[module] = module_schedule
                                # Update current_date based on module duration
                                weeks_for_module = max(1, round(float(duration) / 3))  # Assuming 3 hours per week
                                current_date += timedelta(weeks=weeks_for_module)
                    
                    # Store and display schedule
                    st.session_state["week_schedule"] = full_schedule
                    
                    # Display the schedule
                    st.subheader("Course Schedule")
                    for module, schedule in full_schedule.items():
                        st.markdown(f"### {module}")
                        for week, details in schedule.items():
                            st.markdown(f"#### {week} ({details['dates']})")
                            st.markdown("**Topics:**")
                            for topic in details['topics']:
                                st.markdown(f"- {topic}")
                            st.markdown("**Activities:**")
                            for activity in details['activities']:
                                st.markdown(f"- {activity}")
                            st.markdown("**Learning Objectives:**")
                            for objective in details['objectives']:
                                st.markdown(f"- {objective}")
                            st.markdown("---")
                    
                    # Generate PDF option
                    if st.button("Download Schedule PDF"):
                        pdf_filename = "course_schedule.pdf"
                        schedule_text = ""
                        for module, schedule in full_schedule.items():
                            schedule_text += f"\n\n{module}\n"
                            for week, details in schedule.items():
                                schedule_text += f"\n{week} ({details['dates']})\n"
                                schedule_text += "Topics:\n" + "\n".join(f"- {t}" for t in details['topics']) + "\n"
                                schedule_text += "Activities:\n" + "\n".join(f"- {a}" for a in details['activities']) + "\n"
                                schedule_text += "Objectives:\n" + "\n".join(f"- {o}" for o in details['objectives']) + "\n"
                        
                        generate_pdf(schedule_text, pdf_filename)
                        download_pdf(pdf_filename)
                
                else:
                    st.error("Could not parse module information from the syllabus")
                
            except Exception as e:
                st.error(f"Error generating schedule: {str(e)}")
                st.error("Full error details:", exc_info=True)