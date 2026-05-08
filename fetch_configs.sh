#!/bin/bash
# 创建存储目录
mkdir -p clash xray hysteria hysteria2 singbox naiveproxy juicity shadowquic

BASE_URL="https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp"

# 定义下载函数：目录名 数量 文件名
download_files() {
    local dir=$1
    local count=$2
    local filename=$3
    for i in $(seq 1 $count); do
        echo "下载 $dir/$i..."
        curl -sL "$BASE_URL/$dir/$i/$filename" -o "$dir/$i.${filename##*.}"
    done
}

# 开始下载
download_files "clash.meta2" 6 "config.yaml"
# 把下载的 clash.meta2 移动/改名到目标文件夹
mv clash.meta2/* clash/ 2>/dev/null || true

download_files "xray" 4 "config.json"
download_files "hysteria" 4 "config.json"
download_files "hysteria2" 4 "config.json"
download_files "singbox" 4 "config.json"
download_files "naiveproxy" 2 "config.json"
download_files "juicity" 2 "config.json"
download_files "shadowquic" 2 "client.yaml"
