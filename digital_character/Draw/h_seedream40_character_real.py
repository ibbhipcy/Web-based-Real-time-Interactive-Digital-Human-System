import http.client
import json
import requests

def generate_character_image(hair, figure, facial, appearance):
    """
    根据描述生成数字人图片
    
    参数:
        hair (str): 头发细节（长短发，发色，发型，刘海，配饰）
        figure (str): 整体特征（性别，身高，胖瘦，健壮与否，肤色）
        facial (str): 五官信息（大小形状，颜色，相对位置）
        appearance (str): 穿搭细节（颜色搭配，形制，配饰）
    
    返回:
        str: 成功返回图片URL，失败返回None
    """
    API_KEY = "your_api"
    
    conn = http.client.HTTPSConnection("jmpb-szb.com")
    
    payload = json.dumps({
        "model": "doubao-seedream-4-0-250828",
        "prompt": f"生成一个3D建模风的人物半身像，正面视角。从头到大腿腰部的人物半身像。皮克斯工作室风格，色调柔和，有精细的光泽。头发：{hair}；身材：{figure}；五官：{facial}；服饰：{appearance}。极简纯色背景，无任何文字、水印、多余装饰。3D渲染，OC渲染器，柔焦。",
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
            with open("character_url.txt", "w", encoding="utf-8") as url_file:
                url_file.write(image_url)
            
            print(f"图片生成成功！")
            print(f"图片URL: {image_url}")
            print(f"图片尺寸: {response_json['data'][0].get('size')}")
            print(f"URL已保存到: character_url.txt")
            
            return image_url
        else:
            print("生成失败：响应中未找到图片数据")
            return None
            
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return None
        
    finally:
        conn.close()