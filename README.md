# 名片管理系統

這是一個基於 Flask 和 Gemini AI 的智能名片管理系統，能夠自動辨識和分析名片內容，提供便捷的名片資訊管理功能。

## 功能特點

- 📸 智能名片辨識：使用 Gemini AI 進行高精度文字辨識
- 🔍 自動資訊分類：自動將名片內容分類為公司名稱、姓名、地址等欄位
- 📝 手動編輯功能：支援修改辨識結果
- 📊 資料匯出：支援將名片資料匯出為 CSV 格式
- 🖼️ 圖片預處理：自動優化圖片以提高辨識準確度
- 💾 資料持久化：自動保存辨識結果和原始圖片

## 技術架構

- 後端框架：Flask
- AI 引擎：Google Gemini AI
- 圖片處理：Pillow (PIL)
- 資料儲存：JSON
- 前端技術：HTML, CSS, JavaScript

## 系統需求

- Python 3.7+
- Flask
- Pillow
- Google Gemini AI API 金鑰

## 安裝說明

1. 克隆專案：
```bash
git clone [專案網址]
```

2. 安裝依賴：
```bash
pip install -r requirements.txt
```

3. 設定環境變數：
```bash
export GEMINI_API_KEY="您的 Gemini API 金鑰"
```

4. 啟動應用：
```bash
python app.py
```

## 使用說明

1. 開啟瀏覽器訪問 `http://127.0.0.1:8888`
2. 點擊上傳按鈕選擇名片圖片
3. 系統會自動辨識並分類名片內容
4. 可以手動編輯辨識結果
5. 使用匯出功能將資料匯出為 CSV 檔案

## 注意事項

- 支援的圖片格式：PNG、JPG、JPEG、GIF
- 最大檔案大小限制：16MB
- 系統會自動保存最近 100 筆記錄

## 授權說明

[授權條款說明] 本專案採用 MIT 授權條款

## 聯絡資訊

[聯絡方式(Andy Hsiao蕭禹安)](vulm30@gmail.com) 