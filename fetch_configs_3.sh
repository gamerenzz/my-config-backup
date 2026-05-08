#!/bin/bash
# 创建存储目录 (增加了 mieru)
mkdir -p clash xray hysteria hysteria2 singbox naiveproxy juicity shadowquic mieru

BASE_URL="https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp"

# 定义下载函数：目录名 数量 文件名
download_files() {
    local dir=$1
    local count=$2
    local filename=$3
    for i in $(seq 1 $count); do
        echo "正在下载 $dir/$i..."
        curl -sL "$BASE_URL/$dir/$i/$filename" -o "$dir/$i.${filename##*.}"
    done
}

# 1. 下载 Clash 配置 (6个)
download_files "clash.meta2" 6 "config.yaml"
mv clash.meta2/* clash/ 2>/dev/null || true

# 2. 下载 Xray 配置 (4个)
download_files "xray" 4 "config.json"

# 3. 下载 Hysteria 1 配置 (4个)
download_files "hysteria" 4 "config.json"

# 4. 下载 Hysteria 2 配置 (4个)
download_files "hysteria2" 4 "config.json"

# 5. 下载 Sing-box 配置 (已改为 2 个)
download_files "singbox" 2 "config.json"

# 6. 下载 NaiveProxy 配置 (2个)
download_files "naiveproxy" 2 "config.json"

# 7. 下载 Juicity 配置 (2个)
download_files "juicity" 2 "config.json"

# 8. 下载 ShadowQUIC 配置 (2个)
download_files "shadowquic" 2 "client.yaml"

# 9. 下载 Mieru 配置 (新增 2 个)
download_files "mieru" 2 "config.json"

# 清理空目录
rm -rf clash.meta2
