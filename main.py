import sys 
import json 
import streamlit as st
import tempfile
import time
from resume_parse import parse_resume
from generator import question_to_json, generate_feedback, generate_questions

def print_hist():
    for item in st.session_state.history:
        role = item["role"]
        content = item["content"]

        with st.chat_message(role):
            st.write(content)

if "stage" not in st.session_state:
    st.session_state.stage = "upload"
    st.session_state.json_str = ""
    st.session_state.question = ""
    st.session_state.question_to_json = ""
    st.session_state.answer = ""
    st.session_state.answer_to_json = ""
    st.session_state.history = []
    st.session_state.pending = None
    st.session_state.validation = {}


st.title("Interview Simulator Practice")

if st.session_state.stage == "upload":
    print("file is being read...")
    file_object = st.file_uploader("Please select an input resume: ")
    # file_path = sys.argv[1]

    file_path = ""
    if file_object is not None:
        suffix = ".pdf" if file_object.name.endswith(".pdf") else ".docx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_object.read())
            file_path = tmp.name
    
        if file_path is not None:

            parsed_text = parse_resume(file_path)
            st.write("Resume Successfully Uploaded!")
            time.sleep(1)
            # print(parsed_text)
            st.session_state.json_str = json.dumps(parsed_text, indent=4)

            st.write("Resume is being read...")
            time.sleep(1)
            st.write("Please wait while we generate questions...")
            print("file is read. \nquesions being generated...")

            st.session_state.stage = "question"
            st.rerun()

elif st.session_state.stage == "question":
    print_hist()
    st.session_state.question = generate_questions(st.session_state.json_str)
    print(st.session_state.question)

    st.session_state.history.append({"role": "assistant", "content": st.session_state.question})
    st.chat_message("assistant").write(st.session_state.question)
    st.session_state.question_json = question_to_json(st.session_state.question)

    st.session_state.stage = "answer"


    st.rerun()
 

elif st.session_state.stage == "answer":
    print_hist()
    if answer := st.chat_input("Provide your best answer to the following question:"):
        st.session_state.answer = answer
        st.session_state.answer_json = json.dumps(answer, indent=4)

        st.session_state.history.append({"role": "user", "content": st.session_state.answer})

        st.session_state.stage = "feedback"
        st.rerun()


elif st.session_state.stage == "feedback":
    print_hist()
    feedback = generate_feedback(st.session_state.answer_json, st.session_state.question_json)
    print(feedback)
    st.chat_message("assistant").write(feedback)
    st.session_state.history.append({"role": "assistant", "content":feedback})
    st.session_state.stage =  "question"

    if st.button("Got it!!", width="stretch"):
        st.rerun()

    


        