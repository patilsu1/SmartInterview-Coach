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

    if file_type == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif file_type == "docx":
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    elif file_type == "pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

    elif file_type == "doc":
        return textract.process(file_path).decode("utf-8")

    else:
        return "Unsupported file format."


@cl.on_chat_start
async def start():
    await cl.Message(content="Welcome to **Smart Interview Coach**!").send()
    await cl.Message(content="Please upload your **resume** and **job description** (as text files).").send()
    files = None
 # Wait for the user to upload a file
    while files == None:
        files = await cl.AskFileMessage(
            content="Please upload a Resume file to begin!", accept=["text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/msword", "application/pdf"]
        ).send()

    resume_file = files[0]

   # with open(resume_file.path, "r", encoding="utf-8") as f:
 
    resume_text = await read_file(resume_file.path)
        # resume_text = f.read()

    # Let the user know that the system is ready
    await cl.Message(
        content=f"`{resume_file.name}` uploaded, it contains {len(resume_text)} characters!"
    ).send()

    files = None
    # Wait for the user to upload a file
    while files == None:
        files = await cl.AskFileMessage(
            content="Please upload a JD file to begin!",  accept=["text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword", "application/pdf"]
        ).send()

    jd_file = files[0]

   # with open(jd_file.path, "r", encoding="utf-8") as f:
   #     job_description = f.read()
    job_description = await read_file(jd_file.path)
    # Let the user know that the system is ready
    await cl.Message(
        content=f"`{jd_file.name}` uploaded, it contains {len(job_description)} characters!"
    ).send()



    # Remove the decode calls as the path is already a string
   # resume_text = resume_file.path
    #job_description = jd_file.path

    await cl.Message(content="Analyzing your resume and job description...").send()

    prompt = f"""
You are an expert interview coach. Given the resume and job description below, provide:

1. A list of missing or weakly represented skills in the resume
2. Suggested edits to the resume (bullet points, phrasing, etc.)
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
                {"role": "system", "content": "You are a helpful AI interview coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            top_p=1.0
        )
        output = response.choices[0].message.content
       # output = response['choices'][0]['message']['content']
        await cl.Message(content=output).send()

    except Exception as e:
        await cl.Message(content=f"Error: {e}").send()