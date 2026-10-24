from flask import Flask, render_template, request, jsonify, send_file, Response
import os
import subprocess
import time
import requests
import json
import re
import threading
import http.client

# 引入项目所有模块
from Draw import h_seedream40_character_real
from Video import h_veo
from Language.h_streamTalk import chat_stream_generator
from Audio.h_tts import generate_speech
from Listen.h_asr import transcribe_audio

# ffmpeg 准备
try:
    import imageio_ffmpeg
    FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG_BINARY = 'ffmpeg'

app = Flask(__name__)

# --- 全局配置 ---
MEMORY_FILE = "chat_history.json"
MAX_HISTORY_ROUNDS = 5

# --- 全局状态变量 ---
conversation_counter = 0
background_thread_running = False
latest_generated_video = None

# --- 记忆管理模块 ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f: 
                return json.load(f)
        except Exception: 
            return []
    return []

def save_memory(history):
    recent_history = history[-MAX_HISTORY_ROUNDS * 2:]
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(recent_history, f, ensure_ascii=False, indent=2)
    except Exception as e: 
        print(f"保存记忆失败: {e}")

# --- 基础路由 ---
@app.route('/')
def index():
    return render_template('index.html')

# --- 1. 生图接口 ---
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        hair = data.get('hair', '').strip()
        figure = data.get('figure', '').strip()
        facial = data.get('facial', '').strip()
        appearance = data.get('appearance', '').strip()
        
        if not all([hair, figure, facial, appearance]):
            return jsonify({'error': '所有字段都必须填写'}), 400
        
        character_url = h_seedream40_character_real.generate_character_image(hair, figure, facial, appearance)
        if not character_url:
            return jsonify({'error': '角色图片生成失败'}), 500
        
        try:
            response = requests.get(character_url)
            response.raise_for_status()
            image_filename = f"character_{int(time.time())}.png"
            with open(os.path.join(os.getcwd(), image_filename), 'wb') as f:
                f.write(response.content)
            return jsonify({'success': True, 'image_filename': image_filename, 'character_url': character_url})
        except Exception as e:
            print(f"图片下载失败，退回URL模式: {e}")
            return jsonify({'success': True, 'character_url': character_url})
    except Exception as e:
        return jsonify({'error': f'生成失败: {str(e)}'}), 500

# --- 2. 生视频接口 ---
@app.route('/generate_video', methods=['POST'])
def generate_video():
    try:
        data = request.json
        character_url = data.get('character_url', '').strip()
        if not character_url: 
            return jsonify({'error': '图片URL不能为空'}), 400
        
        action_prompt = "Character lip-syncing:'Hello! Nice to meet you. I'm Nova, your exclusive digital friend!'"
        animation_path = h_veo.generate_animation_video(character_url, action_prompt)
        if not animation_path: 
            return jsonify({'error': '动画视频生成失败'}), 500
        
        video_filename = os.path.basename(animation_path)
        video_full_path = os.path.join(os.getcwd(), video_filename)
        
        try:
            video_name_without_ext = os.path.splitext(video_filename)[0]
            video_no_audio_filename = f"{video_name_without_ext}_no_audio.mp4"
            video_no_audio_path = os.path.join(os.getcwd(), video_no_audio_filename)
            ffmpeg_cmd = [FFMPEG_BINARY, '-i', video_full_path, '-c:v', 'copy', '-an', '-y', video_no_audio_path]
            subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=False)
            
            if os.path.exists(video_no_audio_path):
                return jsonify({'success': True, 'video_path': video_no_audio_filename})
            return jsonify({'success': True, 'video_path': video_filename})
        except Exception as e:
            print(f"去音频失败: {e}")
            return jsonify({'success': True, 'video_path': video_filename})
    except Exception as e:
        return jsonify({'error': f'生成失败: {str(e)}'}), 500

# --- 3. ASR 语音识别接口 ---
@app.route('/asr', methods=['POST'])
def asr():
    if 'audio' not in request.files: 
        return jsonify({'error': '无文件'}), 400
    file = request.files['audio']
    if file.filename == '': 
        return jsonify({'error': '未选择文件'}), 400
    
    ext = os.path.splitext(file.filename)[1].lower()
    temp_filename = f"temp_upload_{int(time.time())}{ext}"
    temp_filepath = os.path.join(os.getcwd(), temp_filename)
    
    try:
        file.save(temp_filepath)
        text = transcribe_audio(temp_filepath)
        if os.path.exists(temp_filepath): 
            os.remove(temp_filepath)
        if text is None: 
            return jsonify({'success': False, 'error': '识别失败'}), 500
        return jsonify({'success': True, 'text': text})
    except Exception as e:
        if os.path.exists(temp_filepath): 
            os.remove(temp_filepath)
        return jsonify({'error': str(e)}), 500

# --- 4. 后台情绪视频生成线程 ---
def background_generate_video(history, current_image_url):
    global background_thread_running, latest_generated_video
    print("\n[后台任务] 开始根据情绪生成新视频...")
    try:
        emotion_prompt = "请阅读以下对话记录，用极其简短的英文单词（如 happy, sad, angry, surprised, neutral）归纳当前角色的情绪，只输出这个词，不要任何标点：\n"
        for msg in history[-4:]:
            emotion_prompt += f"{msg['role']}: {msg['content']}\n"
            
        API_KEY = "your_api"
        conn = http.client.HTTPSConnection("jmpb-szb.com")
        payload = json.dumps({
           "model": "gpt-4.1",
           "input": [{"role": "user", "content": emotion_prompt}]
        })
        headers = {'Accept': 'application/json', 'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
        conn.request("POST", "/v1/responses", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        
        try:
            emotion_text = data["output"][0]["content"][0]["text"].strip().lower()
        except:
            emotion_text = "happy"
        print(f"[后台任务] 归纳出的情绪词: {emotion_text}")
        
        action_prompt = f"Character looks {emotion_text}, talking and moving naturally."
        animation_path = h_veo.generate_animation_video(current_image_url, action_prompt)
        
        if animation_path:
            video_filename = os.path.basename(animation_path)
            video_no_audio_filename = f"{os.path.splitext(video_filename)[0]}_no_audio.mp4"
            ffmpeg_cmd = [FFMPEG_BINARY, '-i', os.path.join(os.getcwd(), video_filename), '-c:v', 'copy', '-an', '-y', os.path.join(os.getcwd(), video_no_audio_filename)]
            subprocess.run(ffmpeg_cmd, capture_output=True, check=False)
            
            latest_generated_video = video_no_audio_filename
            print(f"[后台任务] 新视频生成完毕并已就绪: {latest_generated_video}")
    except Exception as e:
        print(f"[后台任务] 生成视频失败: {e}")
    finally:
        background_thread_running = False

# --- 5. 核心对话接口 (流式分句) ---
@app.route('/chat', methods=['POST'])
def chat():
    global conversation_counter, background_thread_running
    data = request.json
    user_message = data.get('message', '').strip()
    current_image_url = data.get('character_url', '')
    
    if not user_message: 
        return jsonify({'error': '消息不能为空'}), 400
    
    history = load_memory()
    
    def generate_response():
        global conversation_counter, background_thread_running
        full_ai_reply = []
        sentence_buffer = ""
        
        try:
            for chunk in chat_stream_generator(user_message, history):
                if not chunk: continue
                full_ai_reply.append(chunk)
                sentence_buffer += chunk
                
                # 遇到标点符号，切分句子，立刻生成语音
                parts = re.split(r'([。！？，,.!?\n])', sentence_buffer)
                if len(parts) >= 3:
                    sentence = (parts[0] + parts[1]).strip()
                    sentence_buffer = "".join(parts[2:])
                    if not sentence: continue
                    
                    audio_filename = generate_speech(sentence)
                    payload = {"text": sentence, "audio_url": f'/audio/{audio_filename}' if audio_filename else None}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            
            # 收尾最后一句
            if sentence_buffer.strip():
                sentence = sentence_buffer.strip()
                audio_filename = generate_speech(sentence)
                payload = {"text": sentence, "audio_url": f'/audio/{audio_filename}' if audio_filename else None}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                
            yield "data: [DONE]\n\n"
            
            # 保存记忆
            complete_reply = "".join(full_ai_reply)
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": complete_reply})
            save_memory(history)
            
            # 触发后台情绪视频
            conversation_counter += 1
            print(f"[状态] 当前对话轮数: {conversation_counter}")
            if conversation_counter % 5 == 0 and current_image_url and not background_thread_running:
                background_thread_running = True
                threading.Thread(target=background_generate_video, args=(history, current_image_url)).start()
                
        except Exception as e:
            print(f"流式处理失败: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate_response(), mimetype='text/event-stream')

# --- 6. 前端轮询新视频接口 ---
@app.route('/get_new_video', methods=['GET'])
def get_new_video():
    global latest_generated_video
    if latest_generated_video:
        video_path = latest_generated_video
        latest_generated_video = None 
        return jsonify({'success': True, 'video_path': video_path})
    return jsonify({'success': False})

# --- 7. 清除记忆 ---
@app.route('/clear_history', methods=['POST'])
def clear_history():
    if os.path.exists(MEMORY_FILE): 
        os.remove(MEMORY_FILE)
    return jsonify({'success': True})

# --- 8. 静态文件服务 ---
@app.route('/image/<filename>')
def serve_image(filename):
    try:
        p = os.path.join(os.getcwd(), filename)
        if os.path.exists(p): return send_file(p, mimetype='image/png')
        return jsonify({'error': '文件不存在'}), 404
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/video/<filename>')
def serve_video(filename):
    try:
        p = os.path.join(os.getcwd(), filename)
        if os.path.exists(p): return send_file(p, mimetype='video/mp4')
        return jsonify({'error': '文件不存在'}), 404
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    try:
        p = os.path.join(os.getcwd(), filename)
        if os.path.exists(p): return send_file(p, mimetype='audio/mpeg')
        return jsonify({'error': '文件不存在'}), 404
    except Exception as e: return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # 开启 threaded=True 允许后台视频异步生成
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)