import http.client
import json
import time
import requests

def generate_animation_video(image_url, action_prompt="挥手，打招呼，微笑"):
    API_KEY = "your_api"
    try:
        # 每次调用新建连接，防止后台多线程冲突
        conn = http.client.HTTPSConnection("jmpb-szb.com")
        payload = json.dumps({
            "prompt": action_prompt,
            "model": "veo3-fast-frames",
            "images": [image_url, image_url],
            "enhance_prompt": True,
            "enable_upsample": False,
            "aspect_ratio": "16:9"
        })
        headers = {'Accept': 'application/json', 'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
        
        conn.request("POST", "/v1/video/create", payload, headers)
        res = conn.getresponse()
        TASK_ID = json.loads(res.read().decode("utf-8")).get("id")
        conn.close()
        if not TASK_ID: return None
            
        max_wait_time = 600
        start_time = time.time()
        
        while True:
            if time.time() - start_time > max_wait_time: return None
            try:
                # 轮询时也每次新建连接
                q_conn = http.client.HTTPSConnection("jmpb-szb.com")
                headers_q = {'Accept': 'application/json', 'Authorization': f'Bearer {API_KEY}', 'content-type': 'multipart/form-data; boundary='}
                q_conn.request("GET", f"/v1/video/query?id={TASK_ID}", "", headers_q)
                res_q = q_conn.getresponse()
                query_json = json.loads(res_q.read().decode("utf-8"))
                q_conn.close()
                
                status = query_json.get("status")
                if status == "completed":
                    video_url = query_json.get("video_url")
                    if video_url:
                        response = requests.get(video_url)
                        video_filename = f"video_{int(time.time())}_{int(time.time()*1000)%1000}.mp4"
                        with open(video_filename, 'wb') as file:
                            file.write(response.content)
                        return video_filename
                    return None
                elif status in ["error", "video_generation_failed", "failed"]:
                    return None
                time.sleep(5)
            except Exception:
                time.sleep(5)
    except Exception as e:
        print(f"生成动画视频时发生错误: {e}")
        return None