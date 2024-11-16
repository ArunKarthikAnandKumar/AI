import google.generativeai as genai
from google.generativeai import GenerativeModel
import streamlit as st
from dotenv import load_dotenv
import os
import json
import shelve
import unicodedata
from fpdf import FPDF # type: ignore
import base64
from prompts.tabler_prompt import TABLER_PROMPT
from prompts.dictator_prompt import DICTATOR_PROMPT


geminiAPIKey = os.getenv("API_KEY")

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Course Outline', 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1)
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def bullet_list(self, items):
        self.set_font('Arial', '', 12)
        for item in items:
            self.cell(5)  # Indentation for bullet point
            self.cell(0, 10, f"• {item}", 0, 1)
        self.ln()

    def module_section(self, title, hours, topics):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"{title} - {hours}", 0, 1)
        self.set_font('Arial', '', 12)
        for topic in topics:
            self.cell(5)
            self.cell(0, 10, f"• {topic}", 0, 1)
        self.ln()

def generate_outline_pdf(content, filename):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Normalize content
    content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode('ascii')
    
    # Course details
    pdf.chapter_title("Course Details")
    pdf.chapter_body(content['Course Details'])

    # Course objectives
    pdf.chapter_title("Course Objectives")
    pdf.bullet_list(content['Course Objectives'])

    # Course outcomes
    pdf.chapter_title("Course Outcomes")
    pdf.bullet_list(content['Course Outcomes'])

    # Modules
    pdf.chapter_title("Module Structure")
    for module in content['Modules']:
        pdf.module_section(module['title'], module['hours'], module['topics'])

    # Textbooks
    pdf.chapter_title("Textbooks")
    pdf.bullet_list(content['Textbooks'])

    # Reference books
    pdf.chapter_title("Reference Books")
    pdf.bullet_list(content['Reference Books'])

    # Mode of Evaluation
    pdf.chapter_title("Mode of Evaluation")
    pdf.bullet_list(content['Mode of Evaluation'])

    pdf.output(filename, 'F')
    return pdf

def generate_pdf(content, filename):
    content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode('ascii')
    
    # Initialize PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)

    # Split the content based on sections and sub-sections
    sections = content.split('\n\n')  # Split based on double line breaks
    
    for section in sections:
        # Section Header: If it's a major section like Course Code, Course Title, etc.
        if section.startswith('**'):
            # Set section title with bold font
            pdf.set_font('Arial', 'B', 12)
            pdf.multi_cell(0, 10, section)
        else:
            # Regular content
            pdf.set_font('Arial', '', 12)
            pdf.multi_cell(0, 10, section)

    # Save PDF
    pdf.output(filename, 'F')
    return pdf

# Customizing the page configuration
st.set_page_config(
    page_title="Automated Course Content Generator",
    page_icon=":robot:",
    layout="wide",
    initial_sidebar_state="collapsed",
    
)

load_dotenv()

st.title("Automated Course Content Generator 🤖")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

try:
    genai.configure(api_key=geminiAPIKey)
    model = GenerativeModel()
    chat = model.start_chat(history=[])

except :
    print("Unable to setup gemini")

# Ensure openai_model is initialized in session state


# Load chat history from shelve file
def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])

# Save chat history to shelve file
def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages

# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

# Sidebar with a button to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state.messages = []
        save_chat_history([])

# Example of using columns for advanced layouts
col1, col2 = st.columns(2)

col1, col_divider, col2 = st.columns([3.0,0.1,7.0])

with col1:
    st.header("Course Details 📋")
    # Interactive widgets for course details
    course_name = st.text_input("Course Name")
    target_audience_edu_level = st.selectbox(
        "Target Audience Education Level",
        ["Bachelors", "Masters"]
    )
    difficulty_level = st.radio(
        "Course Difficulty Level",
        ["Beginner", "Intermediate", "Advanced"]
    )
    num_modules = st.slider(
        "No. of Modules",
        min_value=1, max_value=8
    )
    course_duration = st.text_input("Course Duration")
    course_credit = st.text_input("Course Credit")

    # Save widget states in session_state
    st.session_state.course_name = course_name
    st.session_state.target_audience_edu_level = target_audience_edu_level
    st.session_state.difficulty_level = difficulty_level
    st.session_state.num_modules = num_modules
    st.session_state.course_duration = course_duration
    st.session_state.course_credit = course_credit

    button1, button2 = st.columns([1, 0.8])
    with button1:
        generate_button = st.button("Generate Course Outline", help="Click me to generate course outline!😁")
    with button2:
        if "pdf" in st.session_state:
            new_course_button = st.button("Start a New Course", help="Click me to start a new course!💡")
            if new_course_button:
                st.session_state.course_name = ""
                st.session_state.target_audience_edu_level = ""
                st.session_state.difficulty_level = ""
                st.session_state.num_modules = 1
                st.session_state.course_duration = ""
                st.session_state.course_credit = ""
                st.session_state.pdf = False
                st.experimental_rerun()
                
with col2:
   
    st.header("Generated Course Content 📝")
    # Display the generated content here
    if generate_button and "pdf" not in st.session_state:
        
        # Include user selections in the message history
        user_selections = f"Course Name: {course_name}\nTarget Audience Edu Level: {target_audience_edu_level}\nDifficulty Level: {difficulty_level}\nNo. of Modules: {num_modules}\nCourse Duration: {course_duration}\nCourse Credit: {course_credit}"
        st.session_state.messages.append({"role": "user", "parts": user_selections})

        PROMPT=f"You are Prompter, the world's best Prompt Engineer. I am using another GenAI tool, Tabler, that helps in generating a course outline for trainers and professionals for the automated course content generation for their courses. Your job is to strictly use the only following inputs: 1) Course Name: {course_name} 2) Target Audience Edu Level: {target_audience_edu_level} 3) Course Difficulty Level: {difficulty_level} 4) No. of Modules: {num_modules} 5) Course Duration: {course_duration} 6) Course Credit: {course_credit}.  to generate a prompt for Tabler so that it can produce the best possible outputs. The prompt that you generate must be comprehensive and strictly follow the above given inputs and also mention the given inputs in the prompt you generate. Moreover, it is your job to also identify if the course name is appropriate and not gibberish."

        response= chat.send_message(PROMPT)

        generated_prompt = response.text
        print(generated_prompt)
        
        
        with st.spinner("Generating course outline..."):

            response = chat.send_message(TABLER_PROMPT)
            response = chat.send_message(generated_prompt)

            Course_outline = response.text
            st.success("Course outline generated successfully!")
 

            st.session_state['course_outline'] = Course_outline
            st.session_state['buttons_visible'] = True

    
    if 'course_outline' in st.session_state and "pdf" not in st.session_state:
        with st.expander("Course Outline"):
            st.write(st.session_state['course_outline'])

        if 'buttons_visible' in st.session_state and st.session_state['buttons_visible']:
            button1, button2 = st.columns([1, 2])
            with button1:
                complete_course_button = st.button("Looks cool. Generate complete course!", help="Click me to generate complete course!😍")
            with button2:
                modifications_button = st.button("Wai wait..!, I need to make some modifications", help="Click me to modify the course outline!🧐")

            # Handle button actions
            if complete_course_button:
                st.session_state['complete_course'] = True
                st.session_state['modifications'] = False
            elif modifications_button:
                st.session_state['modifications'] = True
                st.session_state['complete_course'] = False

            if 'complete_course' in st.session_state and st.session_state['complete_course']:
                with st.spinner("Generating complete course..."):
                    response = chat.send_message(DICTATOR_PROMPT)
                    response = chat.send_message(st.session_state['course_outline'])
                    print('before parsing')
                    print(st.session_state['course_outline'])

                    Dict = response.text
                    
                  
                    cleaned_text = Dict.replace("```python", "").replace("```", "").strip()

                    # Now load the JSON-compatible string
                    try:
                        module_lessons = eval(cleaned_text)
                        print("Parsed JSON:", module_lessons)
                    except json.JSONDecodeError as e:
                        print("Error parsing JSON:", e)
                    

                    if "pdf" not in st.session_state:
                        # complete_course_content = module_content 
                        st.session_state.pdf = generate_pdf(st.session_state['course_outline'], "course.pdf")
                        with open("course.pdf","rb") as pdf_file: 
                                PDFbyte = pdf_file.read()

                        st.success("Your PDF file is ready!")

                    # Provide download button for the PDF
                    button_label = "Download PDF"
                    st.download_button(label=button_label, data=PDFbyte, file_name="course.pdf", mime="application/octet-stream", key="download_pdf_button")

                

                
            elif 'modifications' in st.session_state:
                modifications = st.text_input("Please enter the modifications you'd like to make:")
                if modifications:
                    st.session_state.modifications = modifications
                    Mod = f""" I have provided you with the "course outline" and "modifications". Your task is to modify the existing course outline using modifications provided, and give complete modified course outline as the output. 
                    modifications:
                    {st.session_state.modifications} 
                    course outline:
                    {st.session_state['course_outline']}"""

                    response = chat.send_message(TABLER_PROMPT)
                    response = chat.send_message(Mod)

                    print('Response Before')
                    Mod_CO = response.text
                    print(Mod_CO)
                    

                    with st.spinner("Generating complete course with the specified modifications..."):
                        response = chat.send_message(DICTATOR_PROMPT)
                        response = chat.send_message(Mod_CO)
                        with st.expander("Modified Course Outline"):
                          st.write(Mod_CO)
                     
                        Dict = response.text
                        print('Response After')
                        print(Dict)
                        cleaned_text = Dict.replace("```python", "").replace("```", "").strip()

                    # Now load the JSON-compatible string
                    try:
                        module_lessons = eval(cleaned_text)
                        print("Parsed JSON:", module_lessons)
                    except json.JSONDecodeError as e:
                        print("Error parsing JSON:", e)

                        # Generate the PDF if not already created
                        if "pdf" not in st.session_state:
                            # complete_course_content = module_content 
                            st.session_state.pdf = generate_pdf(st.session_state['course_outline'], "course.pdf")
                            #b64 = base64.b64encode(st.session_state.pdf.output(dest="S").encode("latin1")).decode()
                            with open("course.pdf","rb") as pdf_file: 
                                PDFbyte = pdf_file.read()

                            st.success("Your PDF file is ready!")

                        # Provide download button for the PDF
                        button_label = "Download PDF"
                        st.download_button(label=button_label, data=PDFbyte, file_name="course.pdf", mime="application/octet-stream", key="download_pdf_button")

                        

    else:
        st.write("Your generated content will appear here.")

# Save chat history after each interaction
save_chat_history(st.session_state.messages)
