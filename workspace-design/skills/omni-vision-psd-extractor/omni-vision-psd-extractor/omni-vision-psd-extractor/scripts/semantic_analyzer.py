#!/usr/bin/env python3
import base64
import json
import os
import urllib.request
import urllib.error
import concurrent.futures
from pathlib import Path

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_layer(layer, api_key, base_url, model):
    ref_path = layer.get("ref_path")
    if not ref_path or not os.path.exists(ref_path):
        return layer
    
    group = layer.get("group")
    if group == "05_SUBJECT":
        prompt_text = "请分析这张图片中的主要人物、角色或物品（IP）。请用极其简静的一句话（20字以内）描述它的核心物理特征（例如：‘穿着红色衣服的小女孩，正举起右手，姿态是站立的’）。不要任何解释，只输出特征描述。"
    elif group in ("03_TITLE", "02_LOGO"):
        prompt_text = "请精准识别这张图片中的所有文字内容（OCR）和核心图形元素。如果有文字，请准确提取并输出（例如：‘文字：购买立享折扣’）。如果没有任何可识别内容，请回复‘无’。请用最简短的话输出，严禁啰嗦。"
    else:
        return layer

    try:
        base64_image = encode_image(ref_path)
    except Exception as e:
        print(f"[semantic_analyzer] Error reading image {ref_path}: {e}")
        return layer

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 100,
        "temperature": 0.2
    }
    
    url = f"{base_url.rstrip('/')}/chat/completions"
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    try:
        print(f"[semantic_analyzer] Sending Vision request for layer {layer.get('key')}...")
        with urllib.request.urlopen(req, timeout=45) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['choices'][0]['message']['content'].strip()
            print(f"[semantic_analyzer] Result for {layer.get('key')}: {text}")
            layer["semantic_features"] = text
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"[semantic_analyzer] HTTP Error for {layer.get('key')}: {e.code} - {error_body}")
        layer["semantic_features"] = ""
    except Exception as e:
        print(f"[semantic_analyzer] Error for {layer.get('key')}: {e}")
        layer["semantic_features"] = ""
        
    return layer

def enrich_manifest(manifest):
    api_key = os.getenv("OPENAI_API_KEY", os.getenv("GPT_API_KEY", ""))
    if not api_key:
        print("[semantic_analyzer] Warning: GPT_API_KEY / OPENAI_API_KEY not found in environment. Skipping semantic analysis.")
        return manifest
        
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-5.4"))
    
    layers = manifest.get("layers", [])
    
    print(f"[semantic_analyzer] Starting VLM enrichment with model {model} at {base_url}...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_layer = {}
        for layer in layers:
            group = layer.get("group")
            if group in ("05_SUBJECT", "03_TITLE", "02_LOGO"):
                future = executor.submit(analyze_layer, layer, api_key, base_url, model)
                future_to_layer[future] = layer
                
        for future in concurrent.futures.as_completed(future_to_layer):
            pass # the layer dict is modified in place
            
    print("[semantic_analyzer] Enrichment completed.")
    return manifest
