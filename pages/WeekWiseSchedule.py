import streamlit as st
from PyPDF2 import PdfReader
from fpdf import FPDF
import unicodedata
import base64
import os
import google.generativeai as genai
from google.generativeai import GenerativeModel
from dotenv import load_dotenv

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

# Function to parse PDF content
def parse_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

# Function to generate a structured PDF file
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

# Function to provide a download button for the generated PDF
def download_pdf(pdf_filename):
    with open(pdf_filename, "rb") as pdf_file:
        pdf_data = pdf_file.read()
        st.download_button(
            label="Download formatted PDF",
            data=pdf_data,
            file_name=pdf_filename,
            mime="application/pdf"
        )

# Set up the Streamlit page
st.set_page_config(page_title="Generate Course Outline From PDF", layout="wide")
st.title("Generate Course Outline From PDF 📝")

# PDF file upload
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
if uploaded_file is not None:
    parsed_text = parse_pdf(uploaded_file)
    st.session_state["parsed_text"] = parsed_text
    st.success("PDF parsed successfully!")

    # Structure the content based on provided prompt
    structure_prompt = f"""
    You are an AI assistant. The input content is a raw parsed text from a PDF document. Your task is to restructure this text into a formal, well-organized format with the following specific sections. Follow this structure strictly:

    **Course Code and Course Title**: Clearly extract or identify the course code and title from the content.
    
    **Pre-requisite**: Identify and mention any prerequisite knowledge required for the course if mentioned in the content.
    
    **Syllabus Version**: Indicate the version of the syllabus if available in the content.
    
    **Total Lecture Hours**: Calculate and sum up the total lecture hours mentioned across all modules in the content.
    
    **Course Objectives**: Extract a concise list of objectives capturing the main learning goals of the course.
    
    **Course Outcomes**: List the anticipated learning outcomes, focusing on skills and competencies that students should acquire after completing the course.
    
    **Module Structure**: Present each module in the following detailed format:
       - **Module [Module Number]: [Module Name] - [Number of Hours]**
         - **Content**: Provide a list of subtopics for each module, covering essential areas. Aim for 4-10 subtopics based on the module's complexity. Use the following format as an example:
           - *Module 1: Introduction - 5 hours*
             - High-Performance Computing Disciplines
             - Impact of Supercomputing on Science, Society, and Security
             - Anatomy of a Supercomputer
             - Computer Performance
             - A Brief History of Supercomputing
             
    **Textbooks**: Extract a list of primary textbooks with authors and publication details.
    
    **Reference Books**: Provide a list of additional reference materials or suggested readings, including authors and publication details.

    Here's the input text to restructure:
    {st.session_state['parsed_text']}
    
    Please maintain the same content and meaning but organize it strictly in the specified format. Ensure all sections are covered, even if they need to be inferred from the provided content.
    """

    # Trigger the content formatting
    if st.button("Format The PDF"):
        with st.spinner("Formatting content..."):
            try:
                # Sending the restructuring prompt to the Generative AI model
                response = chat.send_message(structure_prompt)
                formatted_content = response.text

                # Check if formatted content was received
                if formatted_content:
                    st.session_state["formatted_content"] = formatted_content
                    st.success("Content formatted successfully! 🎉")

                    # Display formatted content in an expander
                    with st.expander("Formatted Content"):
                        st.write(formatted_content)
                    
                    # Save formatted content as a PDF
                    pdf_filename = "formatted_content.pdf"
                    generate_pdf(st.session_state["formatted_content"], pdf_filename)

                    # Provide download button for the generated PDF
                    download_pdf(pdf_filename)
                else:
                    st.error("Failed to generate formatted content. Please try again.")

            except Exception as e:
                st.error(f"An error occurred while structuring the content: {e}")
