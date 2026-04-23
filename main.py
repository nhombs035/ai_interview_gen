import sys 
import json 
import streamlit as st
import tempfile
import time
from resume_parse import parse_resume
from generator import to_json, generate_feedback, generate_questions


######################################## GLOBAL LIST INITALIZATIONS ############################################

# Standardized rubric grading areas to grade each question
RUBRIC_AREAS = [
    "Problem Understanding",
    "Algorithm and Approach",
    "Technical Depth",
    "Communication Clarity"
]

# Technical areas that questions are generated from 
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

# Color maping for each focus area to easily recognize
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

# Custom tag/fake buttons for topic selection to display under each question
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

########################################### INITIALIZE session state variables #####################################################
# these are reset with each interview simulater restart and each new session
if "stage" not in st.session_state:
    # contains state machine label
    st.session_state.stage = "upload"

    # json string for resume output
    st.session_state.json_str = ""

    # question storage variables 
    st.session_state.question = ""
    st.session_state.question_to_json = ""

    # focus / topic lsit storage 
    st.session_state.focus = []
    st.session_state.topic_list = {area: 0 for area in FOCUS_AREAS}

    # answer storage variables 
    st.session_state.answer = ""
    st.session_state.answer_to_json = ""

    # feedback and score storage variables 
    st.session_state.feedback_to_json = ""
    st.session_state.scores = []
    st.session_state.focus_scores = []
    st.session_state.total_scores = []

    # question hsitory to ensure no repeat experience questions
    st.session_state.q_history = []

    # general history to allow for question navigation 
    st.session_state.history = []

    # question indexing variables
    st.session_state.total_q = 0
    st.session_state.q_cur = 0 # describes current question view for navigation


########################################################### FRONT END INITIALIZATION #######################################################
st.title("Interview Simulator Practice")

############## End of interview session summary page 
if st.session_state.total_q == 10: # marks end of interview 
    st.title("You have completed the interview!")
    st.write("Here are your final performance statistics")

    st.session_state.stage = "done"
    st.session_state.q_history = []
    st.session_state.history = []

    total_scores = st.session_state.total_scores[0:st.session_state.total_q + 1]

    avg = []
    for i in range(4):
        col_sum = sum(row[i] for row in total_scores)
        avg.append(col_sum / len(total_scores))
    
    total_avg = 0
    for i in total_scores:
        total_avg += sum(i)
    total_avg /= (len(total_scores))
    percent_2 = total_avg/40
    
    st.write("TOTAL AVERAGE SCORE: " + str(int(total_avg)) + "/40")
    st.progress( sum(st.session_state.scores) / 40)

    st.write("\n")

    cols1 = st.columns(2)
    for i in range(2):
        with cols1[i]:
            progress = avg[i]
            st.write(RUBRIC_AREAS[i] + ": " + str(int(progress)) + "/10")
            percent = progress/10
            st.progress(percent)

    cols2 = st.columns(2)
    for i in range(2):
        with cols2[i]:
            idx = i + 2
            progress = avg[idx]
            st.write(RUBRIC_AREAS[idx] + ": " + str(int(progress)) + "/10")
            percent = progress/10
            st.progress(percent)
    
    st.divider()

    if st.button ("Restart Interview Session"):
        st.session_state.clear()
        st.rerun()

########### In session page (default page)
if len(st.session_state.history) != 0 and st.session_state.stage != "question":

    st.title("Question " + str(st.session_state.q_cur + 1))
    history = st.session_state.history[st.session_state.q_cur]

    for item in history:
        
        if item["role"] == "feedback" and item["content"] is not None:
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
            if item["content"] is not None:
                with st.chat_message(item["role"]):
                    st.markdown(item["content"])

                if (item["role"]) == "user":
                    st.divider()

######## Side bar set up 
with st.sidebar:
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button ("Previous"):
            st.session_state.q_cur = max(st.session_state.q_cur - 1 , 0)
            st.rerun()

    with col2:
        if st.button ("Restart"):
            st.session_state.clear()
            st.rerun()
        
    with col3:
        max_q_idx = len(st.session_state.history) - 1
        if st.button ("Next"):
            st.session_state.q_cur = min(st.session_state.q_cur + 1 , max_q_idx)
            st.rerun()

st.sidebar.divider()


## add stats and sidebar menu
st.sidebar.title("Interview Progress: ")
st.sidebar.write("You have answered " + str(st.session_state.total_q) + " out of 10 interview questions" )
percent = st.session_state.total_q/10
st.sidebar.progress(percent)

st.sidebar.title("Performance Stats: ")

if len(st.session_state.total_scores) != 0:
    total_scores = st.session_state.total_scores[0:st.session_state.total_q + 1]
    avg = []
    for i in range(4):
        col_sum = sum(row[i] for row in total_scores)
        avg.append(col_sum / len(total_scores))
    
    total_avg = 0
    for i in total_scores:
        total_avg += sum(i)
    total_avg /= (len(total_scores))
    percent_2 = total_avg/40

else:
    avg = [0, 0, 0, 0]
    total_avg = 0
    percent_2 = 0

st.sidebar.write("Total Score Average: " + str(int(total_avg)) + "/40")
st.sidebar.progress(percent_2)

with st.sidebar:
    cols1 = st.columns(2)
    for i in range(2):
        with cols1[i]:
            progress = avg[i]
            st.write(RUBRIC_AREAS[i] + " Average: " + str(int(progress)) + "/10")
            percent = progress/10
            st.progress(percent)

    cols2 = st.columns(2)
    for i in range(2):
        with cols2[i]:
            idx = i + 2
            progress = avg[idx]
            st.write(RUBRIC_AREAS[idx] + " Average: " + str(int(progress)) + "/10")
            percent = progress/10
            st.progress(percent)

st.sidebar.title("Focus Area Progress: ")
for topic, progress in st.session_state.topic_list.items():
    st.sidebar.write(topic)
    percent = progress/3 
    if percent >= 1:
        percent = 0.999999
    st.sidebar.progress(percent)
    
##################################################################### INTERVIEW STATES #############################################################

# start of interivew resume upload state 
if st.session_state.stage == "upload":

    file_object = st.file_uploader("Please select an input resume: ")

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
            st.session_state.json_str = json.dumps(parsed_text, indent=4)

            st.write("Resume is being read...")
            time.sleep(1)
            st.write("Please wait while we generate questions...")

            st.session_state.stage = "question"
            st.rerun()

# if new question generation state 
elif st.session_state.stage == "question":
    # generate question
    question = generate_questions(st.session_state.json_str, st.session_state.topic_list, st.session_state.q_history)

    st.session_state.question_json = to_json(question)
    st.session_state.question = st.session_state.question_json["question"]
    st.session_state.focus = st.session_state.question_json["focus_areas"]

    #u update hsitory 
    st.session_state.history.append([{"role": "assistant", "content": st.session_state.question},
                                     {"role": "focus", "content": st.session_state.focus},
                                     {"role": "user", "content": None},
                                     {"role": "feedback", "content": None}])
    
    st.session_state.q_history.append(st.session_state.question)

    st.session_state.stage = "answer"
    st.rerun()
 
# if gather user answer stage 
elif st.session_state.stage == "answer":
 
    if st.session_state.history[st.session_state.q_cur][2]["content"] is None: # ensures not revisiting question 
        #retrieve user answer 
        if answer := st.chat_input("Provide your best answer to the following question:"):
            st.session_state.total_q += 1
            st.session_state.answer = answer
            st.session_state.answer_json = json.dumps(answer, indent=4)

            for focus in st.session_state.focus:
                if focus in st.session_state.topic_list:
                    if st.session_state.topic_list[focus] < 3:
                        st.session_state.topic_list[focus] += 1
            
            # update history 
            st.session_state.history[st.session_state.q_cur][2]["content"] = st.session_state.answer
            
            st.session_state.stage = "feedback"
            st.rerun()

# if generate feedback stage
elif st.session_state.stage == "feedback":
    #generate feedback
    feedback = generate_feedback(st.session_state.answer_json, st.session_state.question_json, RUBRIC_AREAS, st.session_state.focus)
    
    # parse and format fedback 
    st.session_state.feedback_to_json = to_json(feedback)
    scores = st.session_state.feedback_to_json["scores"]
    st.session_state.total_scores.append(scores)

    # update history
    st.session_state.history[st.session_state.q_cur][3]["content"] = st.session_state.feedback_to_json

    # move to acknoledgment stage 
    st.session_state.stage =  "wait"
    st.rerun()


# if in acknoledgment stage (time after feedback, waits until user is doen reviewing )  
elif st.session_state.stage == "wait":
    # move on button 
    if st.button("Got it!! Next Question!", use_container_width=True):
        st.session_state.stage = "question"
        st.session_state.q_cur += 1

        st.rerun()