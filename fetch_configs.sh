#!/bin/bash

# 创建存储目录
mkdir -p clash xray hysteria hysteria2 singbox naiveproxy juicity shadowquic mieru

BASE_URL="https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp"

# 下载函数：dir_name, count, target_filename
download_files() {
    local dir=$1; local count=$2; local filename=$3
    for i in $(seq 1 $count); do
        curl -sL "$BASE_URL/$dir/$i/$filename" -o "$dir/$i.${filename##*.}"
    done
}

# 抓取 Alvin 源
echo "正在抓取 Alvin 节点..."
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

# --- 容错处理：抓取 extra.yaml ---
# 先删除旧文件，防止下载失败后读取过时数据
rm -f extra.yaml
echo "正在尝试抓取额外优选源 (makou.cc.cd)..."
# -f 让 curl 在 HTTP 错误(如404)时直接报错不保存文件
curl -sLf "https://chg26.makou.cc.cd/" -o extra.yaml || echo "警告：额外优选源下载失败，将跳过该源。"

# 清理空目录
rm -rf clash.meta2
echo "下载阶段完成。"
