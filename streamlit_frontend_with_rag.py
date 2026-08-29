import streamlit as st
from chatbot_backend_rag import (
    chatbot,
    ingest_pdf,
    retrieve_all_threads,
    thread_document_metadata,
)
from langchain_core.messages import AIMessage, HumanMessage
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

def make_title(text):
    return text.strip().split("\n")[0][:40] or "Untitled chat"

def thread_title(thread_id):
    # Cached so we only walk the checkpointer once per thread.
    if thread_id in st.session_state['thread_names']:
        return st.session_state['thread_names'][thread_id]

    for msg in load_chat(thread_id):
        if isinstance(msg, HumanMessage):
            title = make_title(msg.text)
            st.session_state['thread_names'][thread_id] = title
            return title

    return "Untitled chat"

def visible_messages(messages):
    """Human/AI turns only - ToolMessages are internal, not part of the chat."""
    temp_msg = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        else:
            continue
        if msg.text:
            temp_msg.append({"role": role, "content": msg.text})
    return temp_msg

def stream_ai_response(user_input, config):
    """Yield only the assistant's own text, skipping tool results."""
    for message_chunk, metadata in chatbot.stream(
        {'messages': [HumanMessage(content=user_input)]},
        config=config,
        stream_mode="messages"
    ):
        if isinstance(message_chunk, AIMessage) and message_chunk.text:
            yield message_chunk.text


 ######################### session.  ###################################################
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id']=generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads']= retrieve_all_threads()

if 'thread_names' not in st.session_state:
    st.session_state['thread_names']={}

if 'ingested_files' not in st.session_state:
    st.session_state['ingested_files']={}

add_threads(st.session_state['thread_id'])


########################################### UI of side bar  ################################
st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button("New Chat"):
    start_new_chat()


############################### PDF upload for the current chat ############################
st.sidebar.header("Document")

uploaded_pdf = st.sidebar.file_uploader(
    "Upload a PDF",
    type=["pdf"],
    # Keyed per thread so switching chats clears the widget.
    key=f"uploader_{st.session_state['thread_id']}",
)

if uploaded_pdf is not None:
    # Streamlit re-runs the whole script on every interaction, so only ingest
    # when this thread has not already indexed this exact file.
    fingerprint = (uploaded_pdf.name, uploaded_pdf.size)
    if st.session_state['ingested_files'].get(st.session_state['thread_id']) != fingerprint:
        with st.sidebar.status(f"Indexing {uploaded_pdf.name}..."):
            summary = ingest_pdf(
                uploaded_pdf.getvalue(),
                st.session_state['thread_id'],
                uploaded_pdf.name,
            )
        st.session_state['ingested_files'][st.session_state['thread_id']] = fingerprint
        st.sidebar.success(f"Indexed {summary['chunks']} chunks")

document = thread_document_metadata(st.session_state['thread_id'])
if document:
    st.sidebar.caption(
        f"Active: {document['filename']} - {document['documents']} pages, "
        f"{document['chunks']} chunks"
    )
else:
    st.sidebar.caption("No PDF indexed for this chat yet.")


st.sidebar.header("Chat History")

###################loading the conversation history################
for thread_id in reversed(st.session_state['chat_threads']):
    if st.sidebar.button(thread_title(thread_id), key=thread_id, use_container_width=True):
        st.session_state['thread_id']=thread_id
        st.session_state['message_history']=visible_messages(load_chat(thread_id))


#loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])


user_input = st.chat_input('Type here')


if user_input:
    st.session_state['message_history'].append({'role':'user',  'content': user_input })
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']},
              'metadata':{
                  'thread_id': st.session_state['thread_id']
              },
              'run_name':'chat_turn'
              }


    with st.chat_message('assistant'):
        ai_message = st.write_stream(stream_ai_response(user_input, CONFIG))
    st.session_state['message_history'].append({'role':'assistant',  'content': ai_message })

    # First message in a fresh thread names it. The sidebar was already drawn
    # above, so rerun to show the new label instead of "New Chat".
    if st.session_state['thread_id'] not in st.session_state['thread_names']:
        st.session_state['thread_names'][st.session_state['thread_id']] = make_title(user_input)
        st.rerun()
