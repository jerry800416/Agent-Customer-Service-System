# 🧠 Agent Assistant API – 課程諮詢智能助理系統

這是一套基於 OpenAI Assistant v2 API 的智能助理系統，使用 Flask 建立 API server，提供用戶互動對話、自動課程推薦、報價諮詢、以及潛在學員資料蒐集與 Airtable 建檔功能。

**完整安裝以及說明請參閱：https://jerry800416.medium.com/%E5%A4%A7%E6%A8%A1%E5%9E%8Bllm%E8%90%BD%E5%9C%B0-3-%E8%87%AA%E5%BB%BA%E8%81%8A%E5%A4%A9%E6%A9%9F%E5%99%A8%E4%BA%BA-3d5efb7a0fff**


[toc]


## 📦 專案特色

* 使用 OpenAI 目前已開放模型，支援角色設定與多輪對話
* 支援 `file_search` 工具，自動查詢知識庫內容
* 透過 `function calling` 自動建立潛在客戶表單 (`create_lead`)
* 使用者可上傳多份知識檔案，自動綁定與 Assistant 回答
* 支援自訂角色設定、報價邏輯與資訊引導策略
* 整合 Airtable API 寫入學員名單

## 檔案介紹

```
├─Agent                         # ✅ 智能助理核心邏輯所在資料夾
│  ├─Knowledge                 # 📚 知識庫資料夾：放置用於 file_search 的文字、PDF 檔案
│  ├─assistant.json            # 🧠 儲存 Assistant ID 的本地快取檔，避免重複建立
│  ├─functions.py              # 🔧 自訂函式（如 create_lead）與建立 Assistant 的方法
│  ├─main.py                   # 🚀 Flask 主程式，包含 API 路由：/start、/chat 等功能
│  ├─ref.py                    # 🔑 API 金鑰與設定參數（如 OpenAI key、Airtable token、模型名稱等）
│  └─requirements.txt          # 📦 Python 相依套件清單，可用 pip install -r 安裝
└─WebSite                      # 🌐 前端介面整合區
│  ├─website                 # 💻 網頁前端
│  └─wechat                  # 📨 仿微信網頁前端
└─advanced-gpt-website-template.vf  # 聊天機器人工作流程檔案
```


## 🛠️ 安裝與準備

1. 安裝必要套件：

```bash
pip install -r requirements.txtr
```

1. 在 `ref.py` 新增憑證：

```python

OPENAI_API_KEY = "sk-..."     # OpenAI 金鑰
AIRTABLE_TOKEN = "Bearer ..." # Airtable 金鑰
MODEL = "gpt-4o" # 可自行選擇
PROMPTS = """（你的角色設定，可複製 paste）"""
KNOWLEDGE_BASE = "./knowledge"  # 存放 TXT、PDF 的資料夾路徑
```

3. 準備你的知識檔案（例如 `dige.txt`, `faq.pdf`）放入 `./knowledge` 資料夾

4. 建立 Assistant（會自動儲存 `assistant_id` 至 `assistant.json`）

**完整安裝以及說明請參閱：https://jerry800416.medium.com/%E5%A4%A7%E6%A8%A1%E5%9E%8Bllm%E8%90%BD%E5%9C%B0-3-%E8%87%AA%E5%BB%BA%E8%81%8A%E5%A4%A9%E6%A9%9F%E5%99%A8%E4%BA%BA-3d5efb7a0fff**

## 🚀 啟動伺服器

```bash
python main.py
```

伺服器將啟動於 `http://localhost:8080/`

## 📡 API 路由說明

### `GET /start`

* 建立新的對話 thread
* 上傳知識庫中所有檔案
* 回傳 `thread_id` 及 `attachments` 給前端使用

**回應範例：**

```json
{
  "thread_id": "thread_xxx",
  "attachments": [
    {
      "file_id": "file-abc123",
      "tools": [{"type": "file_search"}]
    }
  ]
}
```

### `POST /chat`

使用者對 Assistant 發送一則訊息。

**Request JSON:**

```json
{
  "thread_id": "thread_xxx",
  "message": "我想報名課程，請問要怎麼開始？",
  "attachments": [...]  // 從 /start 拿來的檔案資訊
}
```

**回應 JSON:**

```json
{
  "response": "請問您的姓名、聯絡電話與 Line ID？"
}
```

## 🧩 Assistant 設定（角色與工具）

建立 Assistant 時設定以下項目：

### ✅ 角色（instructions）

```text
你是一位 AI 課程學習規劃專家，會根據使用者的城市報價並引導留下聯絡方式，最後自動建立表單。
...
（詳細設定請見 ref.py 的 PROMPTS 變數）
```

### ✅ 工具設定

* `file_search`：用於文件檢索
* `create_lead`：用來寫入 Airtable 表單

## 🛠️ Function 呼叫邏輯：`create_lead`

Assistant 根據使用者提供的資訊自動判斷是否需要建立潛在客戶表單，觸發條件為：

* Assistant 模型自動決定呼叫 `create_lead`
* 有哪些欄位就寫入哪些欄位，沒有的用空字串補齊

所有欄位：

```json
{
  "name": "使用者姓名",
  "phone": "電話",
  "line": "Line ID",
  "address": "城市/地區",
  "summary": "提問摘要",
  "intention": "購買意願（強烈/一般/暫不考慮）"
}
```

## 📁 知識庫設計（file\_search）

* 所有檔案放在 `./knowledge/` 資料夾
* 檔案會在 `/start` 中上傳並轉成 `file_id`
* 在 `/chat` 中以 `attachments` 附加進每則訊息中


## ✅ 錯誤處理設計

* 自動容錯 missing 欄位（使用 `.get(k, "")`）
* 檢查 Assistant run 的狀態：`completed` / `requires_action` / `failed`
* 若缺欄位不阻斷流程，允許持續收集資料



## ✅ 測試建議話術

```text
我叫王小明，電話 0932123456，住高雄，我的 LINE 是 @abc123。
我對課程很有興趣，想了解報名流程與價格。
```

這樣最容易誘發 Assistant 呼叫 `create_lead` 函式。


## 結果

![image](https://github.com/jerry800416/Agent-Customer-Service-System/blob/main/Results.gif)