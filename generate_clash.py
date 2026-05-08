import yaml
import json
import os

# 配置读取路径
BASE_DIR = "./"
OUTPUT_FILE = "sub.yaml"

# Clash 基础模板
template = {
    "mixed-port": 7890,
    "allow-lan": True,
    "log-level": "info",
    "dns": {
        "enabled": True,
        "nameserver": ["119.29.29.29", "223.5.5.5"],
        "fallback": ["8.8.8.8", "1.1.1.1"]
    },
    "proxies": [],
    "proxy-groups": [
        {"name": "🚀 节点选择", "type": "select", "proxies": ["♻️ 自动选择", "DIRECT"]},
        {"name": "♻️ 自动选择", "type": "fallback", "url": "http://www.gstatic.com/generate_204", "interval": 300, "proxies": []}
    ],
    "rules": ["MATCH,🚀 节点选择"]
}

unique_nodes = {}

def add_node(proxy):
    # 使用 server+port+name 做去重 key
    key = f"{proxy.get('server')}:{proxy.get('port')}:{proxy.get('type')}"
    if key not in unique_nodes:
        unique_nodes[key] = proxy

# 1. 解析 Clash YAML
clash_path = os.path.join(BASE_DIR, "clash")
if os.path.exists(clash_path):
    for f in os.listdir(clash_path):
        try:
            with open(os.path.join(clash_path, f), 'r') as stream:
                data = yaml.safe_load(stream)
                if data and 'proxies' in data:
                    for p in data['proxies']:
                        add_node(p)
        except: continue

# 2. 解析 Hysteria 1 JSON
h1_path = os.path.join(BASE_DIR, "hysteria")
if os.path.exists(h1_path):
    for f in os.listdir(h1_path):
        try:
            with open(os.path.join(h1_path, f), 'r') as stream:
                data = json.load(stream)
                addr, port = data['server'].split(':')
                node = {
                    "name": f"Hysteria1-{f}",
                    "type": "hysteria",
                    "server": addr,
                    "port": int(port),
                    "auth_str": data.get("auth_str"),
                    "up": str(data.get("up_mbps", 10)),
                    "down": str(data.get("down_mbps", 50)),
                    "sni": data.get("server_name"),
                    "skip-cert-verify": data.get("insecure", True)
                }
                add_node(node)
        except: continue

# 3. 解析 Hysteria 2 JSON
h2_path = os.path.join(BASE_DIR, "hysteria2")
if os.path.exists(h2_path):
    for f in os.listdir(h2_path):
        try:
            with open(os.path.join(h2_path, f), 'r') as stream:
                data = json.load(stream)
                # 处理带端口范围的情况，只取第一个
                addr_full = data['server'].split(',')[0]
                addr, port = addr_full.split(':')
                node = {
                    "name": f"Hysteria2-{f}",
                    "type": "hysteria2",
                    "server": addr,
                    "port": int(port),
                    "password": data.get("auth"),
                    "sni": data.get("tls", {}).get("sni"),
                    "skip-cert-verify": data.get("tls", {}).get("insecure", True)
                }
                add_node(node)
        except: continue

# 4. 解析 Xray VLESS Reality (针对 Mihomo)
xray_path = os.path.join(BASE_DIR, "xray")
if os.path.exists(xray_path):
    for f in os.listdir(xray_path):
        try:
            with open(os.path.join(xray_path, f), 'r') as stream:
                data = json.load(stream)
                outbound = data['outbounds'][0]
                vnext = outbound['settings']['vnext'][0]
                stream_settings = outbound['streamSettings']
                node = {
                    "name": f"VLESS-{f}",
                    "type": "vless",
                    "server": vnext['address'],
                    "port": vnext['port'],
                    "uuid": vnext['users'][0]['id'],
                    "cipher": "auto",
                    "tls": True,
                    "udp": True,
                    "servername": stream_settings['realitySettings']['serverName'],
                    "network": stream_settings['network'],
                    "reality-opts": {
                        "public-key": stream_settings['realitySettings']['publicKey'],
                        "short-id": stream_settings['realitySettings'].get('shortId', "")
                    },
                    "client-fingerprint": stream_settings['realitySettings'].get('fingerprint', "chrome")
                }
                add_node(node)
        except: continue

# 5. 合并并生成文件
template['proxies'] = list(unique_nodes.values())
node_names = [p['name'] for p in template['proxies']]
template['proxy-groups'][0]['proxies'].extend(node_names)
template['proxy-groups'][1]['proxies'].extend(node_names)

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    yaml.dump(template, f, allow_unicode=True, sort_keys=False)

print(f"成功生成订阅，共 {len(template['proxies'])} 个节点。")
