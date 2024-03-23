import streamlit as st
from streamlit_chatbox import *
import time
import simplejson as json
import anthropic
from datetime import datetime
import uuid

def custom_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif callable(obj):
        return None  # Skip functions and lambda expressions
    elif hasattr(obj, '__dict__'):
        return obj.__dict__  # Convert objects with __dict__ to a dictionary
    else:
        return str(obj)  # Convert other non-serializable objects to strings

api_key = "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"
client = anthropic.Client(api_key=api_key)

chat_box = ChatBox()

with st.sidebar:
    st.subheader('Start to chat using Streamlit')
    streaming = st.checkbox('Streaming', True)
    in_expander = st.checkbox('Show messages in expander', True)
    show_history = st.checkbox('Show history', False)

    st.divider()

    btns = st.container()

    file = st.file_uploader(
        "Chat history JSON",
        type=["json"]
    )

    if st.button("Load JSON") and file:
        data = json.load(file)
        chat_box.from_dict(data)

chat_box.init_session()
chat_box.output_messages()

def on_feedback(
    feedback,
    chat_history_id: str = "",
    history_index: int = -1,
):
    reason = feedback["text"]
    score_int = chat_box.set_feedback(feedback=feedback, history_index=history_index)
    st.session_state["need_rerun"] = True

feedback_kwargs = {
    "feedback_type": "thumbs",
    "optional_text_label": "欢迎反馈您打分的理由",
}

if query := st.chat_input('Input your question here'):
    chat_box.user_say(query)

    if streaming:
        elements = chat_box.ai_say(
            [
                Markdown("thinking", in_expander=in_expander, expanded=True, title="answer")
            ]
        )

        time.sleep(1)
        text = ""

        with client.messages.stream(
            max_tokens=1000,
            messages=[{"role": "user", "content": query}],
            model="claude-3-opus-20240229",
        ) as stream:
            for text_chunk in stream.text_stream:
                text += text_chunk
                chat_box.update_msg(text, element_index=0, streaming=True)

        chat_box.update_msg(text, element_index=0, streaming=False, state="complete")
        chat_history_id = str(uuid.uuid4())  # Generate a unique chat history ID
        chat_box.show_feedback(
            **feedback_kwargs,
            key=chat_history_id,
            on_submit=on_feedback,
            kwargs={"chat_history_id": chat_history_id, "history_index": len(chat_box.history) - 1}
        )
    else:
        response = client.messages(
            model="claude-3-opus-20240229",
            messages=[{"role": "user", "content": query}],
            max_tokens=1000,
        )

        text = response.content[0].text

        chat_box.ai_say(
            [
                Markdown(text, in_expander=in_expander, expanded=True, title="answer")
            ]
        )

btns.download_button(
    "Export Markdown",
    "".join(chat_box.export2md()),
    file_name=f"chat_history.md",
    mime="text/markdown",
)

btns.download_button(
    "Export JSON",
    json.dumps(chat_box.to_dict(), default=custom_default),
    file_name="chat_history.json",
    mime="text/json",
)

if btns.button("Clear history"):
    chat_box.init_session(clear=True)
    st.experimental_rerun()

if show_history:
    st.write(chat_box.history)