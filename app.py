import chainlit as cl
import docx
import PyPDF2
import textract
import os
from openai import OpenAI
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


# Set your OpenAI API Key
token = os.getenv("OPENAI_API_KEY")
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)
async def read_file(file_path):
    file_type = file_path.split('.')[-1].lower()

    if (file_type == "txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif (file_type == "docx"):
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    elif (file_type == "pdf"):
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

    elif (file_type == "doc"):
        return textract.process(file_path).decode("utf-8")

    else:
        return "Unsupported file format."

async def handle_follow_up_question(user_question, resume_text, job_description):
    """ Allows users to ask additional questions about the job/interview """
        
    prompt = f"""
    The user has uploaded their resume and job description and received initial interview coaching.
    Now, they have asked a follow-up question:

    **User's Question:** {user_question}

    Please provide a helpful response based on the job description and resume.

    Resume:
    {resume_text}

    Job Description:
    {job_description}
    """

    response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a AI interview coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            top_p=1.0
        )
    return response.choices[0].message.content


@cl.on_chat_start
async def start():
    await cl.Message(content="Welcome to **Smart Interview Coach**! I am An AI-powered interview assistant that analyzes resumes and job descriptions to identify missing skills, suggest improvements, generate tailored interview questions, and provide STAR-format sample answers for effective preparation").send()
    files = None
 # Wait for the user to upload a file
    while files == None:
        files = await cl.AskFileMessage(
            content="Please upload a Resume file to begin!", accept=["text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/msword", "application/pdf"]
        ).send()

    resume_file = files[0]

    # Read the resume file
    resume_text = await read_file(resume_file.path)
        # resume_text = f.read()

 
    files = None
    # Wait for the user to upload a file
    while files == None:
        files = await cl.AskFileMessage(
            content="Please upload a Job description file to begin!",  accept=["text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword", "application/pdf"]
        ).send()

    jd_file = files[0]

  
    job_description = await read_file(jd_file.path)
   

    await cl.Message(content="Analyzing your resume and job description...").send()

    prompt = f"""
You are an expert interview coach. Given the resume and job description below, provide:

1. Can you please tell if this job is great fit from the resume perspective
2. A list of missing or weakly represented skills in the resume
3. Suggested edits to the resume (bullet points, phrasing, etc.)
3. Five tailored behavioral or role-specific interview questions
4. STAR-format sample answers based on the resume content

Resume:
{resume_text}

Job Description:
{job_description}
"""

    try:
        # Fixed unclosed parenthesis and corrected the client usage
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a AI interview coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            top_p=1.0
        )
        output = response.choices[0].message.content
        # Send the response to the user
        await cl.Message(content=output).send()
        
        # Ask the user if they have any follow-up questions
        count = 0
        while count < 5: 
            user_message = await cl.AskUserMessage(content="Do you have any other question").send()
            # Handle follow-up user questions
            follow_up_response = await handle_follow_up_question(user_message['output'], resume_text, job_description)
            await cl.Message(content=follow_up_response).send()
            count += 1


    except Exception as e:
        await cl.Message(content=f"Error: {e}").send()
