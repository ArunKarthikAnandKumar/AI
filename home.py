import streamlit as st
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="Automated Course Content Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Display the header with an emoji icon and title
st.title("🚀 Welcome to the **Automated Course Content Generator** 🤖")
st.write(
    """
    🌟 **Unlock the Future of Course Creation** 🌟
    Effortlessly generate comprehensive course outlines and content with the power of AI! Whether you're an educator, trainer, or content creator, this app is designed to streamline your course development process by:
    - **Generating custom course content** based on your input
    - **Analyzing PDFs** to create structured lessons
    - **Saving time** on research and content structuring
    """
)

# Add a welcome image or logo (optional)
# Uncomment if you have a logo image file, like `logo.png`
# image = Image.open("logo.png")
# st.image(image, use_column_width=True)

# Section 1: Overview
st.header("📘 **Course Overview**")
st.write(
    """
    The **Automated Course Content Generator** leverages advanced AI to create structured, engaging, and comprehensive course materials. Perfect for:
    - **Educators** who want to save time and create tailored course content
    - **Trainers** looking for a more efficient way to structure educational programs
    - **Content creators** aiming to generate engaging, well-organized course outlines with ease
    
    With this tool, you can quickly generate content for any topic, at any difficulty level, and for any audience. 🌍
    """
)

# Section 2: Features
st.header("✨ **Key Features**")
st.markdown(
    """
    - **Prompt-Based Course Generation**: Set parameters such as course difficulty, target audience, and learning objectives, and let the AI generate a personalized course outline for you.
    - **PDF-Based Course Generation**: Upload any PDF, and watch as the AI extracts and organizes the document's information into a structured course framework.
    - **Easy Customization**: Once the AI generates the course, you can modify the content to suit your style and needs, making it fully customizable.
    
    Whether you're building an introductory course or an advanced module, this tool adapts to your requirements. 🌟
    """
)

# Section 3: Get Started
st.header("🚀 **Get Started**")
st.write(
    """
    Ready to start creating course content? Here’s how you can get started:
    
    1. **Prompt-Based Course Generation**: 
        - Choose this option if you want to define key details about your course (e.g., difficulty, target audience) and let the AI generate the course structure for you.
    
    2. **PDF-Based Course Generation**: 
        - Upload a PDF document and watch as the AI intelligently breaks down the content to create an organized course outline based on the material.

    The power to create high-quality educational content is at your fingertips. Let’s build something amazing! 💡
    """
)
