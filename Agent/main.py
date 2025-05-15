from flask import Flask, request, jsonify
from openai import OpenAI
import functions
import json, os, time
from packaging import version
from ref import OPENAI_API_KEY, KNOWLEDGE_BASE

app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)
assistant_id = functions.create_assistant(client)

# 建立 Assistant 時，會自動上傳知識庫資料夾中的檔案
attachments = []
file_paths = os.listdir(KNOWLEDGE_BASE)
for filename in file_paths:
    full_path = os.path.join(KNOWLEDGE_BASE, filename)
    if os.path.exists(full_path):
        file_obj = client.files.create(file=open(full_path, "rb"), purpose="assistants")
        attachments.append({
            "file_id": file_obj.id,
            "tools": [{"type": "file_search"}]
        })
        print(f"上傳檔案 {filename} 成功，ID: {file_obj.id}")
    else:
        print(f"找不到檔案: {filename}")



# === 首頁 ===
@app.route('/')
def index():
    return "<h1>歡迎使用 OpenAI Assistant API</h1>"

# === 建立對話 ===
@app.route('/start', methods=['GET'])
def start_conversation():
    print("開始建立對話...")

    # 建立 thread
    thread = client.beta.threads.create()
    print("對話 thread ID:", thread.id)

    return jsonify({"thread_id": thread.id})


# === 傳送訊息並回應 ===
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('message')

    if not thread_id:
        return jsonify({"error": "Missing thread_id"}), 400

    print("使用者訊息:", user_input)
    print("對話 ID:", thread_id)

    # 1. 發送訊息（含 attachments 綁定）
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input,
        attachments=attachments if attachments else None
    )

    # 2. 啟動 assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # 3. 等待回應（或執行 function）
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )

        print("助手狀態:", run_status.status)

        if run_status.status == "completed":
            break

        elif run_status.status == "requires_action":
            print("執行函式工具...")
            for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                if tool_call.function.name == "create_lead":
                    args = json.loads(tool_call.function.arguments)
                    keys = ["name", "phone", "line", "address", "summary", "intention"]
                    params = {k: args.get(k, "") for k in keys}
                    output = functions.create_lead(
                        params["name"], params["phone"], params["line"],
                        params["address"], params["summary"], params["intention"]
                    )
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=[{
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(output)
                        }]
                    )

        elif run_status.status == "failed":
            print("助手失敗:", run_status.last_error.model_dump())
            return jsonify({
                "error": "Assistant failed",
                "details": run_status.last_error.model_dump()
            }), 500

        time.sleep(1)

    # 4. 抓回 Assistant 回覆
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value
    print("✅ 助手回應:", response)

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
