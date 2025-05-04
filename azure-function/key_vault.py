from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

# تفاصيل الاتصال بـ Key Vault
KEY_VAULT_NAME = os.getenv("KEY_VAULT_NAME")
KEY_VAULT_URI = f"https://{KEY_VAULT_NAME}.vault.azure.net/"

# إنشاء عميل Azure Key Vault
credential = DefaultAzureCredential()
client = SecretClient(vault_url=KEY_VAULT_URI, credential=credential)

# جلب سر من Key Vault
def get_secret(secret_name: str) -> str:
    key_vault_name = os.environ["KEY_VAULT_NAME"]
    key_vault_url = f"https://{key_vault_name}.vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=key_vault_url, credential=credential)
    secret = client.get_secret(secret_name)
    return secret.value
