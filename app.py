from flask import Flask, render_template, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
from PIL import Image
import json
from datetime import datetime
import io
import base64
import re
import csv
import google.generativeai as genai

# 設定 Gemini API
GEMINI_API_KEY = "請輸入您的 Gemini API 金鑰"
genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

# 設定上傳文件夾和資料儲存
UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # 設定允許的檔案

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATA_FOLDER'] = DATA_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上傳文件大小為 16MB

def allowed_file(filename): # 確認是否為允許的檔案
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image):
    """圖片預處理以提高辨識準確度"""
    # 調整大小（如果太大）
    max_size = 2000
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return image

def analyze_text_with_gemini(text):
    """使用 Gemini 分析文字內容，分類為不同欄位"""
    prompt = f"""請分析以下名片文字內容，並將其分類為以下欄位。請直接以 JSON 格式回傳，不要包含任何其他說明文字：

    文字內容：
    {text}

    請以以下 JSON 格式回傳：
    {{
        "company": "單位名稱",
        "name": "姓名",
        "address": "地址",
        "phone": "電話",
        "email": "電子郵件",
        "notes": "備註"
    }}

    注意事項：
    1. 如果某個欄位沒有找到對應內容，請留空字串
    2. 備註欄位請包含所有其他未分類的文字
    3. 請確保回傳的是有效的 JSON 格式
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # 解析 Gemini 的回應
        result_text = response.text
        print(f"Gemini 分析回應: {result_text}")
        
        # 提取 JSON 部分
        json_str = re.search(r'\{.*\}', result_text, re.DOTALL)
        if not json_str:
            print("無法找到 JSON 格式的回應")
            return {
                'company': '',
                'name': '',
                'address': '',
                'phone': '',
                'email': '',
                'notes': ''
            }
            
        result = json.loads(json_str.group())
        
        # 確保所有欄位都存在
        required_fields = ['company', 'name', 'address', 'phone', 'email', 'notes']
        for field in required_fields:
            if field not in result:
                result[field] = ''
            # 確保欄位值為字串類型
            result[field] = str(result[field])
        
        print(f"分析結果: {result}")
        return result
        
    except Exception as e:
        print(f"Gemini 分析錯誤: {str(e)}")
        print(f"錯誤類型: {type(e)}")
        import traceback
        print(f"錯誤堆疊: {traceback.format_exc()}")
        return {
            'company': '',
            'name': '',
            'address': '',
            'phone': '',
            'email': '',
            'notes': ''
        }

def process_image_with_gemini(image):
    """使用 Gemini 進行圖片文字辨識"""
    try:
        # 確保圖片是 PIL Image 格式
        if not isinstance(image, Image.Image):
            image = Image.open(image)
            
        print("開始使用 Gemini 進行圖片辨識...")
        
        # 使用 Gemini 進行圖片辨識
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("已建立 Gemini 模型")
        
        response = model.generate_content([
            """請仔細辨識這張名片上的所有文字內容，包括：
            1. 公司名稱
            2. 姓名和職稱
            3. 電話號碼
            4. 地址
            5. 電子郵件
            6. 其他任何可見的文字
            
            請完整回傳所有辨識到的文字內容。""",
            image
        ])
        
        print("Gemini API 回應狀態:", response.prompt_feedback)
        
        if not response.text:
            print("Gemini 回傳空字串")
            return ""
            
        print(f"Gemini 回傳內容: {response.text}")
        return response.text
        
    except Exception as e:
        print(f"Gemini 圖片辨識錯誤: {str(e)}")
        print(f"錯誤類型: {type(e)}")
        import traceback
        print(f"錯誤堆疊: {traceback.format_exc()}")
        return ""

def save_ocr_result(text, filename, image_data=None):
    """儲存 OCR 結果到 JSON 檔案"""
    # 確保資料目錄存在
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
    
    # 分析文字內容
    analyzed_text = analyze_text_with_gemini(text)
    
    # 準備要儲存的資料
    data = {
        'timestamp': datetime.now().isoformat(),
        'filename': filename,
        'text': text,
        'analyzed': analyzed_text
    }
    
    # 如果提供了圖片資料，將其轉換為 base64 並儲存
    if image_data:
        try:
            # 將圖片轉換為 base64
            buffered = io.BytesIO()
            image_data.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            data['image'] = img_str
        except Exception as e:
            print(f"Error saving image: {str(e)}")
    
    # 讀取現有的資料（如果存在）
    json_file = os.path.join(app.config['DATA_FOLDER'], 'ocr_results.json')
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                results = json.load(f)
            except json.JSONDecodeError:
                results = []
    else:
        results = []
    
    # 添加新的結果
    results.append(data)
    
    # 只保留最近 100 筆記錄
    results = results[-100:]
    
    # 儲存更新後的資料
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '沒有選擇文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '沒有選擇文件'}), 400
    
    if file and allowed_file(file.filename):
        try:
            print(f"開始處理檔案: {file.filename}")
            
            # 直接使用上傳的檔案進行處理
            image = Image.open(file.stream)
            print(f"圖片大小: {image.size}, 模式: {image.mode}")
            
            processed_image = preprocess_image(image)
            print(f"處理後圖片大小: {processed_image.size}, 模式: {processed_image.mode}")
            
            # 使用 Gemini 進行圖片文字辨識
            text = process_image_with_gemini(processed_image)
            
            if not text:
                print("無法辨識圖片中的文字")
                return jsonify({'error': '無法辨識圖片中的文字'}), 400
            
            print(f"辨識到的文字: {text}")
            
            # 使用 Gemini 分析文字內容
            analyzed_text = analyze_text_with_gemini(text)
            print(f"分析結果: {analyzed_text}")
            
            # 儲存辨識結果
            result = save_ocr_result(text, file.filename, processed_image)
            result['analyzed'] = analyzed_text
            
            return jsonify({
                'text': text,
                'analyzed': analyzed_text,
                'timestamp': result['timestamp']
            })
        except Exception as e:
            print(f"處理錯誤: {str(e)}")
            print(f"錯誤類型: {type(e)}")
            import traceback
            print(f"錯誤堆疊: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': '不支援的文件類型'}), 400

@app.route('/results', methods=['GET'])
def get_results():
    """取得所有 OCR 結果"""
    json_file = os.path.join(app.config['DATA_FOLDER'], 'ocr_results.json')
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                results = json.load(f)
                return jsonify(results)
            except json.JSONDecodeError:
                return jsonify([])
    return jsonify([])

@app.route('/update_result', methods=['POST'])
def update_result():
    """更新辨識結果"""
    try:
        data = request.json
        timestamp = data.get('timestamp')
        updated_data = data.get('analyzed')
        
        if not timestamp or not updated_data:
            return jsonify({'error': '缺少必要參數'}), 400
            
        json_file = os.path.join(app.config['DATA_FOLDER'], 'ocr_results.json')
        if not os.path.exists(json_file):
            return jsonify({'error': '找不到結果檔案'}), 404
            
        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
            
        # 尋找並更新對應的結果
        for result in results:
            if result['timestamp'] == timestamp:
                result['analyzed'] = updated_data
                break
                
        # 儲存更新後的結果
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_result', methods=['POST'])
def delete_result():
    """刪除指定的辨識結果"""
    try:
        data = request.json
        timestamp = data.get('timestamp')
        
        if not timestamp:
            return jsonify({'error': '缺少必要參數'}), 400
            
        json_file = os.path.join(app.config['DATA_FOLDER'], 'ocr_results.json')
        if not os.path.exists(json_file):
            return jsonify({'error': '找不到結果檔案'}), 404
            
        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
            
        # 過濾掉要刪除的結果
        results = [result for result in results if result['timestamp'] != timestamp]
        
        # 儲存更新後的結果
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_csv')
def export_csv():
    """匯出所有記錄為 CSV 檔案"""
    try:
        json_file = os.path.join(app.config['DATA_FOLDER'], 'ocr_results.json')
        if not os.path.exists(json_file):
            return jsonify({'error': '找不到結果檔案'}), 404
            
        with open(json_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
            
        # 建立 CSV 檔案
        csv_file = os.path.join(app.config['DATA_FOLDER'], 'export.csv')
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            # 寫入標題列
            writer.writerow(['單位名稱', '姓名', '地址', '電話', '電子郵件', '備註', '登記時間'])
            
            # 寫入資料
            for result in results:
                analyzed = result.get('analyzed', {})
                writer.writerow([
                    analyzed.get('company', ''),
                    analyzed.get('name', ''),
                    analyzed.get('address', ''),
                    analyzed.get('phone', ''),
                    analyzed.get('email', ''),
                    analyzed.get('notes', ''),
                    datetime.fromisoformat(result['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        # 回傳檔案
        return send_file(
            csv_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'名片記錄_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 確保必要的目錄存在
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(DATA_FOLDER, exist_ok=True)
    app.run(host='127.0.0.1', port=8888, debug=True) 