from google import genai

# 1. 用你的 API Key 建立 client
client = genai.Client(api_key="AIzaSyCLfrIqnJDZNx4_1ihSN92lFVgrfb6SfTg")

# 2. 呼叫 Gemini 生成內容
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="你好！請跟我打個招呼",
)

# 3. 印出回傳文字
print(response.text)
