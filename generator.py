from openai import OpenAI, RateLimitError
from dotenv import load_dotenv
import json
import os
import time
import re


load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPEN_API_KEY")
)

def generate_questions(resume_data_json, focus_count):
    prompt = f"""You are a technical interviewer. Based on this resume, generate an interview question
                Focused on one SINGLE element/experience from their resume 

                IMPORTANT RULES:
                - Select EXACTLY 3 focus areas
                - Prioritize focus areas that have been used LESS than 3 times
                - Do NOT exceed 3 uses per focus area unless necessary
                - Focus areas must come ONLY from the provided list

                Resume:
                {resume_data_json}

                Focus areas and current counts:
                {focus_count}


                MUST return JSON in this format:
                {{
                    "question": "...",
                    "focus_areas": ["focus 1", "focus 2", "focus 3"]
                }}
                """

    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                        model="google/gemini-2.0-flash-lite-001",
                        messages = [{"role": "user", "content": prompt}]
                        )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt < 4:
                print(f"Rate limited, retrying in {10 * (attempt + 1)}s...")
                time.sleep(10 * (attempt + 1))
            else:
                raise

def question_to_json(question_txt):
    match = re.search(r"\{.*}", question_txt, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(0))


def generate_feedback(question_answer_json, question_json):
    prompt = f"""You are a technical interviewer. Based on this question and it's rational, generate an interview question
                feedback. 

                Question:
                {question_json}

                Answer:
                {question_answer_json}

                Include structured feedback and score out of 10."""
    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                        model="google/gemini-2.0-flash-lite-001",
                        messages = [{"role": "user", "content": prompt}]
                        )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt < 4:
                print(f"Rate limited, retrying in {10 * (attempt + 1)}s...")
                time.sleep(10 * (attempt + 1))
            else:
                raise
    
    
if __name__=="__main__":
    with open("sample.json", "r") as f:
        resume_data = f.read()

    questions = generate_questions(resume_data)
    print(questions)
