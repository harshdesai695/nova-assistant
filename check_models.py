import os
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError

# Load env
load_dotenv() 

endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
key = os.getenv("AZURE_INFERENCE_CREDENTIAL")
model = os.getenv("LLM_MODEL", "gpt-4o")

print("---------------------------------------")
print("   AZURE AI FOUNDRY CONNECTION TEST    ")
print("---------------------------------------")

if not endpoint or not key:
    print(f"❌ Error: Credentials not found in .env")
else:
    print(f"✅ Credentials Found.")
    masked_key = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "****"
    print(f"   Key: {masked_key}")
    print(f"   Endpoint: {endpoint}")
    
    try:
        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        
        print("\n🧠 Sending test message ('Hello')...")
        response = client.complete(
            messages=[
                SystemMessage(content="You are a helpful assistant."),
                UserMessage(content="Hello! Are you online?")
            ],
            model=model,
            max_tokens=50
        )
        
        print("\n✅ SUCCESS! Brain is active.")
        print(f"   Response: {response.choices[0].message.content}")

    except HttpResponseError as e:
        print(f"\n❌ Request Failed: {e.status_code} - {e.reason}")
        print(f"   Message: {e.message}")
        
        if e.status_code == 404:
            print("\n💡 TIP: Check your Endpoint URL in .env.")
            print("   For Azure OpenAI resources, it must be the FULL URL with api-version.")
            print("   Example: https://YOUR_RES.openai.azure.com/openai/deployments/YOUR_DEP/chat/completions?api-version=2024-05-01-preview")

    except Exception as e:
        print(f"\n❌ General Error: {e}")