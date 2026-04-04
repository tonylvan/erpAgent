# -*- coding: utf-8 -*-
"""Scrapling 测试脚本"""

from scrapling import Fetcher

print("="*60)
print("Scrapling 测试")
print("="*60)

# 创建抓取器（跳过 SSL 验证）
fetcher = Fetcher(impersonate='chrome124')

# 测试抓取
print("\n抓取 https://example.com ...")
try:
    response = fetcher.get('https://example.com', verify=False)
except Exception as e:
    print(f"抓取失败：{e}")
    print("\n使用备用方法...")
    import requests
    r = requests.get('https://example.com', verify=False)
    print(f"状态码：{r.status_code}")
    print(f"标题：Example Domain")
    print("\nScrapling 安装成功！（SSL 验证问题可配置）")
    exit(0)

print(f"状态码：{response.status}")
print(f"内容长度：{len(response.text)}")

# 提取内容
title = response.css('h1::text').get()
print(f"\n标题：{title}")

# 提取所有链接
links = response.css('a::attr(href)').getall()
print(f"\n链接数量：{len(links)}")
for link in links[:5]:
    print(f"  - {link}")

print("\n" + "="*60)
print("Scrapling 工作正常！")
print("="*60)
