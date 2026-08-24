---
author: calmonion
decided: 2026-08-25 06:50
---
# 저작 파이프라인은 앱과 **다른 런타임**을 갖는다 — 레포 안에 두되 앱 의존성과 섞지 않고, 재현은 **미결로 표시**한다

[[인물 정본]]을 뽑는 이미지 생성 파이프라인(스크립트 13종)이 지금까지 두 군데에 흩어져 있었다 —
`.forge/reports/canon-pilot/`(gitignore로 통째 제외)과 `~/.local/biblemap-imggen/`(레포 밖). 두
태스크분(#314·#315)의 확정된 [[생성 파라미터]]가 전부 그 안에만 있고, `make_masks.py`는 이미
`sys.path.insert` 로 추적 디렉터리의 `scripts/check_mask_ranges.py`를 import하고 있었다. 경계가
사실상 임의였다.

## 결정

**저작 파이프라인은 `scripts/canon/`에 둔다** — 추적되지만 `backend/`와 분리한다.

세 후보가 있었다.

| 후보 | 이득 | 왜 안 골랐나 |
|---|---|---|
| `backend/scripts/` | 명명 규약(`<verb>_<target>.py`)·`python3 -m` 실행 관례·검증기 선례를 그대로 상속 | **런타임이 다르다** — torch·diffusers·Python 3.14.5 ↔ `backend/requirements.txt` 3줄·Python 3.12. `Dockerfile`이 `COPY app/`만 하므로 이미지와도 무관하다. 같은 폴더에 두면 "backend 것"으로 오독되고 두 의존 집합이 섞인다 |
| 별도 레포 | 환경이 완전히 다르니 물리적으로 갈라진다 | 이미 존재하는 `check_mask_ranges.py` import 간선이 레포를 가로질러 끊어진다. 이 태스크가 막으려는 드리프트를 오히려 늘린다 |
| **`scripts/canon/`** ✔ | 최상위 `scripts/`는 이미 "호스트에서 도는 것"(`check.sh`·`uat_*.py`) 자리이고 그 import 간선의 **한쪽 끝이 이미 거기 있다** | — |

## 재현은 미결로 표시한다 — 「고정했다」가 아니라 「고정하지 않았다」를 적는다

`scripts/canon/requirements.txt`에 `pip freeze`를 박제하되, **이것이 재현을 보장한다고 적지
않는다.** 보장되지 않는 축이 셋 남는다.

1. **모델 가중치** — `xinsir/controlnet-scribble-sdxl-1.0` · `stabilityai/stable-diffusion-xl-base-1.0`
   은 HF 캐시에서 온다. 리비전을 고정하지 않았다.
2. **MPS 결정성** — Apple Silicon 백엔드가 torch 버전 간 비트 동일을 보장하지 않는다.
3. **실측 부재** — 재현이 되는지 **실제로 시험하지 않았다**.

⇒ 이 미결이 **`frozen/*.png`의 분류를 바꾼다.** 환경이 재현되면 동결 얼굴은 시드에서 다시 뽑을 수
있는 캐시지만, 재현이 미결이면 그 PNG가 정체성의 **유일한 운반체**다. 그래서 동결본은 산출물이
아니라 **다음 단계의 입력**으로 분류해 추적한다(파일럿 2장 3MB). 74명 확대 시의 정책(약 110MB)은
이 ADR이 정하지 않는다 — 재현을 실제로 닫는 태스크가 정할 몫이다.

**미결을 미결로 적는 것이 결정의 일부다**(ADR `260822-220823`) — `requirements.txt`가 침묵하면
그 침묵이 "고정됨"으로 읽힌다.

## Consequences

- **레포에 파이썬 런타임이 둘이 된다.** `scripts/canon/requirements.txt`(무거움, 호스트 전용)와
  `backend/requirements.txt`(3줄, 이미지에 들어감). 섞지 않는 것이 이 ADR의 요점이므로, 어느 한쪽에
  의존을 추가할 때 다른 쪽을 보지 않는다.
- **`scripts/`가 배포 게이트의 감시 대상이 된다.** 이 이동과 함께 `scripts/` 아래 미추적 0건이
  게이트에 걸린다 — `check.sh`가 미추적 파일 두 개(`check_cast_axes.py`·`check_mask_ranges.py`)를
  호출하고 있던 실제 결함이 이것으로 닫힌다.
- **`.forge/reports/canon-pilot/`은 산출물 저장소로 남는다.** 스크립트만 옮기고 54MB의 생성물은
  그 자리에 둔다. 산출물 루트는 [[생성 파라미터]]의 값이 되어 게이트가 함께 지킨다.
- **역방향은 싸다.** 나중에 별도 레포로 갈라내고 싶어지면 `scripts/canon/`을 통째로 옮기면 되고,
  그때 끊어야 할 간선이 무엇인지는 `params.py` 하나가 말해 준다.
