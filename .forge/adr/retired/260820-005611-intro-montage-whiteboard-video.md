---
author: calmonion
decided: 2026-08-20 00:56
---
# 인트로 몽타주는 손저작 SVG에서 구운 화이트보드 필적 MP4로 낸다 — ADR-0024의 "영상 파일 없음"에 좁은 예외

Status: Retired (파일럿 미배송 확정 — 산출물이 git에 들어간 적이 없고, task#279에서 채택하지 않기로 결정)

인트로·투어 애니메이션을 **화이트보드 손그림 필적**(펜촉이 종이 위를 연속으로 미끄러지며 먹을
얹는 연출)으로 개선하자는 요구가 들어왔고, 수단으로 `srt-whiteboard-animation` 스킬을 지정했다.
그 스킬의 산출물은 MP4다. 그런데 이 앱에는 정면으로 부딪히는 결정이 둘 있었다.

- **ADR-0024**(모션 시스템): 무의존 CSS 토큰만, `transform`·`opacity`만 애니메이트, 인트로는
  "실제 영상 파일이 아니라 무의존 CSS/SVG 오토플레이 연출". reduced-motion은 `--dur-*`를 1ms로
  붕괴시켜 **개별 컴포넌트가 reduce 분기를 따로 짜지 않는다**는 것이 계약이다.
- **ADR-0025**(선화 도상): "외부 AI 래스터 이미지·이미지 자산 파일·그래픽 라이브러리는 쓰지
  않는다." 얼굴 초상 금지(예수 등 신학적 민감성), 스타일 편차 금지가 그 알맹이다.

또 하나의 사실이 선택지를 좁혔다: **이 환경에는 이미지 생성 수단이 아예 없다**(이미지 생성
CLI·API 키·MCP 서버 전무). 반면 래스터라이저(`rsvg-convert`·ImageMagick·Playwright)와 스킬의
렌더 환경(`.venv`: cv2·av·numpy)은 전부 갖춰져 있다. 즉 "AI가 그린 그림을 굽는" 경로는
가능하지도 않았다.

## Status

**Rejected (2026-08-20) — 파일럿 반려, 배선 롤백됨.** task#275로 구현해 기계 검증 9종을 전부
통과시켰으나, 실물 판정에서 사용자가 **"그림이 바뀌지도 않고 손모양만 추가된 듯하다"**로 반려했다.
`IntroView.jsx`·`nginx.conf`는 HEAD로 되돌렸고 `frontend/public/whiteboard/`는 제거했다(커밋 전이라
잔재 0). 이 결정의 일부였던 "판정을 통과하지 못하면 확장하지 않고 첫 대안으로 되돌아간다"가 발동한다.

반려 원인 분석은 회고 `260820-055734-intro-montage-whiteboard-video.md`에 있다. 핵심은 **`<video poster>`에
마지막 프레임(=완성된 그림)을 걸어 재생 전에 결말이 먼저 보이는 구조**였다는 것 — 관찰된 증상과 정확히
일치한다. 즉 반려가 "화이트보드 필적이라는 방향" 자체의 기각인지, 이 한 가지 배선 실수의 기각인지는
갈라져 있지 않다. 재시도한다면 그 구분부터 세워야 한다.

저작 소재(`assets/whiteboard/intro-montage/`의 SVG·SRT·주석·README)는 남겨 두었다 — 파생 바이너리는
전부 지웠고 README의 명령 한 줄로 재생성된다.

## Decision

**인트로 ③ 몽타주 비트에 한해 MP4 재생을 허용한다.** 단 그림의 출처는 여전히 **저장소 안의
손저작 stroke-only SVG**이며, MP4는 그 SVG에서 굽는 **파생 자산**이다. 외부 AI 생성 이미지는
쓰지 않는다.

경계를 이렇게 그은 이유: ADR-0025의 알맹이 세 가지(외부 AI 래스터 금지 · 얼굴 초상 금지 ·
스타일 편차 금지)는 **그림 출처를 손저작 SVG로 묶으면 전부 그대로 지켜진다.** 실제로 뒤집히는
것은 ADR-0024의 "인트로는 영상 파일이 아니다" 한 줄뿐이다. ADR-0024의 나머지 계약(토큰 참조
모션·transform/opacity 제약·라이브러리 무의존)은 앱 UI 전체에서 그대로 유효하다 — 이 예외는
모션 시스템의 교체가 아니라 **한 칸의 자산 종류 변경**이다.

따라 붙는 조항 세 개:

1. **reduced-motion은 컴포넌트 분기로 처리한다.** 영상은 `--dur-*` 토큰 붕괴로 즉시 최종
   상태가 되지 않으므로, `prefers-reduced-motion: reduce`에서는 영상을 재생하지 않고 **마지막
   프레임 포스터 PNG를 정적 표시**한다. ADR-0024가 금지한 "개별 컴포넌트의 reduce 분기"의
   명시적 예외이며, 같은 ADR에 이미 `Spinner`가 의도적 예외로 적혀 있어 선례가 있다.
2. **폴백 경로를 지우지 않는다.** 기존 스케치 크로스페이드(`MontageBeat`)는 삭제가 아니라
   강등이며, `onError`에서 그대로 렌더된다. 영상 차단·로드 실패 환경에서 인트로가 빈 화면이
   되지 않게 하는 것이 이 예외를 허용하는 전제 조건이다.
3. **자막은 화면에 태우지 않는다.** 렌더러에 텍스트 그리기 코드가 없다(확인함). SRT는 연출
   타이밍과 서사 순서의 근거로만 쓰이고, 영상에 얹히는 문자는 그림 안의 시대 이름표뿐이다.
   스킬 규범의 "장면 내 문자 절대 금지"는 **AI 생성 이미지의 깨진 글자**를 막는 조항이라,
   손저작 이름표에는 적용하지 않는다(이 프로젝트 한정 완화).

## Considered Options

- **스킬의 화법만 CSS/SVG로 이식**(보이는 펜촉 + `symbol-draw`의 동시 드로우를 한 자루 펜의
  연속 필적으로 직렬화). ADR 위반 0, 번들 증가 0, reduced-motion 계약 무손상. **기술적으로
  가장 깨끗한 안이었고 실제로 먼저 제안했으나, 요구가 "스킬을 사용한 실물 화이트보드 필적"이라
  기각.** 이 안은 영상 파일 없이도 상당 부분을 재현하므로, 파일럿이 반려되면 첫 대안으로 돌아온다.
- **외부 AI 생성 PNG 사용**: ADR-0025 정면 위반이고, 생성 이미지가 얼굴(특히 예수)을 그릴
  리스크가 그 조항의 존재 이유와 직접 충돌한다. 게다가 이 환경에 생성 수단이 없다. 기각.
- **테마 투어 165 정차지 전량 영상화**: 용량·저작량·검증 모두 성립하지 않는다. 기각(후속에서
  투어 개요 단위 9편은 재검토 가능).
- **인트로 6비트 전체를 한 편의 MP4로 교체**: 비트 타이머·순차 디졸브 로직을 걷어내는 큰
  수술이고, 메뉴 소개 장면 3개를 새로 저작해야 한다. 화이트보드 필적을 아무도 실물로 본 적이
  없는 상태에서 이 크기로 착수하는 것은 회고 `260724-004042`가 기록한 "전면 재구현 6번"을 그대로
  다시 부른다. 기각 — 몽타주 한 칸 파일럿으로 축소.

## Consequences

- **정적 자산 예산이라는 개념이 새로 생긴다.** `frontend/public`은 현재 전체 72K다. MP4 한 편이
  즉시 지배적 비중이 되므로 예산을 명시한다: 목표 ≤1.5MB, 상한 3MB. 초과 상태로 완료 선언하지
  않는다.
- **nginx 캐시 규칙에 `mp4`가 필요하다.** 현재 정규식은 `js|css|png|jpg|jpeg|gif|ico|svg|woff2?`뿐이라
  MP4가 `location /`의 `try_files`로 떨어져 `Cache-Control` 없이 서빙된다 → 방문마다 재다운로드.
- **저작 소재를 커밋한다.** `assets/whiteboard/<프로젝트>/`에 `.svg` 원본 · `.png` · `.srt` ·
  `annotation.json` · 마스터 MP4를 함께 둔다. 굽기 명령 한 줄로 재현되지 않으면 6개월 뒤 수정이
  불가능해진다.
- **되돌리기가 비싼 쪽은 코드가 아니라 선례다.** 폴백이 남아 있으므로 코드 되돌리기는 `<video>`
  제거 한 곳이다. 비싼 것은 "영상 자산을 앱에 넣어도 된다"는 선례이며, 실제로 다음 단계(인트로
  전량 · 투어)가 이 선례에 올라탈 예정이다. 그래서 **파일럿 판정을 통과하지 못하면 확장하지
  않고 위 첫 대안(화법 이식)으로 되돌아간다**는 것을 이 결정의 일부로 둔다.
- 스킬 `.venv`에서 cv2와 av가 `libavdevice`를 중복 적재한다는 objc 경고가 뜬다("mysterious
  crashes" 가능). 렌더가 죽으면 첫 용의자다.

## 부록 — 당시 렌더 절차 (task#279에서 흡수)

task#279에서 이 파일럿을 철회하면서 `assets/whiteboard/intro-montage/`를 삭제했다. 따라서 위
「Status」의 "저작 소재는 남겨 두었다"와 "README의 명령 한 줄로 재생성된다"는 **더 이상 유효하지
않다** — 소재(`intro-montage.svg`·`.srt`·`.annotation.json`)도 함께 사라졌으므로 아래 절차만으로는
재생성되지 않고, 그림을 다시 저작해야 한다. 사라지는 유일한 기록이므로 그 README의 본문을
**원문 그대로** 아래에 옮겨 둔다.

### 파일

| 파일 | 역할 |
|---|---|
| `intro-montage.svg` | **정본.** 1600×900, 6구역(시대 3 × 장면+이름표). 여기만 고치면 된다 |
| `intro-montage.png` | 위 SVG의 래스터(렌더러 입력) |
| `intro-montage.srt` | 연출 타이밍·서사 순서의 근거. 영상에 태워지지 않는다 |
| `intro-montage.annotation.json` | 구역·순서·타이밍. `startMs`/`durationMs`는 `reveal` 하위 |

아래는 재생성 산출물이라 저장소에 두지 않는다: `intro-montage.png`(래스터) ·
`drawing-hand-plain.png`(무문자 손 소재) · `intro-montage-whiteboard.mp4` · `intro-montage-poster.png`.

### 재현 (그림을 고친 뒤 이 순서대로)

```bash
D=assets/whiteboard/intro-montage
ENV_PY=~/.claude/skills/srt-whiteboard-animation/.venv/bin/python

# 0) 무문자 손 소재 — 스킬 기본 소재의 펜대에 중국어 문구가 찍혀 있어 내부를 흰색으로 채운다
#    (검은 외곽선은 남기려고 침식 후 채움). 스킬 자체는 수정하지 않는다.
$ENV_PY - <<'EOF'
import cv2, numpy as np
src = "/Users/calmonion/.claude/skills/srt-whiteboard-animation/assets/drawing-hand.png"
img = cv2.imread(src, cv2.IMREAD_UNCHANGED); h, w = img.shape[:2]
near_white = ((img[:,:,:3] > 195).all(axis=2) & (img[:,:,3] > 128)).astype(np.uint8) * 255
n, lab, stats, _ = cv2.connectedComponentsWithStats(near_white, 8)
barrel = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
bm = (lab == barrel).astype(np.uint8) * 255
ff = (255 - bm).copy(); cv2.floodFill(ff, np.zeros((h+2, w+2), np.uint8), (0, 0), 0)
filled = ((ff > 0) | (bm > 0)).astype(np.uint8) * 255
img[cv2.erode(filled, np.ones((5,5), np.uint8)) > 0] = (255, 255, 255, 255)
cv2.imwrite("assets/whiteboard/intro-montage/drawing-hand-plain.png", img)
EOF

# 1) SVG → PNG (반드시 1600×900)
rsvg-convert -w 1600 -h 900 $D/intro-montage.svg -o $D/intro-montage.png

# 2) PNG + 주석 → MP4 (선화가 또렷하므로 skeleton 필적)
$ENV_PY ~/.claude/skills/srt-whiteboard-animation/scripts/render_stream_whiteboard.py \
  $D/intro-montage.png $D/intro-montage.annotation.json $D/intro-montage-whiteboard.mp4 \
  $D/drawing-hand-plain.png \
  --total-ms 10400 --ink-path skeleton --color-fill contour-wipe --cap-long-edge 1280

# 3) 포스터 = 마지막 프레임
ffmpeg -v error -sseof -0.15 -i $D/intro-montage-whiteboard.mp4 -frames:v 1 -y $D/intro-montage-poster.png

# 4) 배포 위치로 복사 → 빌드 (재배선하는 경우에만)
mkdir -p frontend/public/whiteboard
cp $D/intro-montage-whiteboard.mp4 frontend/public/whiteboard/intro-montage.mp4
cp $D/intro-montage-poster.png      frontend/public/whiteboard/intro-montage.png
(cd frontend && npm run build)
```

**재배선한다면 포스터를 마지막 프레임으로 쓰지 마라.** 그러면 영상이 시작되기 전에 완성된
그림이 먼저 보이고, 이어서 빈 캔버스부터 그려져 결말→시작 순으로 뒤집힌다. 첫 프레임(빈 종이)을
포스터로 쓰고, reduce용 정적 이미지만 마지막 프레임으로 따로 두는 것이 맞다.

### 손대면 같이 고쳐야 하는 것

- **길이를 바꾸면** `frontend/src/IntroView.jsx`의 `MONTAGE_MS`를 맞춰라. **영상 길이가 정본이고
  `BEAT_MS[2]`가 파생**이다 — 어긋나면 영상 중간에 다음 비트로 넘어가거나 끝난 뒤 정지 화면이 남는다.
- **모든 먹선은 6구역 사각형 안에 있어야 한다.** 구역 밖 픽셀은 마스크 렌더러가 영영 그리지 않아
  최종 프레임이 원본과 어긋난다. 구역끼리 겹쳐도 안 된다(겹치면 뒤 구역이 앞 구역을 깎는다).
- 검증 스크립트(`.forge/loop-checks.sh` 등 9종)는 롤백과 함께 제거했다. 재시도하면 회고
  `260820-055734`의 「배움」이 그 체크들이 어떻게 틀렸었는지를 기록하고 있으니 먼저 읽어라.
