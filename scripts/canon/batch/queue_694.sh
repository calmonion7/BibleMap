#!/bin/zsh
# task 694 — 베들레헴 새 배치(693)를 LoRA 없이 생성 → 판정 → 보고(이미 된 것은 건너뜀)
cd /Users/calmonion/Project/BibleMap/scripts/canon
~/.local/biblemap-imggen/.venv314/bin/python /Users/calmonion/Project/BibleMap/scripts/canon/batch/rule_ab.py --fixed 694 gen 2>&1 | grep -E "RuleAB|require|실패|막|Errno|Error"
python3 /Users/calmonion/Project/BibleMap/scripts/canon/batch/rule_ab.py --fixed 694 judge 2>&1 | tail -2
python3 /Users/calmonion/Project/BibleMap/scripts/canon/batch/rule_ab.py --fixed 694 report 2>&1 | tail -14
echo "[Queue694] 끝"
