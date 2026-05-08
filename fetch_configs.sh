#!/bin/bash

# 定义基础路径和目标文件夹的映射
# 格式: "URL路径关键字|本地存储文件夹|文件后缀|数量"
targets=(
    "clash.meta2|clash|yaml|6"
    "xray|xray|json|4"
    "hysteria|hysteria|json|4"
    "singbox|singbox|json|4"
    "naiveproxy|naiveproxy|json|2"
    "hysteria2|hysteria2|json|4"
    "juicity|juicity|json|2"
    "shadowquic|shadowquic|yaml|2"
)

BASE_URL="https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp"

for item in "${targets[@]}"; do
    IFS="|" read -r key folder ext count <<< "$item"
    
    # 创建文件夹
    mkdir -p "$folder"
    
    for i in $(seq 1 $count); do
        # 特殊处理文件名（shadowquic 是 client.yaml，其他通常是 config.json/yaml）
        filename="config.$ext"
        if [ "$key" == "shadowquic" ]; then
            filename="client.yaml"
        fi

        URL="$BASE_URL/$key/$i/$filename"
        echo "正在下载: $URL"
        
        # 下载并保存，保存的文件名带上编号
        curl -sL "$URL" -o "$folder/$i.$ext"
    done
done
