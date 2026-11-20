#!/bin/zsh
# task 694~ — 베들레헴 고정 절 N(기본 694) 생성 → 판정 → 보고(이미 된 것은 건너뜀) · 쓰기: queue_694.sh 695
cd /Users/calmonion/Project/BibleMap/scripts/canon
~/.local/biblemap-imggen/.venv314/bin/python /Users/calmonion/Project/BibleMap/scripts/canon/batch/rule_ab.py --fixed ${1:-694} gen 2>&1 | grep -E "RuleAB|require|실패|막|Errno|Error"
python3 /Users/calmonion/Project/BibleMap/scripts/canon/batch/rule_ab.py --fixed ${1:-694} judge 2>&1 | tail -2
python3 /Users/calmonion/Project/BibleMap/scripts/canon/batch/rule_ab.py --fixed ${1:-694} report 2>&1 | tail -14
echo "[Queue${1:-694}] 끝"
