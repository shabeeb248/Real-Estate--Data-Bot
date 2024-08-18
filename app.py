import streamlit as st
import warnings
warnings.filterwarnings('ignore')
import numpy as np
from controller import *

    
def handle_input():

    if st.session_state.user_input:
        # Append user message to chat
        st.session_state.chat_data.append({"role": "user", "content": st.session_state.user_input})
        
        qna = answer(st.session_state.user_input)
        print(qna)
        # Example assistant response (you can replace this with more complex logic)
        st.session_state.chat_data.append(qna)
        st.session_state.user_input = ""

st.markdown("""
    <style>
    .user-message {
        background-color: #DCF8C6;
        padding: 8px 12px;
        border-radius: 15px;
        margin: 5px 0;
        max-height: 2000px;
        align-self: flex-end;
        color: black; 
    }
    .assistant-message {
        background-color: #ECECEC;
        padding: 8px 12px;
        border-radius: 15px;
        max-height: 2000px;
        margin: 5px 0;
        align-self: flex-start;
        color: black;
    }
    .chat-message {
        display: flex;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


st.markdown("""
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        var chatContent = document.getElementById("chat-content");
        chatContent.scrollTop = chatContent.scrollHeight;
    });

    // Scroll to bottom after new messages are added
    const observer = new MutationObserver(() => {
        var chatContent = document.getElementById("chat-content");
        chatContent.scrollTop = chatContent.scrollHeight;
    });

    observer.observe(document.getElementById("chat-content"), { childList: true });
    </script>
    """, unsafe_allow_html=True)
# Function to display the first page content
def page1():
    st.title("File Upload")

    # File upload
    uploaded_file = st.file_uploader("Upload Excel file", type=["csv"])
    button = st.button("Upload")
    if uploaded_file is not None and button:
        cons = create(uploaded_file)
        st.write(cons)
        st.write("Upload Successful. Go to Chat Page")

# Function to display the second page content
def page2():
    chat = getchat()
    st.session_state.chat_data = chat
    st.title("Chat")
    
    st.markdown('<div class="chat-content">', unsafe_allow_html=True)
    for message in st.session_state.chat_data:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-container"><div class="chat-message user-message">{message["content"]}</div></div>', unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(message["content"],unsafe_allow_html=True)
        
        # Check if there's an image and display it
        if "image" in message:
            st.image(message["image"], caption="Image from Assistant", use_column_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    #cols = st.columns([9, 1])
    #with cols[0]:
    user_input = st.text_input("Type your message here:", key="user_input", label_visibility="collapsed", on_change=handle_input)

    #with cols[1]:
    #    submit_button = st.button("Send", on_click=handle_input, args=(user_input,))
    #


def main():

    st.sidebar.title("Navigation")
    
    # Selectbox for page navigation
    page = st.sidebar.selectbox("Choose a page", ["Upload", "Chat"])

    # Load the selected page
    if page == "Upload":
        page1()
    elif page == "Chat":
        page2()

if __name__ == "__main__":
    main()
