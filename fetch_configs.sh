#!/bin/bash
# 创建存储目录
mkdir -p clash xray hysteria hysteria2 singbox naiveproxy juicity shadowquic mieru

BASE_URL="https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp"

# 下载函数
download_files() {
    local dir=$1; local count=$2; local filename=$3
    for i in $(seq 1 $count); do
        curl -sL "$BASE_URL/$dir/$i/$filename" -o "$dir/$i.${filename##*.}"
    done
}

# 抓取原有的所有地址
download_files "clash.meta2" 6 "config.yaml"
mv clash.meta2/* clash/ 2>/dev/null || true
download_files "xray" 4 "config.json"
download_files "hysteria" 4 "config.json"
download_files "hysteria2" 4 "config.json"
download_files "singbox" 2 "config.json"
download_files "naiveproxy" 2 "config.json"
download_files "juicity" 2 "config.json"
download_files "shadowquic" 2 "client.yaml"
download_files "mieru" 2 "config.json"

# --- 新增：抓取 data.yaml 数据源 ---
echo "抓取额外数据源..."
curl -sL "https://chg26.makou.cc.cd/" -o extra.yaml

rm -rf clash.meta2
