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

def generate_questions(resume_data_json, focus_count, past_questions_list):
    prompt = f"""You are a technical interviewer. Based on this resume, generate an interview question
                Focused on one SINGLE element/experience from their resume 

                IMPORTANT RULES:
                - Whatever you do, DO NOT exceed 3 uses per focus area for current counts. If the current count is 3, do not use that focus area
                - Select EXACTLY 3 focus areas
                - Prioritize focus areas that have been used LESS than 3 times
                - Focus areas must come ONLY from the provided list
                - Try not to ask repeated/related questions to those that were already asked

                Resume:
                {resume_data_json}

                Focus areas and current counts:
                {focus_count}

                Past Questions List:
                {past_questions_list}


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

def to_json(txt):
    match = re.search(r"\{.*}", txt, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(0))


def generate_feedback(question_answer_json, question_json, rubric_areas, focus_areas):
    prompt = f"""You are a senior technical interviewer. Evaluate the canidates answer using the following crieteria

                SCORING INSTRUCTIONS:
                - score each rubric area from 0 to 10 (ints only)
                - be VERY strict and consistent 
                - do not give all high scores unless clearly justified

                FOCUS AREA FEEDBACK INSTRUCTIONS:
                - give feedback to the interviewe about their answers
                - specifically give feedback about how they met the focus areas
                - allways mention something they did well and how they can improve
                - use "you" and other nouns like that. like you are directly talking to them
                - keep it 1 sentence that is max 40 words

                Rubric Areas:
                {rubric_areas}

                Question:
                {question_json}

                Answer:
                {question_answer_json}

                Focus Areas:
                {focus_areas}

                MUST return JSON in this format:
                {{
                    "scores": [score 1, score 2, score 3, score 4, score 5],
                    "focus_areas": ["feedback bullet for focus area 1", "feedback bullet for focus area 2", "feedback bullet for focus area 3"]
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
    
    
if __name__=="__main__":
    with open("sample.json", "r") as f:
        resume_data = f.read()

    questions = generate_questions(resume_data)
    print(questions)
