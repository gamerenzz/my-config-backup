import yaml
import json
import os
import base64
import urllib.parse

unique_nodes = {}

def add_node(proxy):
    if not proxy or 'server' not in proxy: return
    key = f"{proxy.get('server')}:{proxy.get('port')}:{proxy.get('type')}"
    if key not in unique_nodes:
        unique_nodes[key] = proxy

def process_files():
    # 1. 解析原有下载的目录 (Alvin9999 的源)
    directories = ['./clash', './xray', './hysteria2', './singbox']
    for directory in directories:
        if os.path.exists(directory):
            for f in os.listdir(directory):
                # ... 这里保留你之前 185 行版本中对各个文件夹的详细解析逻辑 ...
                # 为了篇幅，此处省略具体的 try-except 块，请保持原样
                pass

    # 2. --- 精准提取 extra.yaml 里的“老司机”节点 ---
    if os.path.exists('extra.yaml'):
        try:
            with open('extra.yaml', 'r', encoding='utf-8') as s:
                data = yaml.safe_load(s)
                
                # 第一步：先找到“老司机”这个组包含哪些节点名称
                target_node_names = []
                for group in data.get('proxy-groups', []):
                    if group.get('name') == '老司机':
                        target_node_names = group.get('proxies', [])
                        break
                
                # 第二步：只提取这些指定名称的节点
                if data and 'proxies' in data:
                    for p in data['proxies']:
                        if p.get('name') in target_node_names:
                            # 修改名称前缀，方便识别
                            p['name'] = f"优选-{p.get('type')}-{len(unique_nodes)}"
                            add_node(p)
                            
        except Exception as e:
            print(f"解析 extra.yaml 优选节点失败: {e}")

process_files()

# --- 3. 生成 Clash YAML (极简规则) ---
dynamic_nodes = list(unique_nodes.values())
dynamic_names = [p['name'] for p in dynamic_nodes]

template = {
    "mixed-port": 7890,
    "allow-lan": True,
    "mode": "rule",
    "log-level": "info",
    "unified-delay": True,
    "global-client-fingerprint": "chrome",
    "dns": {
        "enable": True,
        "listen": "0.0.0.0:1053",
        "enhanced-mode": "fake-ip",
        "nameserver": ["223.5.5.5", "119.29.29.29"]
    },
    "proxies": dynamic_nodes,
    "proxy-groups": [
        {"name": "🚀 节点选择", "type": "select", "proxies": ["♻️ 自动选择", "DIRECT"] + dynamic_names},
        {"name": "♻️ 自动选择", "type": "url-test", "url": "http://www.gstatic.com/generate_204", "interval": 300, "proxies": dynamic_names}
    ],
    "rules": [
        "DOMAIN-SUFFIX,cn,DIRECT",
        "GEOIP,LAN,DIRECT",
        "GEOIP,CN,DIRECT",
        "MATCH,🚀 节点选择"
    ]
}

with open('sub.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(template, f, allow_unicode=True, sort_keys=False)


# --- 4. 生成 V2Ray Base64 ---
v2ray_links = []
for node in dynamic_nodes:
    name = urllib.parse.quote(node['name'])
    try:
        if node['type'] == 'vless':
            if 'ws-opts' in node: # 处理 extra.yaml 里的优选节点
                path = urllib.parse.quote(node['ws-opts']['path'])
                v2ray_links.append(f"vless://{node['uuid']}@{node['server']}:{node['port']}?security=tls&sni={node.get('servername',node['server'])}&type=ws&path={path}#{name}")
            else: # 处理 Reality 节点
                path = urllib.parse.quote(node.get('xhttp-opts', {}).get('path', ''))
                v2ray_links.append(f"vless://{node['uuid']}@{node['server']}:{node['port']}?security=reality&sni={node['servername']}&pbk={node['reality-opts']['public-key']}&sid={node['reality-opts']['short-id']}&type={node.get('network','tcp')}&path={path}#{name}")
        elif node['type'] == 'hysteria2':
            v2ray_links.append(f"hysteria2://{node['password']}@{node['server']}:{node['port']}?sni={node['sni']}&insecure=1#{name}")
        elif node['type'] == 'tuic':
            v2ray_links.append(f"tuic://{node['uuid']}:{node['password']}@{node['server']}:{node['port']}?sni={node['sni']}&alpn=h3#{name}")
        elif node['type'] == 'hysteria':
            auth = node.get('auth-str') or node.get('auth_str', '')
            v2ray_links.append(f"hysteria://{node['server']}:{node['port']}?auth={auth}&sni={node['sni']}&alpn=h3&insecure=1#{name}")
        elif node['type'] == 'vmess': # extra.yaml 里有 vmess
            v2_data = {"v": "2", "ps": node['name'], "add": node['server'], "port": node['port'], "id": node['uuid'], "aid": node['alterId'], "net": node['network'], "type": "none", "host": node['ws-opts']['headers']['Host'], "path": node['ws-opts']['path'], "tls": "none"}
            v2ray_links.append(f"vmess://{base64.b64encode(json.dumps(v2_data).encode()).decode()}#{name}")
    except: pass

b64_content = base64.b64encode("\n".join(v2ray_links).encode('utf-8')).decode('utf-8')
with open('v2ray.txt', 'w', encoding='utf-8') as f: f.write(b64_content)
