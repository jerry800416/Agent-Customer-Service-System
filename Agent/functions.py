import json
import requests
import os
from openai import OpenAI
from ref import AIRTABLE_TOKEN, OPENAI_API_KEY,MODEL, PROMPTS
from flask import Flask, jsonify

# 初始化 OpenAI 客戶端
client = OpenAI(api_key=OPENAI_API_KEY)

# ========================
# 函數：create_lead
# 功能：將使用者表單資料上傳至 Airtable
# 輸入：name, phone, line, address, summary, intention（皆為 str）
# 輸出：若成功回傳 Airtable JSON 回應，失敗則回傳 None
# ========================
def create_lead(name, phone, line, address, summary, intention):
    url = "https://api.airtable.com/v0/appxxxxxxxxxxxx/tblcxxxxxxxxxxxx"
    headers = {
        "Authorization": AIRTABLE_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "records": [{
            "fields": {
                "Name": name,
                "Phone": phone,
                "Line": line,
                "Address": address,
                "Summary": summary,
                "Intention": intention
            }
        }]
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("表單資料成功建立")
        return response.json()
    else:
        print("表單建立失敗，回應內容如下:", response.text)
        return None


def create_assistant(client):
    """
    功能：建立一個 OpenAI Assistant，使用最新模型 gpt-4o-mini，並加入工具：
         - file_search（文件檢索）
         - function（Airtable 表單寫入）
    輸入：
        - client：OpenAI 客戶端物件
    輸出：
        - assistant_id（str）：新建或載入的 Assistant ID
    """

    assistant_file_path = './Agent/assistant.json'  # 本地保存的 assistant ID 檔案路徑

    # 若已有 assistant.json，直接讀取並回傳
    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("已載入本地 assistant ID:", assistant_id)

    else:
        # 建立 Assistant（使用 GPT-4o-mini 模型 + 支援 file_search + 自定義函數）
        assistant = client.beta.assistants.create(
            instructions=PROMPTS.strip(),
            model= MODEL,  # 使用模型
            tools=[
                {"type": "file_search"},  # 替代舊版 retrieval
                {
                    "type": "function",
                    "function": {
                        "name": "create_lead",
                        "description": "Capture lead details and save to Airtable.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Name of the lead."},
                                "phone": {"type": "string", "description": "Phone number of the lead."},
                                "line": {"type": "string", "description": "Line ID of the lead."},
                                "address": {"type": "string", "description": "Address of the lead."},
                                "summary": {"type": "string", "description": "Summarize students’ questions."},
                                "intention": {"type": "string", "description": "Students’ purchase intention."}
                            },
                            "required": ["name", "phone", "line", "address", "summary", "intention"]
                        }
                    }
                }
            ]
        )

        # 儲存 assistant ID 到本地檔案
        with open(assistant_file_path, 'w') as file:
            json.dump({'assistant_id': assistant.id}, file)
            print("建立新 Assistant 並儲存 ID:", assistant.id)

        assistant_id = assistant.id

    return assistant_id

