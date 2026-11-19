#!/bin/zsh
# task 690~693 — LoRA v2 학습이 끝나면 기혼 690(세기 1.0)·691(0.8)·692(1.2)·베들레헴 693 생성 → 판정 → 보고. 이미 된 그림·판정은 건너뜀.
cd /Users/calmonion/Project/BibleMap/scripts/canon
VENV=~/.local/biblemap-imggen/.venv314/bin/python
while pgrep -f "[m]flux-train" >/dev/null; do sleep 30; done
[ -f ~/.local/biblemap-imggen/lora/oil-horn-v2.safetensors ] || { echo "[Queue690] LoRA v2 없음 — 학습 실패"; exit 1; }
for n in 690 691 692 693; do $VENV /Users/calmonion/Project/BibleMap/scripts/canon/batch/rule_ab.py --fixed $n gen 2>&1 | grep -E "RuleAB|require|실패|막|Errno|Error" ; done
for n in 690 693 691 692; do python3 /Users/calmonion/Project/BibleMap/scripts/canon/batch/rule_ab.py --fixed $n judge 2>&1 | tail -2; python3 /Users/calmonion/Project/BibleMap/scripts/canon/batch/rule_ab.py --fixed $n report 2>&1 | tail -12; done
echo "[Queue690] 끝"
