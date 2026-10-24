import http.client
import json
import requests

def generate_background_image(background_description):
    """
    根据描述生成背景图片
    
    参数:
        background_description (str): 背景描述（室内/室外，什么场所，有什么景观，什么视角）
    
    返回:
        str: 成功返回图片URL，失败返回None
    """
    API_KEY = "your_api"
    
    conn = http.client.HTTPSConnection("jmpb-szb.com")
    
    payload = json.dumps({
        "model": "doubao-seedream-4-0-250828",
        "prompt": f"{background_description}。结合赛璐璐的清晰线条与柔和光影、日系二次元画风和中国唐朝、宋朝或者明朝经典建筑风格。平视视角。不要出现任何文字。",
        "size": "4096x2304",
        "sequential_image_generation": "auto",
        "stream": False,
        "response_format": "url",
        "watermark": True
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
            with open("background_url.txt", "w", encoding="utf-8") as url_file:
                url_file.write(image_url)
            
            print(f"图片生成成功！")
            print(f"图片URL: {image_url}")
            print(f"图片尺寸: {response_json['data'][0].get('size')}")
            print(f"URL已保存到: background_url.txt")
            
            return image_url
        else:
            print("生成失败：响应中未找到图片数据")
            return None
            
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return None
        
    finally:
        conn.close()