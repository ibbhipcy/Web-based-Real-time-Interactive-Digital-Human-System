import http.client
import json

def chat_stream_generator(user_message, history=[]):
    API_KEY = "your_api"
    conn = http.client.HTTPSConnection("jmpb-szb.com")
    
    input_messages = []
    for msg in history:
        input_messages.append({"role": msg["role"], "content": msg["content"]})
    input_messages.append({"role": "user", "content": user_message})
    
    payload = json.dumps({
       "model": "gpt-4.1",
       "stream": True,
       "input": input_messages
    })
    
    headers = {
       'Accept': 'application/json',
       'Authorization': f'Bearer {API_KEY}',
       'Content-Type': 'application/json'
    }
    
    try:
        conn.request("POST", "/v1/responses", payload, headers)
        res = conn.getresponse()
        
        for line in res:
            line = line.decode('utf-8').strip()
            if not line: continue
            if line.startswith('data: '):
                chunk = line[6:]
                if chunk == '[DONE]': break
                try:
                    data = json.loads(chunk)
                    if "delta" in data:
                        # 兼容处理：如果是标准 responses，字段是 text；如果是 chat/completions，字段是 content
                        if "text" in data["delta"]:
                            yield data["delta"]["text"]
                        elif "content" in data["delta"] and data["delta"]["content"]:
                            yield data["delta"]["content"]
                except json.JSONDecodeError:
                    pass
        conn.close()
    except Exception as e:
        print(f"流式对话模型请求失败: {e}")
        yield "抱歉，我的大脑连线出了点问题。"