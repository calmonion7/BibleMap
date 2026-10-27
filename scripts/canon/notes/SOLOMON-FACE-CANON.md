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
- 사람 답(2026-10-27): **s7** 고름(메모 없음) → `frozen/solomon.png` 교체 · 옛 판 `frozen/retired-v1/solomon.png` · 카드 `canon_face` 추가.

## 규칙으로 넓힘 — spec.cast-canon-face (2026-10-27 사용자 「규칙으로」)

- 원장 규칙 `spec.cast-canon-face`(recheck.cast_canon_face_errors): 명세 인물마다 카드 `canon_face` · 정본 파일 · `prompt_sha` = 지금 카드의 정면 정본 문구 지문(`gen_face_canon.prompt_sha`). 처음 재검: 명세 3/38 · 걸린 인물 29.
- 다윗·사무엘: 지금 카드 문구로 같은 시드 11 정면을 다시 그리니 frozen과 화소까지 같음 → 지문만 채움(사람 확인 없음). 사울은 다름(평균 화소차 22 — 353 뒤 카드가 바뀜) → 다시 그림.
- 27명(사울 + 카드 파생 정본 없던 26명): `gen_face_canon.py --seeds 11 42 7 23`(353·솔로몬 모두 후보끼리 차이가 거의 없어 8 → 4시드) → `~/.local/biblemap-imggen/face-canon-v3/` · `judge_face_canon.py --dir … --who <id>`. david-boy·doeg는 인코더 SIGSEGV로 한 번 실패 → 다시 돌려 됨.
- 눈 확인(기계 추천 25장 몽타주): 대머리·붕괴 없음. 아히멜렉·칼 든 신하는 추천이 3/4 그림 → 화면에서 같은 시드 정면을 추천으로.
- 사람 화면: https://claude.ai/artifact/1SKN9yTGFUpb8z4Jz3P9qB (`batch/make_canon_face_page.py` · 27명 × 후보 4 + 지금 정본 · 「전부 기계 추천으로」 단추 · 8.8MB) → 답 반영 `python3 batch/apply_canon_faces.py '<판정 task canon-faces + JSON>'` → `recheck.py specs`·`images`.
