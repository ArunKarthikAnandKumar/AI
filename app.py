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
# from prompts.coursify_prompt import COURSIFY_PROMPT
from prompts.tabler_prompt import TABLER_PROMPT
from prompts.dictator_prompt import DICTATOR_PROMPT
from prompts.quizzy_prompt import QUIZZY_PROMPT


geminiAPIKey = os.getenv("API_KEY")

def generate_pdf(content, filename):
    content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode('ascii')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.multi_cell(0, 10, content)
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
        min_value=1, max_value=15
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

        PROMPT = f"""
    You are Prompter, the world's best Prompt Engineer. I am using another GenAI tool, Tabler, to generate a comprehensive course outline for trainers and professionals in automated course content creation. Your task is to use **only** the following inputs:

    1. **Course Name**: {course_name}
    2. **Target Audience Education Level**: {target_audience_edu_level}
    3. **Course Difficulty Level**: {difficulty_level}
    4. **Number of Modules**: {num_modules}
    5. **Course Duration**: {course_duration}
    6. **Course Credit**: {course_credit}

    In addition, generate modules based on below topics:

    - **Algorithm Design Paradigms**: Greedy Techniques, Backtracking Techniques, Dynamic Programming, Branch & Bound Techniques
    - **String Matching Algorithms**
    - **Shortest Path Algorithms**: All-pairs shortest path algorithms
    - **Network Flow Algorithms**
    - **Computational Geometry**: Line Segments, Convex Hull finding algorithms
    - **Randomized Algorithms**
    - **Complexity Classification**: Approximation algorithms

    Your goal is to create a detailed and structured prompt for Tabler that strictly follows these inputs. Ensure that the generated prompt clearly mentions each input field and reflects the specified topics accurately. Additionally, verify that the provided course name is relevant and appropriate for the content; it should not be nonsensical or gibberish.
    """

        response= chat.send_message(PROMPT)

        generated_prompt = response.text
        print(generated_prompt)
        # st.success("Prompt generated successfully!")
        # st.write(generated_prompt)
        
        
        with st.spinner("Generating course outline..."):

            response = chat.send_message(TABLER_PROMPT)
            response = chat.send_message(generated_prompt)

            Course_outline = response.text
            print(Course_outline)
            st.success("Course outline generated successfully!")

            # with st.expander("Course Outline"):
            #     st.write(Course_outline)
            

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
                    
                    # st.success("DICTator is here!")
                    # st.write(Dict)

                    cleaned_text = Dict.replace("```python", "").replace("```", "").strip()

                    # Now load the JSON-compatible string
                    try:
                        module_lessons = eval(cleaned_text)
                        print("Parsed JSON:", module_lessons)
                    except json.JSONDecodeError as e:
                        print("Error parsing JSON:", e)
                    

    # Rest of your code using `module_lessons`...        
                # Generate content for each module and lesson
                for module_name, lessons in module_lessons.items():
                    module_content = ""

                    # Loop through lessons in each module
                    for lesson_name in lessons:
                        module_lesson_prompt = f"""You are Coursify, an AI assistant specialized in generating high-quality educational content for online courses. Your knowledge spans a wide range of academic and professional domains, allowing you to create in-depth and engaging material on any given topic. For this task, you will be generating detailed content for the lesson '{lesson_name}' which is part of the module '{module_name}' in the course '{course_name}'. Your goal is to provide a comprehensive and learner-friendly exploration of this specific topic, covering all relevant concepts, theories, and practical applications, as if you were an experienced instructor teaching the material.

                        To ensure the content is effective and aligns with best practices in instructional design, you will follow Bloom's Taxonomy approach. This means structuring the material in a way that progressively builds learners' knowledge and skills, starting from foundational concepts and working up to higher-order thinking and application. Your response should be verbose, with in-depth explanations, multiple examples, and a conversational tone that mimics an instructor's teaching style.

                        The structure of your response should include (but NOT limited to) the following elements:

                        1) Introduce the topic and provide context, explaining its relevance and importance within the broader course and domain, as an instructor would do in a classroom setting.
                        2) Define and clarify key terms, concepts, and principles related to the topic, with detailed explanations, analogies, and examples to aid comprehension.
                        3) Present thorough, step-by-step explanations of the concepts, using real-world scenarios, visual aids, and analogies to ensure learners grasp the material.
                        4) Discuss real-world applications, case studies, or scenarios that demonstrate the practical implications of the topic, drawing from industry best practices and authoritative sources.
                        5) Incorporate interactive elements, such as reflective questions, exercises, or problem-solving activities, to engage learners and reinforce their understanding, as an instructor would do in a classroom.
                        6) Seamlessly integrate relevant tangential concepts or background information as needed to provide a well-rounded learning experience, ensuring learners have the necessary foundational knowledge.
                        7) Maintain a conversational, approachable tone while ensuring accuracy and depth of content, as if you were an experienced instructor teaching the material.

                        Remember, the goal is to create a comprehensive and self-contained learning resource on the specified topic, with the level of detail and instructional quality that one would expect from an expert instructor. Your output should be formatted using Markdown for clarity and easy integration into course platforms.
                        Note: Add a blank line at the end of the course content.
                        Make sure the content generated is easily convertible to a sensible using HTML Tags.
                        """
                        
                        with st.spinner(f"Generating content for {module_name}, {lesson_name}"):
                            response = chat.send_message(module_lesson_prompt)
                            complete_course = response.text
                            
                            st.success(f"Generated content for {module_name}, {lesson_name}")
                            
                            with st.expander("Click to view!"):
                                st.write(complete_course)
                            
                            module_content += complete_course + "\n\n"

                  

                    # Generate the PDF if not already created
                    if "pdf" not in st.session_state:
                        # complete_course_content = module_content 
                        st.session_state.pdf = generate_pdf(st.session_state['course_outline'], "course.pdf")
                        with open("course.pdf","rb") as pdf_file: 
                                PDFbyte = pdf_file.read()

                        st.success("Your PDF file is ready!")

                    # Provide download button for the PDF
                    button_label = "Download PDF"
                    st.download_button(label=button_label, data=PDFbyte, file_name="course.pdf", mime="application/octet-stream", key="download_pdf_button")

                    break

                
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
                    

        
                    for module_name, lessons in module_lessons.items():
                        module_content = ""

                        # Loop through lessons in each module
                        for lesson_name in lessons:
                            module_lesson_prompt = f"""You are Coursify, an AI assistant specialized in generating high-quality educational content for online courses. Your knowledge spans a wide range of academic and professional domains, allowing you to create in-depth and engaging material on any given topic. For this task, you will be generating detailed content for the lesson '{lesson_name}' which is part of the module '{module_name}' in the course '{course_name}'. Your goal is to provide a comprehensive and learner-friendly exploration of this specific topic, covering all relevant concepts, theories, and practical applications, as if you were an experienced instructor teaching the material.

                            To ensure the content is effective and aligns with best practices in instructional design, you will follow Bloom's Taxonomy approach. This means structuring the material in a way that progressively builds learners' knowledge and skills, starting from foundational concepts and working up to higher-order thinking and application. Your response should be verbose, with in-depth explanations, multiple examples, and a conversational tone that mimics an instructor's teaching style.

                            The structure of your response should include (but NOT limited to) the following elements:

                            1) Introduce the topic and provide context, explaining its relevance and importance within the broader course and domain, as an instructor would do in a classroom setting.
                            2) Define and clarify key terms, concepts, and principles related to the topic, with detailed explanations, analogies, and examples to aid comprehension.
                            3) Present thorough, step-by-step explanations of the concepts, using real-world scenarios, visual aids, and analogies to ensure learners grasp the material.
                            4) Discuss real-world applications, case studies, or scenarios that demonstrate the practical implications of the topic, drawing from industry best practices and authoritative sources.
                            5) Incorporate interactive elements, such as reflective questions, exercises, or problem-solving activities, to engage learners and reinforce their understanding, as an instructor would do in a classroom.
                            6) Seamlessly integrate relevant tangential concepts or background information as needed to provide a well-rounded learning experience, ensuring learners have the necessary foundational knowledge.
                            7) Maintain a conversational, approachable tone while ensuring accuracy and depth of content, as if you were an experienced instructor teaching the material.

                            Remember, the goal is to create a comprehensive and self-contained learning resource on the specified topic, with the level of detail and instructional quality that one would expect from an expert instructor. Your output should be formatted using Markdown for clarity and easy integration into course platforms.
                            Note: Add a blank line at the end of the course content.
                            Make sure the content generated is easily convertible to a sensible using HTML Tags.
                            """
                            
                            with st.spinner(f"Generating content for {module_name}, {lesson_name}"):
                                response = chat.send_message(module_lesson_prompt)
                                complete_course = response.text
                                
                                st.success(f"Generated content for {module_name}, {lesson_name}")
                                
                                with st.expander("Click to view!"):
                                    st.write(complete_course)
                                
                                module_content += complete_course + "\n\n"

                    

                        # Generate the PDF if not already created
                        if "pdf" not in st.session_state:
                            complete_course_content = module_content 
                            st.session_state.pdf = generate_pdf(complete_course_content, "course.pdf")
                            b64 = base64.b64encode(st.session_state.pdf.output(dest="S").encode("latin1")).decode()
                            st.success("Your PDF file is ready!")

                        # Provide download button for the PDF
                        button_label = "Download PDF"
                        st.download_button(label=button_label, data=b64, file_name="course.pdf", mime="application/pdf", key="download_pdf_button")

                        break

    else:
        st.write("Your generated content will appear here.")

# Save chat history after each interaction
save_chat_history(st.session_state.messages)
