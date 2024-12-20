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

def generate_pdf(content, filename):
    content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode('ascii')
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)

    sections = content.split('\n\n')  
    for section in sections:
        if section.startswith('**'):
            pdf.set_font('Arial', 'B', 12)
            pdf.multi_cell(0, 10, section)
        else:
            pdf.set_font('Arial', '', 12)
            pdf.multi_cell(0, 10, section)

    # Save PDF
    pdf.output(filename, 'F')
    return pdf

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


def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])

def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages

if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state.messages = []
        save_chat_history([])

col1, col2 = st.columns(2)

col1, col_divider, col2 = st.columns([3.0,0.1,7.0])

with col1:
    st.header("Course Details 📋")
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
                response = chat.send_message(DICTATOR_PROMPT)
                response = chat.send_message(st.session_state['course_outline'])
                Dict = response.text
                cleaned_text = Dict.replace("```python", "").replace("```", "").strip()

                try:
                    module_lessons = eval(cleaned_text)
                    print("Parsed JSON:", module_lessons)
                except json.JSONDecodeError as e:
                    print("Error parsing JSON:", e)
                    module_lessons = {}

                modifications = {}
               
               
                st.write("### Modify Course Outline")

                # Loop through each module to display content and allow modifications
                for module_name, lessons in module_lessons.items():
                    st.write(f"**{module_name}**")
                    
                    # Display lesson details
                    for lesson_name in lessons:
                        st.write(f"- {lesson_name}")
                    
                    # Input field for module content changes
                    mod_input = st.text_area(f"Modify content for {module_name} (Optional):")
                    if mod_input:
                        modifications[module_name] = mod_input
                    
                
                if st.button("Submit Changes"):
                    # Store modifications and weightage updates in session state
                    st.session_state.modifications = {
                        "content_changes": modifications,
                    }

                    # Prepare input for the modification prompt
                    mod_text = f"""
                    I have provided the "course outline", "modifications", and "weightage updates". 
                    Your task is to modify the existing course outline using the provided inputs and generate the complete modified course outline as the output. 
                    Here are the details:

                    Modifications:
                    {st.session_state.modifications['content_changes']}
                    
                    Course Outline:
                    {st.session_state['course_outline']}
give the output as plaintext.


                    """

                    response = chat.send_message(TABLER_PROMPT)
                    response = chat.send_message(mod_text)

                    Mod_CO = response.text
                    st.session_state["modified_course_outline"] = Mod_CO

                    st.success("Modified course outline generated! 🎉")

                    with st.expander("Modified Course Outline"):
                        st.write(st.session_state["modified_course_outline"],unsafe_allow_html=True)

                        # Generate the PDF if not already created
                        if "pdf" not in st.session_state:
                            # complete_course_content = module_content 
                            st.session_state.pdf = generate_pdf(st.session_state['modified_course_outline'], "course.pdf")
                            #b64 = base64.b64encode(st.session_state.pdf.output(dest="S").encode("latin1")).decode()
                            with open("course.pdf","rb") as pdf_file: 
                                PDFbyte = pdf_file.read()

                            st.success("Your PDF file is ready!")

                        # Provide download button for the PDF
                        button_label = "Download PDF"
                        st.download_button(label=button_label, data=PDFbyte, file_name="course.pdf", mime="application/octet-stream", key="download_pdf_button")
                        #break

                        

    else:
        st.write("Your generated content will appear here.")

# Save chat history after each interaction
save_chat_history(st.session_state.messages)
