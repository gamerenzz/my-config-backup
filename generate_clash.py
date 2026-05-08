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

# --- 1. 手动定义 9 个“老司机”优选节点 ---
adult_servers = [
    "visa.com", "www.visa.com", "www.visa.cn", "zoneabc.net", 
    "youxuan.cf.090227.xyz", "www.shopify.com", "store.ubi.com", 
    "cf.tencentapp.cn", "cloudflare-dl.byoip.top"
]

adult_proxies = []
for srv in adult_servers:
    adult_proxies.append({
        "name": f"🔞-{srv}",
        "server": srv,
        "port": 443,
        "type": "vless",
        "uuid": "2d9b713f-29d6-4d08-77fc-68035992bfc0",
        "tls": True,
        "skip-cert-verify": True,
        "servername": "less17.mc2kz.us.ci",
        "network": "ws",
        "ws-opts": {"path": "/", "headers": {"Host": "less17.mc2kz.us.ci"}}
    })

# 解析各个目录
def process_files():
    # 1. 原生 Clash 格式
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

    # 2. Xray (VLESS Reality) 增强版
    xray_path = './xray'
    if os.path.exists(xray_path):
        for f in os.listdir(xray_path):
            try:
                with open(os.path.join(xray_path, f), 'r') as s:
                    data = json.load(s)
                    out = data['outbounds'][0]
                    v = out['settings']['vnext'][0]
                    ss = out['streamSettings']
                    xpath = ss.get('xhttpSettings', {}).get('path') or ss.get('wsSettings', {}).get('path')
                    node = {
                        "name": f"VLESS-Reality-{f}",
                        "type": "vless",
                        "server": v['address'],
                        "port": v['port'],
                        "uuid": v['users'][0]['id'],
                        "cipher": "auto",
                        "tls": True,
                        "udp": True,
                        "servername": ss['realitySettings']['serverName'],
                        "network": ss.get('network', 'tcp'),
                        "reality-opts": {
                            "public-key": ss['realitySettings']['publicKey'],
                            "short-id": ss['realitySettings'].get('shortId', "")
                        },
                        "client-fingerprint": ss['realitySettings'].get('fingerprint', 'chrome')
                    }
                    if ss.get('network') == 'xhttp':
                        node["xhttp-opts"] = {"path": xpath}
                    add_node(node)
            except: pass

    # 3. Hysteria 2
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

    # 4. Sing-box (解析其中的 TUIC, Hysteria2, VLESS Reality 等节点)
    singbox_path = './singbox'
    if os.path.exists(singbox_path):
        for f in os.listdir(singbox_path):
            if not f.endswith('.json'): continue
            try:
                with open(os.path.join(singbox_path, f), 'r') as s:
                    data = json.load(s)
                    for out in data.get('outbounds', []):
                        if out.get('type') == 'tuic':
                            node = {
                                "name": f"Singbox-TUIC-{f}-{out.get('tag', 'node')}",
                                "type": "tuic",
                                "server": out['server'],
                                "port": out['server_port'],
                                "uuid": out.get('uuid'),
                                "password": out.get('password'),
                                "alpn": out.get('tls', {}).get('alpn', ['h3']),
                                "sni": out.get('tls', {}).get('server_name'),
                                "skip-cert-verify": out.get('tls', {}).get('insecure', True),
                                "congestion-controller": out.get("congestion_control", "bbr"),
                                "udp-relay-mode": "native"
                            }
                            add_node(node)
                        elif out.get('type') == 'hysteria2':
                            node = {
                                "name": f"Singbox-Hys2-{f}-{out.get('tag', 'node')}",
                                "type": "hysteria2",
                                "server": out['server'],
                                "port": out['server_port'],
                                "password": out.get("password"),
                                "sni": out.get('tls', {}).get('server_name'),
                                "skip-cert-verify": out.get('tls', {}).get('insecure', True)
                            }
                            add_node(node)
                        elif out.get('type') == 'vless':
                            tls = out.get('tls', {})
                            if tls.get('enabled') and tls.get('reality'):
                                node = {
                                    "name": f"Singbox-VLESS-{f}-{out.get('tag', 'node')}",
                                    "type": "vless",
                                    "server": out['server'],
                                    "port": out['server_port'],
                                    "uuid": out.get('users', [{}])[0].get('uuid'),
                                    "cipher": "auto", "tls": True, "udp": True,
                                    "servername": tls.get('server_name'),
                                    "reality-opts": {
                                        "public-key": tls.get('reality', {}).get('public_key'),
                                        "short-id": tls.get('reality', {}).get('short_id', "")
                                    },
                                    "client-fingerprint": tls.get('utls', {}).get('fingerprint', 'chrome')
                                }
                                add_node(node)
            except: pass

process_files()

# --- 2. 整合所有节点数据 ---
dynamic_nodes = list(unique_nodes.values())
dynamic_names = [p['name'] for p in dynamic_nodes]
adult_names = [p['name'] for p in adult_proxies]
all_proxies = dynamic_nodes + adult_proxies

# --- 3. 生成 Clash YAML ---
template = {
    "mixed-port": 7890,
    "allow-lan": True,
    "mode": "rule",
    "log-level": "info",
    "unified-delay": True,
    "global-client-fingerprint": "chrome",
    "proxies": all_proxies,
    "proxy-groups": [
        {"name": "🚀 节点选择", "type": "select", "proxies": ["♻️ 自动选择", "DIRECT"] + dynamic_names},
        {"name": "♻️ 自动选择", "type": "url-test", "url": "http://www.gstatic.com/generate_204", "interval": 300, "proxies": dynamic_names},
        {"name": "🔞 老司机", "type": "url-test", "url": "https://www.google.com/generate_204", "interval": 300, "proxies": adult_names}
    ],
    "rule-providers": {
        "adults": {
            "type": "http",
            "behavior": "domain",
            "url": "https://raw.githubusercontent.com/fireinrain/porndude-clash-rules/master/adults.txt",
            "interval": 86400,
            "format": "text"
        }
    },
    "rules": [
        "RULE-SET,adults,🔞 老司机",
        "MATCH,🚀 节点选择"
    ]
}
with open('sub.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(template, f, allow_unicode=True, sort_keys=False)

# --- 4. 生成 V2Ray 订阅 (Base64) ---
v2ray_links = []
for node in all_proxies:
    name = urllib.parse.quote(node.get('name', 'node'))
    try:
        if node['type'] == 'vless':
            if 'ws-opts' in node: # 处理老司机 WS 节点
                path = urllib.parse.quote(node['ws-opts']['path'])
                host = node['ws-opts']['headers'].get('Host', node['servername'])
                v2ray_links.append(f"vless://{node['uuid']}@{node['server']}:{node['port']}?security=tls&sni={node['servername']}&type=ws&path={path}&host={host}#{name}")
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
    except: pass

b64_content = base64.b64encode("\n".join(v2ray_links).encode('utf-8')).decode('utf-8')
with open('v2ray.txt', 'w', encoding='utf-8') as f:
    f.write(b64_content)

print(f"处理完成：Clash 节点 {len(all_proxies)} 个，V2Ray 链接 {len(v2ray_links)} 个。")
