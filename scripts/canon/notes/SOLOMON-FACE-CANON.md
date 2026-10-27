# 솔로몬 정본 얼굴 v2 (2026-10-27)

카드 `cast/solomon.json`의 얼굴 층(task 352, 2026-10-15)과 정본 그림 `frozen/solomon.png`(task 331, 2026-09-04 판 경로)가 어긋남 — 머리(웨이브 장발 ↔ 카드 「short dark hair」) · 옷(크림색 ↔ 짙은 푸른 베옷) · 화풍(만화풍 ↔ 색연필). 사람이 확정한 두 여인 s101(짧은 머리·푸른 겉옷)은 카드 쪽. task 353(사울·다윗·사무엘 v2 정본)과 같은 길로 카드에서 다시 그림.

- 생성: `HF_HUB_OFFLINE=1 $VENV gen_face_canon.py --who solomon --out ~/.local/biblemap-imggen/face-canon` — 8시드 × 정면·3/4 = 16장(레포 밖).
- 기계 판정: `python3 judge_face_canon.py --who solomon` → `~/.local/biblemap-imggen/face-canon/judge-solomon.json` · 상위 3장 중 사울 정본과 가장 구별되는 장 = **s7-front**(distinct 4).

| 후보 | vocab | style | clean | head | 평균 |
|---|---|---|---|---|---|
| s7-front | 8.5 | 9 | 9 | 9 | 8.88 |
| s11-34 | 9 | 9 | 9 | 8 | 8.75 |
| s11-front | 8.5 | 9 | 8.5 | 9 | 8.75 |
| s101-front | 8.5 | 9 | 9 | 8 | 8.62 |
| s303-34 | 9 | 9.5 | 9 | 7 | 8.62 |
| s202-front | 7.5 | 9 | 8.5 | 9 | 8.5 |
| s23-34 | 9 | 9 | 9 | 7 | 8.5 |
| s303-front | 8 | 9 | 9 | 8 | 8.5 |
| s5-front | 8.5 | 9 | 8.5 | 8 | 8.5 |
| s7-34 | 8.5 | 9 | 9 | 7.5 | 8.5 |
| s101-34 | 8.5 | 9.5 | 9 | 6.5 | 8.38 |
| s202-34 | 8.5 | 9 | 9 | 6.5 | 8.25 |
| s23-front | 6.5 | 9 | 8.5 | 9 | 8.25 |
| s42-34 | 8.5 | 9 | 8.5 | 7 | 8.25 |
| s5-34 | 8.5 | 9 | 9 | 6.5 | 8.25 |
| s42-front | 4 | 9 | 8.5 | 9 | 7.62 |

- 눈 확인: 정면 8장이 거의 같은 얼굴(353 「별차이 없어보인다」와 같은 결) · s42만 턱수염 뚜렷(vocab 4) · 여럿이 옅은 수염 그림자 · 20대 초반보다 서른 즈음으로 보임(카드 ageBand 「in his 20s」가 그만큼만 끌어냄).
- 사람 화면: https://claude.ai/artifact/55Z4kFdmhig934fBFjvd7W (폰용 비공개 · 질문 하나 「솔로몬 정본 얼굴로 어느 그림을 쓸까요?」 · 정면 8장(3/4 단추) + 지금 정본 + 참고 두 여인 s101 왕 얼굴).
- 답 반영(353 선례): 새 장을 고르면 `frozen/solomon.png` → `frozen/retired-v1/solomon.png`로 옮기고 고른 정면을 `frozen/solomon.png`로 · `cast/solomon.json`에 `canon_face`(saul 꼴) · 「지금 정본」이면 그대로 두고 카드를 정본에 맞출지 다시 결정 · 「아무거나」면 기계 1위 s7.
