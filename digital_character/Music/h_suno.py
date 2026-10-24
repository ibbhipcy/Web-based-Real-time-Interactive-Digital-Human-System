import http.client
import json
import time
import requests

API_KEY = "your_api"

conn = http.client.HTTPSConnection("jmpb-szb.com")
payload = json.dumps({
   "gpt_description_prompt": "一首动听的情歌",
   "make_instrumental": False,
   "mv": "chirp-v4",
   "prompt": "Cat Dance"
})
headers = {
   'Accept': 'application/json',
   'Authorization': f'Bearer {API_KEY}',
   'Content-Type': 'application/json'
}
conn.request("POST", "/suno/submit/music", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
response_text = data.decode("utf-8")

response_dict = json.loads(response_text)
music_id = response_dict["data"]
print(f"提取到的音乐ID: {music_id}")

######################################################################################################################################
# 轮询检测任务状态
print("开始轮询任务状态...")
max_wait_time = 600  # 最大等待时间（秒）
check_interval = 5   # 检查间隔（秒）
start_time = time.time()
timeout = False

while True:
   # 检查是否超时
   current_time = time.time()
   if current_time - start_time > max_wait_time:
      print(f"\n等待超时（{max_wait_time}秒），任务可能仍在处理中")
      timeout = True
      break 
   try:
      # 查询任务状态
      payload = ''
      headers = {
         'Accept': 'application/json',
         'Authorization': f'Bearer {API_KEY}',
         'Content-Type': 'application/json'
      }
      conn.request("GET", f"/suno/fetch/{music_id}", payload, headers)
      res = conn.getresponse()
      data = res.read()
      print(data.decode("utf-8")) ##

      query_data = data.decode("utf-8")
      query_json = json.loads(query_data) ##
      print(query_json)
        
      status = query_json["data"]["status"]
      print(status)
      elapsed = int(current_time - start_time)
        
      print(f"\r已等待 {elapsed} 秒 | 任务状态: {status}", end="", flush=True)
        
      # 检查状态
      if status == "SUCCESS":
         print(f"\n\n音乐生成任务完成！")
         # 提取音乐URL
         audio_url = query_json["data"]["data"][0]["audio_url"]
         if audio_url:
            print(f"音乐URL: {audio_url}")
            # 下载音乐
            response = requests.get(audio_url)
            response.raise_for_status()  # 检查请求是否成功
            with open("audio.mp3", 'wb') as file:
               file.write(response.content)
            print("音乐下载完成！")
            break
         else:
            print("警告：任务完成但返回值未找到音乐URL！")
            break
            
      elif status in ["FAILURE"]:
            print(f"\n\n任务错误相应！")
            break
            
      elif status in ["NOT_START", "SUBMITTED", "QUEUED", "IN_PROGRESS"]:
            # 继续等待
            time.sleep(check_interval)
            
      else:
            print(f"\n未知状态: {status}")
            time.sleep(check_interval)
            
      conn.close()
        
   except Exception as e:
      print(f"\n查询状态时出错: {e}")
      time.sleep(check_interval)

########################################################################################################################################