import yaml
import json
import os

unique_nodes = {}

def add_node(proxy):
    if not proxy or 'server' not in proxy: return
    # 去重逻辑：基于 服务器、端口、协议类型
    key = f"{proxy.get('server')}:{proxy.get('port')}:{proxy.get('type')}"
    if key not in unique_nodes:
        unique_nodes[key] = proxy

# 解析各个目录
def process_files():
    # 1. 原生 Clash 格式
    for f in os.listdir('./clash'):
        try:
            with open(f'./clash/{f}', 'r') as s:
                data = yaml.safe_load(s)
                if data and 'proxies' in data:
                    for p in data['proxies']:
                        p['name'] = f"Clash-{p['type']}-{len(unique_nodes)}"
                        add_node(p)
        except: pass

    # 2. Xray (VLESS Reality)
    for f in os.listdir('./xray'):
        try:
            with open(f'./xray/{f}', 'r') as s:
                data = json.load(s)
                out = data['outbounds'][0]
                v = out['settings']['vnext'][0]
                ss = out['streamSettings']
                node = {
                    "name": f"VLESS-Reality-{f}",
                    "type": "vless",
                    "server": v['address'],
                    "port": v['port'],
                    "uuid": v['users'][0]['id'],
                    "cipher": "auto", "tls": True, "udp": True,
                    "servername": ss['realitySettings']['serverName'],
                    "network": ss.get('network', 'tcp'),
                    "reality-opts": {"public-key": ss['realitySettings']['publicKey'], "short-id": ss['realitySettings'].get('shortId', "")},
                    "client-fingerprint": ss['realitySettings'].get('fingerprint', 'chrome')
                }
                add_node(node)
        except: pass

    # 3. Hysteria 2
    for f in os.listdir('./hysteria2'):
        try:
            with open(f'./hysteria2/{f}', 'r') as s:
                data = json.load(s)
                addr_port = data['server'].split(',')[0].split(':')
                node = {
                    "name": f"Hysteria2-{f}",
                    "type": "hysteria2",
                    "server": addr_port[0].replace('[','').replace(']',''),
                    "port": int(addr_port[1]),
                    "password": data.get("auth"),
                    "sni": data['tls']['sni'],
                    "skip-cert-verify": True
                }
                add_node(node)
        except: pass

    # 4. Sing-box (解析其中的 TUIC 节点)
    for f in os.listdir('./singbox'):
        try:
            with open(f'./singbox/{f}', 'r') as s:
                data = json.load(s)
                for out in data.get('outbounds', []):
                    if out['type'] == 'tuic':
                        node = {
                            "name": f"TUIC-{f}",
                            "type": "tuic",
                            "server": out['server'],
                            "port": out['server_port'],
                            "uuid": out['uuid'],
                            "password": out['password'],
                            "alpn": out['tls']['alpn'],
                            "sni": out['tls']['server_name'],
                            "skip-cert-verify": True
                        }
                        add_node(node)
        except: pass

process_files()

# 生成最终 YAML
template = {
    "mixed-port": 7890,
    "allow-lan": True,
    "mode": "rule",
    "log-level": "info",
    "proxies": list(unique_nodes.values()),
    "proxy-groups": [
        {"name": "🚀 节点选择", "type": "select", "proxies": ["♻️ 自动选择", "DIRECT"] + [p['name'] for p in unique_nodes.values()]},
        {"name": "♻️ 自动选择", "type": "fallback", "url": "http://www.gstatic.com/generate_204", "interval": 300, "proxies": [p['name'] for p in unique_nodes.values()]}
    ],
    "rules": ["MATCH,🚀 节点选择"]
}

with open('sub.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(template, f, allow_unicode=True, sort_keys=False)
