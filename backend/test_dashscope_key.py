# -*- coding: utf-8 -*-
import os
import dashscope
from dashscope import Generation

# Load from .env file
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        if 'DASHSCOPE_API_KEY' in line:
            key = line.strip().split('=')[1]
            print(f"API Key from .env: {key}")
            print(f"Key length: {len(key)}")
            print(f"Key starts with: {key[:10]}...")
            
            # Test the key
            dashscope.api_key = key
            r = Generation.call(
                model='qwen-plus',
                messages=[{'role': 'user', 'content': '你好，请用中文回答'}],
                result_format='message'
            )
            
            print(f"\nTest call status: {r.status_code}")
            if r.status_code == 200:
                print(f"Response: {r.output.choices[0].message.content}")
            else:
                print(f"Error: {r.code} - {r.message}")
            break
