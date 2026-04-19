import sys 
import json 
import streamlit as st
import tempfile
import time
from resume_parse import parse_resume
from generator import question_to_json, generate_feedback, generate_questions

FOCUS_AREAS = [
    "Product Thinking",
    "Ownership",
    "Technical Depth",
    "System Thinking",
    "Tradeoff Awareness",
    "Execution and Impact",
    "Communication",
    "Learning and Growth",
    "Scalability and Performance Awareness",
    "Collaboration"
]

COLOR_MAP = {
    "Product Thinking": "#C86161",
    "Ownership": "#DA864F",
    "Technical Depth": "#D8CF89",
    "System Thinking": "#B8CA88",
    "Tradeoff Awareness": "#67B988",
    "Execution and Impact": "#6CB8A7",
    "Communication": "#8888DC",
    "Learning and Growth": "#A36FC1",
    "Scalability and Performance Awareness": "#CF64CF",
    "Collaboration": "#D06C94"
}

def focus_tags_disp(focus_list):
    focus_list = [f.strip() for f in focus_list]
    columns = st.columns(len(focus_list))

    for i, focus in enumerate(focus_list):
        color = COLOR_MAP.get(focus)

        columns[i].markdown(
            f"""
            <div style="
                background-color: {color};
                padding: 6px 12px;
                border-radius: 20px;
                text-align: center;
                font-weight: 600;
                color: white;
                font-size: 14px;
            ">
                {focus}
            </div>
            """,
            unsafe_allow_html=True
        )

if "stage" not in st.session_state:
    st.session_state.stage = "upload"
    st.session_state.json_str = ""
    st.session_state.question = ""
    st.session_state.focus = []
    st.session_state.question_to_json = ""
    st.session_state.answer = ""
    st.session_state.answer_to_json = ""
    st.session_state.history = []
    st.session_state.pending = None
    st.session_state.validation = {}
    st.session_state.topic_list = {area: 0 for area in FOCUS_AREAS}


st.title("Interview Simulator Practice")

for item in st.session_state.history:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

if st.session_state.stage == "answer":
    focus_tags_disp(st.session_state.focus)

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
    question = generate_questions(st.session_state.json_str, st.session_state.topic_list)
    
    print(question)

    st.session_state.question_json = question_to_json(question)
    st.session_state.question = st.session_state.question_json["question"]
    st.session_state.focus = st.session_state.question_json["focus_areas"]


    # st.write("DEBUG:", st.session_state.question_json)
    # st.write("TYPE:", type(st.session_state.question_json))

    for focus in st.session_state.focus:
        if focus in st.session_state.topic_list:
            st.session_state.topic_list[focus] += 1

    st.session_state.history.append({"role": "assistant", "content": st.session_state.question})
    

    st.session_state.stage = "answer"
    st.rerun()
 

elif st.session_state.stage == "answer":
    if answer := st.chat_input("Provide your best answer to the following question:"):
        st.session_state.answer = answer
        st.session_state.answer_json = json.dumps(answer, indent=4)

        st.session_state.history.append({"role": "user", "content": st.session_state.answer})

        st.session_state.stage = "feedback"
        st.rerun()


elif st.session_state.stage == "feedback":
    feedback = generate_feedback(st.session_state.answer_json, st.session_state.question_json)
    print(feedback)
    st.session_state.history.append({"role": "assistant", "content":feedback})
    st.session_state.stage =  "wait"

    st.rerun()

    
elif st.session_state.stage == "wait":
    if st.button("Got it!!", use_container_width=True):
        st.session_state.stage = "question"
        st.rerun()