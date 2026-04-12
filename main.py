import sys 
import json 
from resume_parse import parse_resume
from generator import question_to_json, generate_feedback, generate_questions


if __name__ == "__main__":

    print("file is being read...")
    file_path = sys.argv[1]
    parsed_text = parse_resume(file_path)
    # print(parsed_text)
    json_str = json.dumps(parsed_text, indent=4)

    print("file is read. \nquesions being generated...")
    question = generate_questions(json_str)
    print(question)

    answer = input("Enter answer to response: ")
    answer_json = json.dumps(answer, indent=4)

    question_json = question_to_json(question)

    feedback = generate_feedback(answer_json, question_json)
    print(feedback)

    


    