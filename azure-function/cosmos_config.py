import os
from azure.cosmos import CosmosClient

# قم بتهيئة التفاصيل الخاصة بـ Cosmos DB
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER")

# إنشاء العميل للاتصال بـ Cosmos DB
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)

# الوصول إلى الـ database
database = client.get_database_client(COSMOS_DATABASE)

# الوصول إلى الـ container
container = database.get_container_client(COSMOS_CONTAINER)
