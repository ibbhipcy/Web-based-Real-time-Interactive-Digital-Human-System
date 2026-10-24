import http.client
import json
import os
import requests

def mix_character_background():
    """
    将character_url.txt中的人物融合到background_url.txt的背景中
    
    返回:
        str: 成功返回融合后的图片URL，失败返回None
    """
    API_KEY = "your_api"
    
    # 检查文件是否存在
    if not os.path.exists("character_url.txt"):
        print("错误：character_url.txt 文件不存在")
        return None
    
    if not os.path.exists("background_url.txt"):
        print("错误：background_url.txt 文件不存在")
        return None
    
    # 读取URL
    try:
        with open("character_url.txt", "r", encoding="utf-8") as f:
            character_url = f.read().strip()
        
        with open("background_url.txt", "r", encoding="utf-8") as f:
            background_url = f.read().strip()
    except Exception as e:
        print(f"读取URL文件时发生错误: {e}")
        return None
    
    conn = http.client.HTTPSConnection("jmpb-szb.com")
    
    payload = json.dumps({
        "model": "doubao-seedream-4-5-251128",
        "prompt": "将图1的人物融合到图2的正中间，仔细考虑光影、透视等等关系，不要对图1的人物形象和图二做任何细节改动",
        "image": [
            character_url,
            background_url
        ],
        "sequential_image_generation": "disabled",
        "size": "4096x2304",
        "watermark": False
    })
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        conn.request("POST", "/v1/images/generations", payload, headers)
        res = conn.getresponse()
        data = res.read()
        response_json = json.loads(data.decode("utf-8"))
        
        # 提取图片URL
        if "data" in response_json and len(response_json["data"]) > 0:
            image_url = response_json["data"][0]["url"]
            
            # 保存URL到文件
            with open("mix_url.txt", "w", encoding="utf-8") as url_file:
                url_file.write(image_url)
            
            print(f"图片生成成功！")
            print(f"图片URL: {image_url}")
            print(f"图片尺寸: {response_json['data'][0].get('size')}")
            print(f"URL已保存到: mix_url.txt")
            
            return image_url
        else:
            print("生成失败：响应中未找到图片数据")
            return None
            
    except Exception as e:
        print(f"融合图片时发生错误: {e}")
        return None
        
    finally:
        conn.close()


# if "data" in response_json and len(response_json["data"]) > 0:
#     image_url = response_json["data"][0]["url"]
#     r = requests.get(image_url)
#     with open("mix_image.jpg", "wb") as f:
#         f.write(r.content)
#     print("图片已下载到当前文件夹: mix_image.jpg")