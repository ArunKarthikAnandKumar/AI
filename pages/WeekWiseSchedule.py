import streamlit as st
from PyPDF2 import PdfReader
from fpdf import FPDF
import unicodedata
import base64
import os
import google.generativeai as genai
from google.generativeai import GenerativeModel
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import re
import plotly.figure_factory as ff
import pandas as pd
import plotly.express as px
import traceback

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
    """Parse PDF content."""
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

def create_calendar_view(schedule_data, start_date):
    """Create a Gantt chart visualization of the schedule."""
    tasks = []
    colors = px.colors.qualitative.Set3
    color_map = {}
    current_color_idx = 0
    
    for module, weeks in schedule_data.items():
        if current_color_idx >= len(colors):
            current_color_idx = 0
        color_map[module] = colors[current_color_idx]
        current_color_idx += 1
        
        for week, details in weeks.items():
            try:
                date_range = details['dates'].split(' - ')
                start = datetime.strptime(date_range[0], '%Y-%m-%d')
                end = datetime.strptime(date_range[1], '%Y-%m-%d')
                
                for topic in details['topics']:
                    tasks.append({
                        'Task': topic,
                        'Start': start,
                        'Finish': end,
                        'Module': module,
                        'Resource': week
                    })
            except Exception as e:
                st.warning(f"Skipping week due to date parsing error: {str(e)}")
                continue
    
    if not tasks:
        st.error("No valid schedule data to visualize")
        return None
        
    df = pd.DataFrame(tasks)
    unique_modules = df['Module'].unique()
    colors_list = [color_map[module] for module in unique_modules]
    
    try:
        fig = ff.create_gantt(df,
                            colors=colors_list,
                            index_col='Module',
                            show_colorbar=True,
                            group_tasks=True,
                            showgrid_x=True,
                            showgrid_y=True)
        
        fig.update_layout(
            title='Course Schedule Timeline',
            xaxis_title='Date',
            height=400 + (len(tasks) * 25),
            font=dict(size=10),
            showlegend=True
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating Gantt chart: {str(e)}")
        return None

def generate_pdf(content, filename):
    """Generate PDF from content."""
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

def extract_json_from_response(response_text):
    """Extract JSON from model response text."""
    try:
        match = re.search(r'```(?:json|python)?\s*({[\s\S]*?})\s*```', response_text)
        if match:
            json_str = match.group(1)
        else:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
            else:
                return None
        
        json_str = json_str.strip()
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Error extracting JSON: {str(e)}")
        return None

def parse_duration(duration):
    """Helper function to parse duration values into float."""
    if isinstance(duration, (int, float)):
        return float(duration)
    elif isinstance(duration, str):
        try:
            return float(duration.replace('hours', '').strip())
        except ValueError:
            return 3.0
    elif isinstance(duration, list):
        for item in duration:
            try:
                return float(str(item).replace('hours', '').strip())
            except ValueError:
                continue
        return 3.0
    return 3.0

def generate_week_schedule(module_content, module_duration, start_date):
    """Generate weekly schedule for a module."""
    duration = parse_duration(module_duration)
    
    schedule_prompt = f"""
    Create a detailed week-by-week schedule for the following module:
    
    Module Content: {module_content}
    Hours allocated: {duration}
    Starting from: {start_date}
    
    Format your response as a JSON object with the following structure:
    {{
        "Week 1": {{
            "dates": "{start_date} - {start_date + timedelta(days=7)}",
            "topics": ["topic1", "topic2"],
            "activities": ["activity1", "activity2"],
            "objectives": ["objective1", "objective2"]
        }}
    }}
    Ensure all dates are in YYYY-MM-DD format.
    """
    
    try:
        response = chat.send_message(schedule_prompt)
        schedule_data = extract_json_from_response(response.text)
        if schedule_data:
            return schedule_data
        else:
            end_date = start_date + timedelta(days=7)
            return {
                "Week 1": {
                    "dates": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
                    "topics": module_content if isinstance(module_content, list) else [module_content],
                    "activities": ["Lecture", "Discussion"],
                    "objectives": ["Understand basic concepts"]
                }
            }
    except Exception as e:
        st.error(f"Error generating schedule: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Course Schedule Generator", layout="wide")
    st.title("Course Schedule Generator 📅")

    try:
        # Initialize Gemini model
        load_dotenv()
        geminiAPIKey = os.getenv("API_KEY")
        genai.configure(api_key=geminiAPIKey)
        model = GenerativeModel()
        chat = model.start_chat(history=[])
    except Exception as e:
        st.error(f"Unable to setup generative model: {str(e)}")
        st.error(f"Detailed error: {traceback.format_exc()}")
        return

    # File upload
    uploaded_file = st.file_uploader("Upload Course Syllabus PDF", type=["pdf"])
    
    if uploaded_file is not None:
        try:
            parsed_text = parse_pdf(uploaded_file)
            st.session_state["parsed_text"] = parsed_text
            st.success("PDF parsed successfully!")

            # Schedule parameters
            with st.expander("Schedule Parameters"):
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Course Start Date", min_value=datetime.today())
                with col2:
                    total_weeks = st.number_input("Total Course Duration (weeks)", min_value=1, max_value=52, value=15)

            if st.button("Generate Schedule"):
                with st.spinner("Generating course schedule..."):
                    try:
                        # Get module information
                        duration_prompt = f"Analyze this syllabus and return a JSON with module names and durations in hours: {parsed_text}"
                        content_prompt = f"Analyze this syllabus and return a JSON with module names and their topics: {parsed_text}"
                        
                        week_data = extract_json_from_response(chat.send_message(duration_prompt).text)
                        content_data = extract_json_from_response(chat.send_message(content_prompt).text)
                        
                        if week_data and content_data:
                            # Generate schedule
                            schedule_data = {}
                            current_date = start_date
                            
                            for module, duration in week_data.items():
                                if module in content_data:
                                    schedule = generate_week_schedule(
                                        content_data[module],
                                        duration,
                                        current_date
                                    )
                                    if schedule:
                                        schedule_data[module] = schedule
                                        weeks = max(1, round(parse_duration(duration) / 3))
                                        current_date += timedelta(weeks=weeks)
                            
                            # Store schedule data
                            st.session_state["schedule_data"] = schedule_data
                            
                            # Create visualization
                            fig = create_calendar_view(schedule_data, start_date)
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Display schedule details
                            st.subheader("Detailed Schedule")
                            for module, weeks in schedule_data.items():
                                with st.expander(f"{module}"):
                                    for week, details in weeks.items():
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
                            
                            # PDF download option
                            if st.button("Download Schedule PDF"):
                                pdf_filename = "course_schedule.pdf"
                                schedule_text = ""
                                for module, weeks in schedule_data.items():
                                    schedule_text += f"\n\n{module}\n"
                                    for week, details in weeks.items():
                                        schedule_text += f"\n{week} ({details['dates']})\n"
                                        schedule_text += "Topics:\n" + "\n".join(f"- {t}" for t in details['topics']) + "\n"
                                        schedule_text += "Activities:\n" + "\n".join(f"- {a}" for a in details['activities']) + "\n"
                                        schedule_text += "Objectives:\n" + "\n".join(f"- {o}" for o in details['objectives']) + "\n"
                                
                                generate_pdf(schedule_text, pdf_filename)
                                with open(pdf_filename, "rb") as pdf_file:
                                    pdf_data = pdf_file.read()
                                    st.download_button(
                                        label="Download Schedule PDF",
                                        data=pdf_data,
                                        file_name=pdf_filename,
                                        mime="application/pdf"
                                    )
                        
                        else:
                            st.error("Could not parse module information from the syllabus")
                    
                    except Exception as e:
                        st.error(f"Error generating schedule: {str(e)}")
                        st.error(f"Detailed error: {traceback.format_exc()}")
                        
        except Exception as e:
            st.error(f"Error processing PDF: {str(e)}")
            st.error(f"Detailed error: {traceback.format_exc()}")

if __name__ == "__main__":
    main()