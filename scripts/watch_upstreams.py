#!/usr/bin/env python3
"""Watch the upstream free-subscription repos listed in README.md.

For each upstream repo, fetch its star count and latest commit date from the
GitHub API and rewrite the marked table region in README.md. A repo with no
commit for over 30 days is flagged as stopped. Run daily by GitHub Actions.
Stdlib only.
"""
import datetime
import json
import os
import re
import sys
import urllib.request

UPSTREAMS = [
    "Pawdroid/Free-servers",
    "ermaozi/get_subscribe",
    "awesome-vpn/awesome-vpn",
    "free18/v2ray",
    "VPN-Subcription-Links/ClashX-V2Ray-TopFreeProxy",
    "ripaojiedian/freenode",
    "snakem982/proxypool",
    "abshare/abshare.github.io",
    "zhuhaiuk/free-nodes",
]

CADENCE = {
    "Pawdroid/Free-servers": "约 6 小时",
    "ermaozi/get_subscribe": "持续更新",
    "awesome-vpn/awesome-vpn": "每日",
    "free18/v2ray": "每日",
    "VPN-Subcription-Links/ClashX-V2Ray-TopFreeProxy": "频繁",
    "ripaojiedian/freenode": "频繁",
    "snakem982/proxypool": "每日",
    "abshare/abshare.github.io": "自动更新",
    "zhuhaiuk/free-nodes": "每小时",
}

DESC = {
    "Pawdroid/Free-servers": "免费订阅地址与节点合集，Clash / SS / V2Ray / Trojan",
    "ermaozi/get_subscribe": "自动获取免费机场订阅链接：Clash / V2Ray / Trojan / SSR / SS",
    "awesome-vpn/awesome-vpn": "免费代理节点聚合：vmess / vless / trojan / ss",
    "free18/v2ray": "每日分享免费节点、免费机场，含 Quantumult X 订阅",
    "VPN-Subcription-Links/ClashX-V2Ray-TopFreeProxy": "Clash 与 V2Ray 免费订阅链接精选",
    "ripaojiedian/freenode": "免费订阅 / 节点合集：ss / ssr / vmess / vless / trojan",
    "snakem982/proxypool": "免费节点池，Clash / V2Ray 订阅",
    "abshare/abshare.github.io": "Allblue 免费节点，流量用完自动换新订阅，支持 Clash / v2rayN / 小火箭",
    "zhuhaiuk/free-nodes": "自动更新的免费节点订阅，支持 Clash / Mihomo / V2Ray / Trojan / Shadowrocket",
}

TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get_json(url):
    headers = {"User-Agent": "airport-watch", "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    today = datetime.datetime.now(datetime.timezone.utc).date()
    rows = []
    for full in UPSTREAMS:
        try:
            info = get_json("https://api.github.com/repos/" + full)
            commits = get_json("https://api.github.com/repos/" + full + "/commits?per_page=1")
            last = commits[0]["commit"]["committer"]["date"][:10]
            last_date = datetime.date.fromisoformat(last)
            stars = info["stargazers_count"]
        except Exception as exc:
            print("WARN: %s failed: %s" % (full, exc), file=sys.stderr)
            rows.append(
                "| [%s](https://github.com/%s) | ? | %s | %s | 未知 | 查询失败 |"
                % (full, full, CADENCE[full], DESC[full])
            )
            continue
        stale = (today - last_date).days > 30
        status = "已停更" if stale else "更新中"
        rows.append(
            "| [%s](https://github.com/%s) | ★%d | %s | %s | %s | %s |"
            % (full, full, stars, CADENCE[full], DESC[full], last, status)
        )
    table = "\n".join(rows)

    with open("README.md", encoding="utf-8") as fh:
        readme = fh.read()
    pattern = re.compile(
        r"<!-- UPSTREAM-TABLE:START -->.*?<!-- UPSTREAM-TABLE:END -->", re.S
    )
    replacement = "<!-- UPSTREAM-TABLE:START -->\n" + table + "\n<!-- UPSTREAM-TABLE:END -->"
    new, n = pattern.subn(replacement, readme)
    if n == 0:
        print("ERROR: markers not found in README.md", file=sys.stderr)
        return 1
    new = re.sub(
        r"星数与更新状态核实于 \d{4}-\d{2}-\d{2}（由自动化每日更新）。",
        "星数与更新状态核实于 %s（由自动化每日更新）。" % today.isoformat(),
        new,
    )
    if new != readme:
        with open("README.md", "w", encoding="utf-8") as fh:
            fh.write(new)
        print("README updated")
    else:
        print("no change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
