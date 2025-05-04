import streamlit as st
import uuid
import requests
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# التحقق من وجود اسم Key Vault
keyVaultName = os.getenv("KEY_VAULT_NAME")
if not keyVaultName:
    st.error("KEY_VAULT_NAME غير موجود في متغيرات البيئة.")
    st.stop()

KVUri = f"https://{keyVaultName}.vault.azure.net"
credential = DefaultAzureCredential()
kv_client = SecretClient(vault_url=KVUri, credential=credential)

BASE_URL = kv_client.get_secret('PROJ-BASE-ENDPOINT-URL').value

LOAD_CHAT_URL = BASE_URL + "load_chat/"
SAVE_CHAT_URL = BASE_URL + "save_chat/"
DELETE_CHAT_URL = BASE_URL + "delete_chat/"
UPLOAD_PDF_URL = BASE_URL + "upload_pdf/"
CHAT_URL = BASE_URL + "chat/"
RAG_CHAT_URL = BASE_URL + "rag_chat/"

# تهيئة جلسة المستخدم
if "history_chats" not in st.session_state:
    st.session_state["history_chats"] = []
if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = None
if "chat_names" not in st.session_state:
    st.session_state["chat_names"] = {}

def load_chats_from_db():
    response = requests.get(LOAD_CHAT_URL)
    print("RESPONSE STATUS:", response.status_code)
    print("RESPONSE TEXT:", response.text)  # أضف هذا السطر

    if response.status_code == 200:
        try:
            records = response.json()
        except Exception as e:
            print("Failed to parse JSON:", e)
            print("Raw response:", response.text)
            return
        for record in records:
            chat_id = record['id']
            messages = record['messages']
            name = record['chat_name']
            pdf_path = record['pdf_path']
            pdf_name = record['pdf_name']
            pdf_uuid = record['pdf_uuid']
            st.session_state["history_chats"].append({
                "id": chat_id,
                "messages": messages,
                "pdf_name": pdf_name,
                "pdf_path": pdf_path,
                "pdf_uuid": pdf_uuid
            })
            st.session_state["chat_names"][chat_id] = name
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

def save_chat_to_db(chat_id, chat_name, messages, pdf_name, pdf_path, pdf_uuid):
    payload = {
        "chat_id": chat_id,
        "chat_name": chat_name,
        "messages": messages,
        "pdf_name": pdf_name,
        "pdf_path": pdf_path,
        "pdf_uuid": pdf_uuid
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(SAVE_CHAT_URL, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to save data. Status code: {response.status_code}")

def create_chat_with_pdf(chat_name, uploaded_pdf):
    with st.spinner("Uploading and Processing document..."):
        files = {"file": (uploaded_pdf.name, uploaded_pdf.getvalue(), "application/pdf")}
        response = requests.post(UPLOAD_PDF_URL, files=files)
        if response.status_code == 200:
            pdf_path = response.json()["pdf_path"]
            pdf_uuid = response.json()["pdf_uuid"]
            new_chat_id = str(uuid.uuid4())
            new_chat = {
                "id": new_chat_id,
                "messages": [],
                "pdf_name": uploaded_pdf.name,
                "pdf_path": pdf_path,
                "pdf_uuid": pdf_uuid
            }
            st.session_state["history_chats"].insert(0, new_chat)
            st.session_state["chat_names"][new_chat_id] = chat_name
            st.session_state["current_chat"] = new_chat_id
            save_chat_to_db(new_chat_id, chat_name, [], uploaded_pdf.name, pdf_path, pdf_uuid)
            st.success("Uploaded and chat created!")
        else:
            st.error("Failed to upload PDF.")

def create_chat(chat_name):
    new_chat_id = str(uuid.uuid4())
    new_chat = {
        "id": new_chat_id,
        "messages": [],
        "pdf_name": None,
        "pdf_path": None,
        "pdf_uuid": None
    }
    st.session_state["history_chats"].insert(0, new_chat)
    st.session_state["chat_names"][new_chat_id] = chat_name
    st.session_state["current_chat"] = new_chat_id
    save_chat_to_db(new_chat_id, chat_name, [], None, None, None)

def delete_chat():
    if st.session_state["current_chat"]:
        chat_id = st.session_state["current_chat"]
        st.session_state["history_chats"] = [
            chat for chat in st.session_state["history_chats"] if chat["id"] != chat_id
        ]
        del st.session_state["chat_names"][chat_id]
        payload = {"chat_id": chat_id}
        headers = {"Content-Type": "application/json"}
        response = requests.post(DELETE_CHAT_URL, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Failed to delete data. Status code: {response.status_code}")
        st.session_state["current_chat"] = (
            st.session_state["history_chats"][0]["id"] if st.session_state["history_chats"] else None
        )

def select_chat(chat_id):
    st.session_state["current_chat"] = chat_id

# تحميل المحادثات
load_chats_from_db()

# Sidebar
with st.sidebar:
    st.title("Chat Management")
    uploaded_pdf = st.file_uploader("Upload PDF", type="pdf", key="pdf_uploader")
    chat_name = st.text_input("Enter Chat Name:", key="new_chat_name")

    if st.button("Create New Chat"):
        if chat_name.strip():
            create_chat(chat_name.strip())
        else:
            st.warning("Chat name cannot be empty.")

    if st.button("Create New Chat with PDF"):
        if not uploaded_pdf:
            st.warning("Please upload a PDF file first.")
        elif chat_name.strip():
            create_chat_with_pdf(chat_name.strip(), uploaded_pdf)
        else:
            st.warning("Chat name cannot be empty.")

    if st.session_state["history_chats"]:
        chat_options = {
            chat["id"]: st.session_state["chat_names"][chat["id"]]
            for chat in st.session_state["history_chats"]
        }
        selected_chat = st.radio(
            "Select Chat",
            options=list(chat_options.keys()),
            format_func=lambda x: chat_options[x],
            key="chat_selector",
            on_change=lambda: select_chat(st.session_state.chat_selector),
        )
        st.session_state["current_chat"] = selected_chat

        st.button("Delete Chat", on_click=delete_chat)

# Main chat area
st.title("Chatbot Application")

if st.session_state["current_chat"]:
    chat_id = st.session_state["current_chat"]
    chat_name = st.session_state["chat_names"][chat_id]
    st.subheader(f"Current Chat: {chat_name}")
    current_chat = next(
        (chat for chat in st.session_state["history_chats"] if chat["id"] == chat_id),
        None,
    )

    if current_chat:
        if current_chat["pdf_name"]:
            st.subheader(f"PDF: {current_chat['pdf_name']}")

        for message in current_chat["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Your Message:"):
            current_chat["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                payload = {
                    "messages": [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
                }
                headers = {"Content-Type": "application/json"}

                if current_chat["pdf_uuid"]:
                    payload["pdf_uuid"] = current_chat["pdf_uuid"]
                    chat_url = RAG_CHAT_URL
                else:
                    chat_url = CHAT_URL

                def get_stream_response():
                    with requests.post(chat_url, json=payload, headers=headers, stream=True) as r:
                        for chunk in r.iter_content(chunk_size=128):
                            yield chunk.decode("utf-8")

                response = st.write_stream(get_stream_response)
                current_chat["messages"].append({"role": "assistant", "content": response})
                save_chat_to_db(chat_id, chat_name, current_chat["messages"],
                                current_chat["pdf_name"], current_chat["pdf_path"], current_chat["pdf_uuid"])
else:
    st.write("No chat selected. Use the sidebar to create or select a chat.")
