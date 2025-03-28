import pdfplumber
import os
from dotenv import load_dotenv
import openai
import streamlit as st


# Load environment variables
load_dotenv()

# cv_path = st.session_state.cv_path
cv_path = r"D:\Job Automation Bot\temp\Resume.pdf"


class textExtractor:
    def __init__(self,cv_path):
        self.cv_path=cv_path
    def extract_cv_text(self):
        cv_path = self.cv_path
        """Extracts text from a PDF CV."""
        with pdfplumber.open(cv_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        return text  # Strip extra spaces/newlines


# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
class CVBot:
    def __init__(self, cv_text,question,options=None):
        self.cv_text=cv_text
        self.options=options
        self.question=question

    def query_gpt(self):
        cv_text = self.cv_text
        options = self.options
        question = self.question

        """Generates an answer based on the given question and CV text."""

        prompt = f"""
            You are a CV analysis expert. Your task is to extract or infer answers to given questions based on the CV text provided. 

            ### **Instructions:**
            1. **Detect answer type:**
            - If the question is about **experience, salary, years, age,notice period,education or any numerical data**, return an **integer** (default to `0` if not found).
            - Otherwise, return a **short text answer**.
            
            2. **Answering the question:**
            - If the answer exists in the CV, return it.
            - If not found:
                - Return `"N/A"` for text-based questions.
                - Return `0` for numerical questions (like `experience in years`, `salary`,`Notice period`,`Education`,`Amount`,`Experience` etc.).
            
            3. **Handling Multiple-choice Questions:**
            - If **options are provided**, return the closest matching answer from the option.
            - If no exact match is found in the CV, return random answer from the option.
            - **question** = Location (city), return Dhaka, Bangladesh

            4.**Handel Phone Numbers:**
            - If the question asks for a phone number and options are provided (like +1, +91, +44, +33, +880), return only from the given options.
            - If the question is about **phone number**, return the phone number without country code.
            
            5.**Handel Location**:
            - If question is in {default} return answer.

            ---

            ### **CV TEXT:**
            {cv_text}

            ### **QUESTION:**
            {question}

            ### **OPTIONS:**
            {options}

            ### default:**
            {default}

            ### **ANSWER:**
            """

        response = openai.chat.completions.create(  #  Correct new API call
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a CV analysis expert. Answer accurately and concisely."},
                {"role": "user", "content": prompt}
            ]
        )
        # response.choices[0].message.content.strip()
        # cv_text = extract_cv_text(cv_path)
        # gpt = CVBot(cv_text,question,options)
        # answer = gpt.query_gpt()

        raw_output = response.choices[0].message.content.strip()
        clean_output = raw_output.strip("'")  # Remove double single quotes if present
        return clean_output

default = {
    "Location (city)": "Dhaka, Bangladesh",
    "Location (country)": "Bangladesh",
    "Location (state)": "Dhaka",}

# cv_text = extract_cv_text(cv_path)
# question = "do you have right to work in the applying country?"
# gpt = CVBot(cv_text,question,options=["yes","no"])
# answer = gpt.query_gpt()
# print(answer)

# text = textExtractor(cv_path).extract_cv_text()
# question = "how many years of experience do you have in python?"
# options = ["0,1,2,3"]

# gpt = CVBot(text, question, options)
# answer = gpt.query_gpt()
# print(answer)

class ask_query():
    def __init__(self,question,options=None):
        self.question=question
        self.options=options

    def ask(self):
        question = self.question
        options=self.options
        text=textExtractor(cv_path).extract_cv_text()
        response = CVBot(text,question,options).query_gpt()
        return response

question = "Location(city)"
# options=["Bangladesh (+880)","India (+91)","America (+1)"]

answer = ask_query(question,options=None).ask()
print(answer)

