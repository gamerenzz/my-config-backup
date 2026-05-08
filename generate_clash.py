import yaml
import json
import os
import base64
import urllib.parse

unique_nodes = {}

def add_node(proxy):
    if not proxy or 'server' not in proxy: return
    # 去重逻辑：基于 服务器、端口、协议类型
    key = f"{proxy.get('server')}:{proxy.get('port')}:{proxy.get('type')}"
    if key not in unique_nodes:
        unique_nodes[key] = proxy

def process_files():
    # --- 1. 解析 clash 目录 ---
    clash_path = './clash'
    if os.path.exists(clash_path):
        for f in os.listdir(clash_path):
            try:
                with open(os.path.join(clash_path, f), 'r') as s:
                    data = yaml.safe_load(s)
                    if data and 'proxies' in data:
                        for p in data['proxies']:
                            p['name'] = f"Clash-{p['type']}-{len(unique_nodes)}"
                            add_node(p)
            except: pass

    # --- 2. 解析 xray 目录 (VLESS Reality) ---
    xray_path = './xray'
    if os.path.exists(xray_path):
        for f in os.listdir(xray_path):
            try:
                with open(os.path.join(xray_path, f), 'r', encoding='utf-8') as s:
                    data = json.load(s)
                    out = data['outbounds'][0]
                    v = out['settings']['vnext'][0]
                    ss = out['streamSettings']
                    xpath = ss.get('xhttpSettings', {}).get('path') or ss.get('wsSettings', {}).get('path')
                    node = {
                        "name": f"VLESS-Reality-{f}",
                        "type": "vless",
                        "server": v['address'], "port": v['port'], "uuid": v['users'][0]['id'],
                        "cipher": "auto", "tls": True, "udp": True,
                        "servername": ss['realitySettings']['serverName'],
                        "network": ss.get('network', 'tcp'),
                        "reality-opts": {"public-key": ss['realitySettings']['publicKey'], "short-id": ss['realitySettings'].get('shortId', "")},
                        "client-fingerprint": ss['realitySettings'].get('fingerprint', 'chrome')
                    }
                    if ss.get('network') == 'xhttp': node["xhttp-opts"] = {"path": xpath}
                    add_node(node)
            except: pass

    # --- 3. 解析 hysteria (v1) 目录 ---
    h1_path = './hysteria'
    if os.path.exists(h1_path):
        for f in os.listdir(h1_path):
            try:
                with open(os.path.join(h1_path, f), 'r') as s:
                    data = json.load(s)
                    addr_port = data['server'].split(':')
                    node = {
                        "name": f"Hys1-{f}",
                        "type": "hysteria",
                        "server": addr_port[0], "port": int(addr_port[1]),
                        "auth_str": data.get("auth_str"),
                        "up": "10 Mbps", "down": "50 Mbps",
                        "sni": data.get("server_name", "apple.com"),
                        "alpn": ["h3"], "protocol": "udp", "skip-cert-verify": True
                    }
                    add_node(node)
            except: pass

    # --- 4. 解析 hysteria2 目录 ---
    h2_path = './hysteria2'
    if os.path.exists(h2_path):
        for f in os.listdir(h2_path):
            try:
                with open(os.path.join(h2_path, f), 'r') as s:
                    data = json.load(s)
                    addr_port = data['server'].split(',')[0].split(':')
                    node = {
                        "name": f"Hys2-{f}",
                        "type": "hysteria2",
                        "server": addr_port[0].replace('[','').replace(']',''),
                        "port": int(addr_port[1]),
                        "password": data.get("auth"),
                        "sni": data['tls']['sni'],
                        "skip-cert-verify": True
                    }
                    add_node(node)
            except: pass

    # --- 5. 解析 singbox 目录 (TUIC) ---
    sb_path = './singbox'
    if os.path.exists(sb_path):
        for f in os.listdir(sb_path):
            try:
                with open(os.path.join(sb_path, f), 'r') as s:
                    data = json.load(s)
                    for out in data.get('outbounds', []):
                        if out.get('type') == 'tuic':
                            node = {
                                "name": f"Singbox-TUIC-{f}",
                                "type": "tuic",
                                "server": out['server'], "port": out['server_port'],
                                "uuid": out['uuid'], "password": out['password'],
                                "alpn": ["h3"], "sni": out['tls']['server_name'],
                                "skip-cert-verify": True, "udp-relay-mode": "native"
                            }
                            add_node(node)
            except: pass

    # --- 6. 解析 extra.yaml (包含优选节点) ---
    if os.path.exists('extra.yaml'):
        try:
            with open('extra.yaml', 'r', encoding='utf-8') as s:
                data = yaml.safe_load(s)
                if data and 'proxies' in data:
                    for p in data['proxies']:
                        p['name'] = f"Extra-{p.get('type')}-{len(unique_nodes)}"
                        add_node(p)
        except: pass

process_files()

# --- 生成 Clash YAML ---
all_nodes = list(unique_nodes.values())
node_names = [p['name'] for p in all_nodes]

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
    "proxies": all_nodes,
    "proxy-groups": [
        {"name": "🚀 节点选择", "type": "select", "proxies": ["♻️ 自动选择", "DIRECT"] + node_names},
        {"name": "♻️ 自动选择", "type": "url-test", "url": "http://www.gstatic.com/generate_204", "interval": 300, "proxies": node_names}
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

# --- 生成 V2Ray Base64 ---
v2ray_links = []
for node in all_nodes:
    name = urllib.parse.quote(node['name'])
    try:
        if node['type'] == 'vless':
            if 'ws-opts' in node: # 优选节点
                v2ray_links.append(f"vless://{node['uuid']}@{node['server']}:{node['port']}?security=tls&sni={node['servername']}&type=ws&path={urllib.parse.quote(node['ws-opts']['path'])}#{name}")
            else: # Reality
                xpath = urllib.parse.quote(node.get('xhttp-opts', {}).get('path', ''))
                v2ray_links.append(f"vless://{node['uuid']}@{node['server']}:{node['port']}?security=reality&sni={node['servername']}&pbk={node['reality-opts']['public-key']}&sid={node['reality-opts']['short-id']}&type={node.get('network','tcp')}&path={xpath}#{name}")
        elif node['type'] == 'hysteria2':
            v2ray_links.append(f"hysteria2://{node['password']}@{node['server']}:{node['port']}?sni={node['sni']}&insecure=1#{name}")
        elif node['type'] == 'tuic':
            v2ray_links.append(f"tuic://{node['uuid']}:{node['password']}@{node['server']}:{node['port']}?sni={node['sni']}&alpn=h3#{name}")
        elif node['type'] == 'hysteria':
            auth = node.get('auth-str') or node.get('auth_str', '')
            v2ray_links.append(f"hysteria://{node['server']}:{node['port']}?auth={auth}&sni={node['sni']}&alpn=h3&insecure=1#{name}")
        elif node['type'] == 'vmess':
            v2_data = {"v": "2", "ps": node['name'], "add": node['server'], "port": node['port'], "id": node['uuid'], "aid": node['alterId'], "net": node['network'], "type": "none", "host": node['ws-opts']['headers'].get('Host',''), "path": node['ws-opts']['path'], "tls": "none"}
            v2ray_links.append(f"vmess://{base64.b64encode(json.dumps(v2_data).encode()).decode()}#{name}")
    except: pass

b64_content = base64.b64encode("\n".join(v2ray_links).encode('utf-8')).decode('utf-8')
with open('v2ray.txt', 'w', encoding='utf-8') as f: f.write(b64_content)
