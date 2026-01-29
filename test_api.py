import requests

url = "https://down.mptext.top/api/public/v1/download?url=https://mp.weixin.qq.com/s/tr38EieqyftubIx2FMWUWw&format=markdown"

payload={}
headers = {
  'X-Auth-Key': 'b975c9e0308d4a55afb2392990e060fd'
}

response = requests.request("GET", url, headers=headers, data=payload)

print("响应状态码:", response.status_code)
print("响应内容:", response.text[:500], "...")

# 测试搜索公众号接口
search_url = "https://down.mptext.top/api/public/v1/account"
search_params = {
    "keyword": "财联社",
    "page": 1,
    "page_size": 20
}

search_response = requests.request("GET", search_url, headers=headers, params=search_params)
print("\n搜索公众号响应状态码:", search_response.status_code)
print("搜索公众号响应内容:", search_response.text[:500], "...")
