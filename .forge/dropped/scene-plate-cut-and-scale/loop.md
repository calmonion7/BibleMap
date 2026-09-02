# LOOP — 삼상17 장면의 육안 결함 셋(창·지물·시선)을 닫고 v33/v35 갈래를 한 판으로 합친다
started: 2026-09-01
replan-round: 1
replan-cap: 3
budget-tokens: none
budget-spent: 0 · since: 2026-09-01T00:00:00Z
closed: 2026-09-02 — 사람 결정으로 종료(갈래 C: C2를 성과로 확정, C1·C8은 별건, task 326 보관).
      실측·진단은 `scripts/canon/notes/SCENE-1SAM17.md` §17~§18로 승격했다.
wall: fork (C1을 닫는 두 갈래가 모두 승인 밖이다 — ⓐ 그림을 고치는 길은 접지 기하 훑기라 「접지 훑기 ≤N회」라는 새 GPU 예산 항목이 필요하고(후보당 창 인페인트 1회 — 판 캐시는 이미 있다), ⓑ 자를 고치는 길은 C9가 기계로 막는다. 시간 상한 80분도 초과했다(약 115분). 아울러 **C8은 프롬프트 축이라 이 스코프에서 원리상 닫을 수 없다** — 현 계약으로는 goal-met에 도달할 수 없다)

⚠ **2026-09-02 라벨 재조준** — C1·C2·C7·C8이 `v37`을 못박고 있었으나 v37은 다시 렌더되지 않는다
(task 325는 보관됐고, 후속 task 326이 내는 라벨은 `v38`이다). **임계·산식·판정 대상은 한 글자도
바꾸지 않고 「어느 렌더를 재는가」만 v37 → v38로 옮긴다.** 그대로 두면 검사가 영구히 불가능해져
루프가 사무적 사유로 no-progress 벽에 걸린다. 아울러 C1을 우회하는 두 길(자를 고치기 · 상자를
옮기기)을 task 326의 DoD 4·5에서 끌어와 **C9·C10으로 승격**한다 — 검사 집합은 **더 엄해질 뿐**
느슨해지지 않는다.

## Stop-condition checks (ALL must pass)
- [ ] C1. 회귀 가드 겸 전진 검사 — `judge_scene.py v38` 종료코드 0 (다섯 축 C1~C5 유지)
      cmd: `~/.local/biblemap-imggen/.venv314/bin/python3 scripts/canon/judge_scene.py v38; echo $?`
      ⚠ v37에서 C3 이음매만 false였다(0.511 > 0.4). 나머지 넷은 이미 true다.
- [x] C2. 다윗 기여 잉크 — v38의 (S5 − S4) ink_david ≥ 0.0868
      cmd: task 326 계획 본문의 python 3줄. 사전 실측 v37 = 0.0430, v35 = 0.0307, v33 = 0.0868
- [x] C3. §16 존재 — `grep -c '^## 16\.' $D` = 1
- [x] C4. §16 실질 — 본문 ≥ 20줄 · `0.0545` 포함(C4 산식 결함 기록) · `시선` 포함(DoD 5 실측 기록)
      cmd: `awk '/^## 16\./{f=1;next} /^## /{f=0} f' $D` 로 본문 뽑아 3조건 판정
- [x] C5. 끊긴 포인터 제거 — `grep -c 'reference/scripture-v17' $D` = 0
- [x] C6. §15 오번호 정정 — `sed -n '/^## 15\./p' $D | grep -c 'task 325'` = 0
- [ ] C7. 골리앗의 창이 **한 자루**로 읽힌다 (v38-final-s11.png)
      evidence: external
- [ ] C8. 다윗이 **막대기와 물매를 둘 다** 든다 (v38-final-s11.png)
      evidence: external
- [x] C9. **판정자 무변경** — `git diff --numstat scripts/canon/judge_scene.py | wc -l` = 0
      *C1을 「자를 고쳐」 통과하는 길을 기계로 막는다(task 326 DoD 4에서 승격).*
- [x] C10. **`REGIONS` 무변경** — 아래 두 grep이 각 1
      `grep -c '"goliath":      (0.625, 0.05, 0.855, 0.95)' scripts/canon/gen_scripture_scene.py`
      `grep -c '"david":        (0.15, 0.52, 0.305, 0.92)' scripts/canon/gen_scripture_scene.py`
      *C1을 「상자를 옮겨 자를 눈멀게 해」 통과하는 길을 기계로 막는다(task 326 DoD 5에서 승격 —
      하단 0.95→1.00은 새 하단선 639가 `_edge_seam` 가드 `line < 636`에 걸려 하단 변이 판정에서
      통째로 빠진다. ADR `260830-125824`가 금지하는 파생원 교체다).*

$D = scripts/canon/notes/SCENE-1SAM17.md

## Check progress (updated after EVERY stop-condition run)
- C1: **fail** ×1 · regressed: ×0 · last-evidence: "v38 judge 종료코드 **1** — C3 이음매 **0.6579**
      @ `S3/goliath.left`(v37 0.5111 @ bottom). C1·C2·C4·C5는 참. S4/shieldman이 0.0000 → 0.4138로
      새로 걸렸다. **다만 육안으로는 v37·v38 어느 쪽에도 사각 잔상이 없다** — 판정 표본이 n=38
      (구역 높이 576 중)이라 픽셀 몇 개가 값을 정한다."
      reflection: "**진단이 뒤집혔다(2026-09-02, task 326 실측).** 이음매를 만드는 것은 붙임이
      아니라 **접지 `_contact()`**다: `place`만이면 하단 변에 배경으로 닿은 열이 15개뿐이라 판정
      대상조차 아니고(가드 n<20), 접지가 그것을 135열로 만든다. 접지 띠 위에서 오프라인 재현과
      실제의 차이가 0.0001이므로 이 분리는 확정이다. 따라서 **다음 시도는 `_plate`/`_place` 기하가
      아니라 `_contact`의 기하여야 하고, 그것은 후보마다 GPU가 든다** = 이 스코프의 예산 밖.
      더 깊은 물음: `paste_seam`이 n≈38에서 육안 결함 없이 0.66을 낸다 — 자의 작동점 자체가
      의심스러운데 자를 고치는 것은 C9가 기계로 막는다(사람 결정)."
      tried: 부정어 변형 D(테두리족 필수부 승격) · scene-plate-cut-and-scale(본체 기준 배율·중심)
      ⊕ **2026-09-02 재개 실측(코드 판독, GPU 0).** fork를 두 가지로 더 좁혔다.
      ① **접지만 재실행하는 길이 지금은 없다.** `_plate`→`_place`→`_contact`가 단계 루프 한 회차
         안에 붙어 있고(`gen_scripture_scene.py:551-555`), 캔버스는 시드마다 새로 쌓아 디스크에서
         이어받지 못한다. `--stages`로 골라도 `_plate`가 같이 돈다.
         ⚠ **정정(같은 세션, 코드 재판독):** 판 캐시는 **이미 있다** — `_plate()`가 크롭 전 원본을
         `plate-*.png`로 저장하고 알파는 `PAPER`/`PLATE_CUT`에서 재파생된다(`:421-424`, 주석이
         「GPU 없이 반복할 수 있다」고 명시). 따라서 후보당 비용은 「판 렌더 1 + 인페인트 1」이
         아니라 **창 인페인트 1회**다. 필요한 것은 캐시가 아니라 **저장된 판에서 `_place`→
         `_contact`만 재실행하는 소품**이다. 그래도 GPU 0은 아니므로 「접지 훑기 ≤N회」라는
         **새 예산 항목**을 사람이 열어야 한다.
      ② **자의 교정 분리가 무너졌다.** `judge_scene.py`의 이음매 임계 0.40은 커밋 e1ea578에서
         열 판 교정으로 잡혔다 — 상자 인페인팅 .774~.950 대 판 합성 .250. 그런데 지금 판 합성이
         **육안 결함 없이 .658**을 낸다. 즉 그 분리가 사라졌고, 표본이 n=38(구역 높이 576의 6.6%)
         뿐인데 「한 변의 대부분에서 끊긴다」는 기전 논거로 0.40을 적용하고 있다. 그림이 아니라
         **자의 작동점 문제**로 읽힌다. 고치려면 C9를 사람이 풀어야 한다.
- C2: **pass** · last-evidence: "v38 다윗 기여 잉크 **0.1150** (목표 ≥0.0868, 132%).
      S4=0.0545 S5=0.1694. v35 .0307 → v36 .0320 → v37 .0430 → **v38 .1150**.
      기전: 얇은 물매 끈이 판 bbox를 늘려 소년을 축소시키고(배율) 판 중심을 끌어당겨 몸을 상자
      밖으로 밀어냈다(중심). `_place()`의 기준을 판 전체 bbox에서 **본체**(`BODY_COV=0.20`)로
      옮겨 둘 다 닫았다. 붙일 범위는 알파 전체 그대로라 물매는 그림에 남는다."
- C3: **pass** · last-evidence: "grep -c '^## 16\.' → 1"
- C4: **pass** · last-evidence: "§16 본문 68줄(≥20) · `0.0545` 2회 · `시선` 2회"
- C5: **pass** · last-evidence: "grep -c 'reference/scripture-v17' → 0 (§0 최선본 줄을 v37로 갱신하고 재현 명령이 곧 산출물임을 명시)"
- C6: **pass** · last-evidence: "sed -n '/^## 15\./p' | grep -c 'task 325' → 0"
- C7: waiting ×1 · last-evidence: "**v38**-final-s11.png 드라이브 관찰 — 창이 **한 자루로 유지된다**
      (잎사귀 날 + 곧은 자루). task 326은 프롬프트를 한 글자도 안 건드렸고 회귀 가드로서 유지됐다.
      사람 판정 대기."
- C8: waiting ×1 · last-evidence: "**v38**-final-s11.png 드라이브 관찰 — **물매 끈은 남아 있으나
      막대기는 없다.** ⚠ task 326이 프롬프트 축을 명시적으로 제외했으므로 이 검사는 이번 판에서
      움직일 수 없었다. 이 루프의 마지막 미결이며 별건 프롬프트 작업이 필요하다. 사람 판정 대기."
- C9: **pass** · last-evidence: "git diff --numstat scripts/canon/judge_scene.py | wc -l → 0 (v38 시점 재확인)"
- C10: **pass** · last-evidence: "두 grep 각 1 (v38 시점 재확인) — REGIONS 원값 유지"

## Authorized replan scope
- 실패한 정지조건 검사에 **직접 추적되는** 픽스포워드만. 현재 멤버 계획
  `scene-plate-cut-and-scale`(task 326)의 「하지 않을 것」이 그대로 하드 제외선이다:
  - **프롬프트 변경** — 절제가 아니라 예산의 기둥이다. 문구를 건드리는 순간 저장한 판이 무효가 되고
    훑기가 GPU 0을 잃어 task 325의 예산(판 14·185분)으로 돌아간다.
  - `judge_scene.py` 수정 (임계·산식·새 축 무엇도) — C9가 기계로 막는다
  - `REGIONS` 이동, 특히 골리앗 하단 0.95→1.00 — C10이 기계로 막는다
  - 시드 채택·전체 시드 교체·단계별 시드 도입 (`params.py`의 「축을 섞지 않는다」)
  - 별도 지물 단계(S9) 부활 — v10~v13 네 판 연속 실패로 닫힌 길
  - 판 합성 구조(규칙 열째) 되돌리기
  - 다른 장면·다른 본문으로의 일반화
- **판 예산: 판 렌더 ≤4판 · 전 8단계 ≤2판 · 합성 훑기 무제한(GPU 0) · 시간 ≤80분이 하드 상한.**
  넘겨야만 가능하면 생성하지 말고 **fork 벽**으로 넘긴다. 넘길 때는 **C1(이음매)을 먼저 닫고**
  C2는 실측을 남긴 채 별건으로 — C1이 열린 회귀 가드라 우선순위가 다르다.
- C7·C8은 `evidence: external`이므로 **픽스포워드 대상이 아니다** — 판정자가 사람이다.
- always-halt action classes: prod data mutation/deletion · deploy/release/publish ·
  outbound external comms · irreversible VCS/file destruction (force-push · history rewrite ·
  mass deletion) · financial/payment · secret/permission change · privacy-data exposure

## Tasks
- ~~scene-eye-defects~~ (task 325 — 2026-09-02 `verified: failed`로 `.forge/dropped/`에 보관.
  창 결함①은 닫았고 문서 검사 넷은 통과했으나 DoD가 `v37`을 못박아 자력 봉인이 불가능했다.
  실측은 §16과 보관된 run.md에 남아 있다.)
- scene-plate-cut-and-scale (task 326 — 실행 완료 2026-09-02, `verified: failed`. **C2를 닫았고**
  C1은 못 닫았다 — 진단이 뒤집혀 원인이 `_contact`로 밝혀졌다. 활성 슬롯에 있다)
