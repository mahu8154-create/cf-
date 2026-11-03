import os
import requests

# 从环境变量读取配置
API_TOKEN = os.environ.get("CF_API_TOKEN")
ZONE_ID = os.environ.get("CF_ZONE_ID")
RECORD_NAME = os.environ.get("RECORD_NAME")  # 例如 cdn.yourdomain.com

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

def get_best_ip():
    # 从测速生成的 result.txt 中读取第一个（最优）IP
    if not os.path.exists("result.txt"):
        print("未找到测速结果文件")
        return None
    with open("result.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) > 1:
            # CSV 格式第一行是标题，第二行是数据，IP 在第一列
            best_ip = lines[1].split(",")[0].strip()
            return best_ip
    return None

def update_dns(ip):
    # 1. 查找该子域名的 DNS 记录 ID
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?name={RECORD_NAME}&type=A"
    response = requests.get(url, headers=headers).json()
    
    if not response['result']:
        print(f"未找到对应的 DNS 记录: {RECORD_NAME}，请先在 Cloudflare 创建一条 A 记录")
        return
        
    record_id = response['result'][0]['id']
    
    # 2. 更新 DNS 记录为最新的优选 IP
    update_url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}"
    data = {
        "type": "A",
        "name": RECORD_NAME,
        "content": ip,
        "ttl": 60,
        "proxied": False  # 优选 IP 必须关闭代理（即灰云）
    }
    update_res = requests.put(update_url, headers=headers, json=data).json()
    if update_res.get("success"):
        print(f"成功将 {RECORD_NAME} 更新为优选 IP: {ip}")
    else:
        print(f"更新失败: {update_res.get('errors')}")

if __name__ == "__main__":
    ip = get_best_ip()
    if ip:
        print(f"获取到最优 IP: {ip}")
        update_dns(ip)
    else:
        print("未能获取优选 IP")
