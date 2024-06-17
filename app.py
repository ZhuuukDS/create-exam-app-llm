import os
import streamlit as st
from groq import Groq
from streamlit_extras.buy_me_a_coffee import button
from docx import Document
import docx2txt
from pypdf import PdfReader
from get_questions import get_mcq, get_owq
from txt_to_template import generate_output
from dotenv import load_dotenv

load_dotenv()
groq_api = os.getenv('groq_api_key')


st.set_page_config(page_title="Exam bot", 
                   page_icon="🤖")

# function to open a file and to return its contents as a string
def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if len(st.session_state.chat_history) > 20:
    st.session_state.chat_history = st.session_state.chat_history[-20:]


def get_response(user_input, chat_history):
    """
    Function to send a query to Groq's model and get the response.
    """
    # initialize Groq client
    client = Groq(api_key=groq_api)
    system_message = open_file('chatbot_conversational.txt')
    messages = [{'role': 'system', 'content': system_message}] + chat_history + [{'role': 'user', 'content': user_input}]

    # perform the chat completion request
    chat_completion = client.chat.completions.create(
        model='llama3-70b-8192', # can be 'llama3-8b-8192', mixtral-8x7b-32768, etc
        messages=messages,
        temperature=0.5,
        top_p=1,
        stream=False
    )
    response_content = chat_completion.choices[0].message.content.replace('"', '')

    return response_content

# frontend part
st.markdown("<h1 style='text-align: center; color: orange;'>Create Exam</h1>", unsafe_allow_html=True)

css='''
<style>
    section.main > div {max-width:60rem}
</style>
'''
st.markdown(css, unsafe_allow_html=True)

with st.container(height=490, border=True):
    st.header('Enter the course topics')
    st.markdown('____________')
    tab1, tab2 = st.tabs(['Type manually', 'From file'])

    with tab1:
        inp = st.text_input(label='Type in the topics here')

        if st.button("Save"):
                if inp:
                    with open("user_topics.txt", 'a', encoding="utf-8") as out:
                        out.write(inp+', ')
                    st.write(inp)

    with tab2:
        user_topics = st.file_uploader(label="Upload the file with a list of topics :+1: :sunglasses:", type=["docx", "pdf", "txt"], accept_multiple_files=True)

        if st.button("Process"):
            if user_topics:
                for file in user_topics:
                    file_details = f"filetype: {file.type}\n\n filesize: {file.size}"
                    if file.type =="text/plain":
                        user_topics_txt_string = str(file.read(), "utf-8")
                        with open("user_topics.txt", 'a', encoding="utf-8") as out:
                            out.write(user_topics_txt_string+', ')
                        st.write("Done!")
                    elif file.type == "application/pdf":
                        user_topics_pdf = PdfReader(file)
                        with open("user_topics.txt", 'a') as f:
                            for page in user_topics_pdf.pages:
                                f.write(page.extract_text()+', ')
                        st.write("Done!")
                    else:
                        user_topics_docx = docx2txt.process(file)
                        with open("user_topics.txt", 'a') as out:
                            out.write(user_topics_docx+', ')         
                        st.write("Done!")
            else:
                st.write("Upload file first!")

if inp or user_topics:
    if st.button(label='Show topics'):
        with open('user_topics.txt', 'r+') as ut:
            topics = ut.read()
            st.session_state['topics'] = topics
        
    if 'topics' in st.session_state:
        st.text_area('See and edit topics:', key='topics', height=200)
            
        if st.button('Confirm topics'):
            with open('user_topics.txt', 'w') as ut:
                print(st.session_state['topics'], file=ut)
                # st.session_state['topics']
                st.write('Done!')
                st.session_state['topics_confirmed'] = True

with st.container(border=True):
    st.header('Generate exam parts')
    st.markdown('____________')
    if 'topics_confirmed' in st.session_state:

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('Multiple Choice Questions')
            if st.button(label="Create MCQs"):
                get_mcq()
                with open("chat_mcq.txt", 'r', encoding="utf-8") as f: 
                    data = f.read()
                    st.session_state["new_mcq"] = data

            if "new_mcq" in st.session_state:
                st.text_area("Check and edit if needed: ", key="new_mcq", height=420)
                if st.button("Confirm MCQs"):
                    with open("chat_mcq.txt", 'w') as out: # rewrite the file with updated questions
                        print(st.session_state["new_mcq"], file=out)
                    st.write('Confirmed!')
        with col2:
            st.markdown('Open-Written Questions')
            if st.button(label="Create OWQs"):
                get_owq()
                with open("chat_owq.txt", 'r', encoding="utf-8") as f: 
                    data = f.read()
                    st.session_state["new_owq"] = data

            if "new_owq" in st.session_state:
                st.text_area("Check and edit if needed: ", key="new_owq", height=420)
                if st.button("Confirm OWQs"):
                    with open("chat_owq.txt", 'w') as out: # rewrite the file with updated questions
                        print(st.session_state["new_owq"], file=out)
                    st.write('Confirmed!')

        if 'new_mcq' in st.session_state or 'new_owq' in st.session_state:
            if st.button("Get exam!", use_container_width = True):
                generate_output()
                del st.session_state['topics']
                del st.session_state['topics_confirmed']

    # download exam 
    if os.path.exists("output.docx"):
        with open("output.docx", 'rb') as file:
            st.download_button(label="Download Exam", data=file, file_name="output.docx")


    # delete the output.docx
    if os.path.exists("output.docx"):
        os.remove("output.docx")
        # clean the text files
        with open('user_topics.txt', 'w') as file:
            pass
        with open('chat_mcq.txt', 'w') as cmcq:
            pass
        with open('chat_owq.txt', 'w') as cowq:
            pass

# -----------------------------------------
# FEEDBACKS PART
# -----------------------------------------
with st.container(border=True):
    st.header("Feedback and comments")
    st.markdown('______________')

    # like button
    like = st.checkbox("Do you like this app?")

    # 'buy me a coffee' link
    if like:
        button(username="zhuuukds", floating=False, width=221)

    # function to clear feedback text input
    def clear_text():
        st.session_state.feedback = st.session_state.widget
        st.session_state.widget = ""

    # feedback field
    with open("feedbacks.txt", 'a', encoding="utf-8") as f:
        st.text_input('Tell me what can be improved:', key='widget', on_change=clear_text)
        feedback = st.session_state.get('feedback', '')
        # save feedback to file
        print(feedback, file=f)
        st.write(feedback)


# -----------------------------------------
# CHAT PART
# -----------------------------------------
with st.container(height=100, border=True):
    # chat 
    st.header('Let\'s chat :)')
    st.markdown('__________')

# roles in chat history
for message in st.session_state.chat_history:
    if message["role"] == "assistant":
        with st.chat_message("Cybria", avatar="👩‍🎤"):
            st.write(message["content"])
    elif message["role"] == "user":
        with st.chat_message("Human"):
            st.write(message["content"])


user_query = st.chat_input("now chat with me...")
if user_query is not None and user_query != '':
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    with st.chat_message("human"):
        st.markdown(user_query)
    with st.chat_message("Cybria", avatar="👩‍🎤"):
        response = get_response(user_query, st.session_state.chat_history)
        st.write(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})

# --------------------------------------------------------------------------------------
