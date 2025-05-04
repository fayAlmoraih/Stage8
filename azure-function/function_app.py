import azure.functions as func
import logging
from azure.cosmos import CosmosClient
import os
from dotenv import load_dotenv
import json

# تحميل متغيرات البيئة
load_dotenv()

# جلب القيم من ملف .env
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE_NAME = os.getenv("COSMOS_DATABASE_NAME")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME")

app = func.FunctionApp()

@app.function_name(name="HttpTriggerFA")
@app.route(route="storechat", methods=["POST"])
def store_chat(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # التحقق من أن كل المتغيرات موجودة
        if not all([COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DATABASE_NAME, COSMOS_CONTAINER_NAME]):
            return func.HttpResponse("Error: Missing required environment variables for Cosmos DB connection", status_code=500)

        # قراءة البيانات من الطلب
        data = req.get_json()

        chat_id = data.get("chat_id")
        chat_name = data.get("chat_name")
        messages = data.get("messages", [])
        pdf_name = data.get("pdf_name")
        pdf_path = data.get("pdf_path")
        pdf_uuid = data.get("pdf_uuid")

        if not chat_id or not chat_name:
            return func.HttpResponse("Missing chat_id or chat_name", status_code=400)

        # الاتصال بـ Cosmos DB
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(COSMOS_DATABASE_NAME)
        container = database.get_container_client(COSMOS_CONTAINER_NAME)

        item = {
            "id": chat_id,
            "chat_name": chat_name,
            "messages": messages,
            "pdf_name": pdf_name,
            "pdf_path": pdf_path,
            "pdf_uuid": pdf_uuid
        }

        container.upsert_item(item)

        return func.HttpResponse("Chat saved successfully", status_code=200)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
