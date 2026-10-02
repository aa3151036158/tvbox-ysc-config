#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性应用脚本：抓取 live_sources 直播源并注入 output/单仓聚合.json（用完即删）。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("REPO", "Lightconer/tvbox-ysc-config")
import update  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
cfg = json.load(open(os.path.join(ROOT, "config", "sources.json"), encoding="utf-8"))
raw_base = f"https://raw.githubusercontent.com/{os.environ['REPO']}/main/output"

entries = []
for src in cfg.get("live_sources", []):
    sid = src.get("id", "live")
    name = src.get("name", "直播")
    text = None
    for url in src.get("urls", []):
        try:
            text = update.fetch_live_text(url)
            print(f"[OK]   {name} <- {url}")
            break
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {name}  {url}  ->  {e}")
    if text is None:
        raise SystemExit("直播源抓取失败")
    with open(os.path.join(OUT, f"{sid}.txt"), "w", encoding="utf-8") as f:
        f.write(text if text.endswith("\n") else text + "\n")
    entries.append(
        {
            "name": name,
            "type": 0,
            "playerType": 1,
            "url": f"{raw_base}/{sid}.txt",
            "epg": "https://epg.112114.xyz/?ch={name}&date={date}",
            "logo": "https://epg.112114.xyz/logo/{name}.png",
        }
    )

merged_path = os.path.join(OUT, "单仓聚合.json")
d = json.load(open(merged_path, encoding="utf-8"))
old_lives = d.get("lives", [])

# 用与 update.py 完全一致的方式重算 lives（输入 = 当前 output 下各成功源的配置）
fetched = []
for sid in ("feimao", "wangerxiao", "ouge", "4k"):
    p = os.path.join(OUT, f"{sid}.json")
    if os.path.exists(p):
        fetched.append((sid, sid, json.load(open(p, encoding="utf-8"))))
recomputed = update.merge_configs(fetched, entries)["lives"]

if recomputed[: len(old_lives)] != old_lives:
    print("[WARN] 重算的 lives 前缀与现存不一致，改为直接追加")
    d["lives"] = old_lives + [e for e in entries if e not in old_lives]
else:
    d["lives"] = recomputed

with open(merged_path, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("lives 数量:", len(d["lives"]))
print(json.dumps(d["lives"][-1], ensure_ascii=False, indent=2))
