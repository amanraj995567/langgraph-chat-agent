import streamlit as st
from database_backend import chatbot, retrive_all_threads
from langchain_core.messages import HumanMessage
import uuid


################################# utility function ##################################
def generate_thread_id():
    thread_id = str(uuid.uuid4())
    return thread_id

def add_threads(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def  start_new_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id']=thread_id
    add_threads(st.session_state['thread_id'])
    st.session_state['message_history']=[]

def load_chat(thread_id):
    state = chatbot.get_state(config= {'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])





 ######################### session.  ###################################################
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id']=generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads']= retrive_all_threads()

add_threads(st.session_state['thread_id'])


########################################### UI of side bar  ################################
st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button("New Chat"):
    start_new_chat()

st.sidebar.header("Chat History")

###################loading the conversation history################
for thread_id in st.session_state['chat_threads']:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id']=thread_id
        messages = load_chat(thread_id)

        temp_msg = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role= "user"
            else:
                role= "assistant"
            temp_msg.append({"role": role, "content": msg.text})

        st.session_state['message_history']=temp_msg



#loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])


user_input = st.chat_input('Type here')


if user_input:
    st.session_state['message_history'].append({'role':'user',  'content': user_input })
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}


    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            str(message_chunk.text) for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            )
        )
    st.session_state['message_history'].append({'role':'assistant',  'content': ai_message })



