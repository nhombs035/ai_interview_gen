import sys 
import json 
import streamlit as st
import tempfile
import time
from resume_parse import parse_resume
from generator import to_json, generate_feedback, generate_questions


## INITIALIZATION of set lists 
RUBRIC_AREAS = [
    "Problem Understanding",
    "Algorithm and Approach",
    "Technical Depth",
    "Communication Clarity"
]


FOCUS_AREAS = [
    "Product Thinking",
    "Ownership",
    "Technical Depth",
    "System Thinking",
    "Tradeoff Awareness",
    "Execution and Impact",
    "Communication",
    "Learning and Growth",
    "Performance Awareness",
    "Collaboration"
]

COLOR_MAP = {
    "Product Thinking": "#C86161",
    "Ownership": "#DA864F",
    "Technical Depth": "#948E5F",
    "System Thinking": "#7B865C",
    "Tradeoff Awareness": "#589470",
    "Execution and Impact": "#5A9084",
    "Communication": "#8888DC",
    "Learning and Growth": "#A36FC1",
    "Performance Awareness": "#CF64CF",
    "Collaboration": "#D06C94"
}

## Custom tag/fake buttons for topic selection
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

## INITIALIZE session state variables
if "stage" not in st.session_state:
    st.session_state.stage = "upload"

    st.session_state.json_str = ""

    st.session_state.question = ""
    st.session_state.question_to_json = ""

    st.session_state.focus = []
    st.session_state.topic_list = {area: 0 for area in FOCUS_AREAS}

    st.session_state.answer = ""
    st.session_state.answer_to_json = ""

    st.session_state.feedback_to_json = ""
    st.session_state.scores = []
    st.session_state.focus_scores = []

    st.session_state.q_history = []

    st.session_state.history = []
    st.session_state.pending = None
    st.session_state.validation = {}

    st.session_state.total_q = 0



## PAGE SET UP

if st.sidebar.button ("Restart Interview"):
    st.session_state.clear()
    st.rerun()

st.sidebar.divider()

st.title("Interview Simulator Practice")

## add stats and sidebar menu
st.sidebar.title("Interview Progress: ")
st.sidebar.write("You have reached " + str(st.session_state.total_q) + " out of 10 available questions" )
percent = st.session_state.total_q/10
st.sidebar.progress(percent)

st.sidebar.title("Performance Stats: ")

st.sidebar.title("Focus Area Progress: ")
for topic, progress in st.session_state.topic_list.items():
    st.sidebar.write(topic)
    percent = progress/3 
    st.sidebar.progress(percent)


## PRINT CONVO
for item in st.session_state.history:
    
    if item["role"] == "feedback":
        st.chat_message("assistant").write("Thank you for your response! Grading and providing feedback now!")
        feedback_json = item["content"]

        st.session_state.scores = feedback_json["scores"]
        st.session_state.focus_scores = feedback_json["focus_areas"]

        st.write("TOTAL SCORE: " + str(sum(st.session_state.scores)) + "/40")
        st.progress( sum(st.session_state.scores) / 40)

        st.write("\n")

        cols1 = st.columns(2)
        for i in range(2):
            with cols1[i]:
                progress = st.session_state.scores[i]
                st.write(RUBRIC_AREAS[i] + ": " + str(progress) + "/10")
                percent = progress/10
                st.progress(percent)

        cols2 = st.columns(2)
        for i in range(2):
            with cols2[i]:
                idx = i + 2
                progress = st.session_state.scores[idx]
                st.write(RUBRIC_AREAS[idx] + ": " + str(progress) + "/10")
                percent = progress/10
                st.progress(percent)

        st.write("\n")

        for item in st.session_state.focus_scores:
            st.write(f"- {item}")

        st.write("\n")

    elif item["role"] == "focus":
        focus_tags_disp(item["content"])
        st.divider()


    else: 
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

        if (item["role"]) == "user":
            st.divider()
    
################################# STATES #######################################

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
    st.session_state.total_q += 1

    question = generate_questions(st.session_state.json_str, st.session_state.topic_list, st.session_state.q_history)
    
    print(question)

    st.session_state.question_json = to_json(question)
    st.session_state.question = st.session_state.question_json["question"]
    st.session_state.focus = st.session_state.question_json["focus_areas"]


    # st.write("DEBUG:", st.session_state.question_json)
    # st.write("TYPE:", type(st.session_state.question_json))

    st.session_state.history.append({"role": "assistant", "content": st.session_state.question})
    st.session_state.history.append({"role": "focus", "content": st.session_state.focus})
    st.session_state.q_history.append(st.session_state.question)

    st.session_state.stage = "answer"
    st.rerun()
 

elif st.session_state.stage == "answer":
    if answer := st.chat_input("Provide your best answer to the following question:"):
        st.session_state.answer = answer
        st.session_state.answer_json = json.dumps(answer, indent=4)

        st.session_state.history.append({"role": "user", "content": st.session_state.answer})
        

        for focus in st.session_state.focus:
            if focus in st.session_state.topic_list:
                st.session_state.topic_list[focus] += 1

        st.session_state.stage = "feedback"
        st.rerun()


elif st.session_state.stage == "feedback":
    feedback = generate_feedback(st.session_state.answer_json, st.session_state.question_json, RUBRIC_AREAS, st.session_state.focus)
    print(feedback)
    
    st.feedback_to_json = to_json(feedback)

    st.session_state.history.append({"role": "feedback", "content":st.feedback_to_json})
    st.session_state.stage =  "wait"

    st.rerun()

    
elif st.session_state.stage == "wait":
    if st.button("Got it!! Next Question!", use_container_width=True):
        st.session_state.stage = "question"
        st.rerun()