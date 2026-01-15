import google.generativeai as genai
import os

# 從環境變數或直接設定 API Key
# 請確保 GEMINI_API_KEY 環境變數已設定，或者直接在這裡替換成您的 API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCLfrIqnJDZNx4_1ihSN92lFVgrfb6SfTg")
genai.configure(api_key=GEMINI_API_KEY)

print("可用模型列表及其支援的方法：")
for model in genai.list_models():
    print(f"{model.name}: {model.supported_generation_methods}") 