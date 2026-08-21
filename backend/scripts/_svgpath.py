"""SVG path d 속성 → 절대 좌표 점 목록. 상대 명령(h·v·q·l 소문자)을 절대로 환산한다.
바운딩 박스로 겹침을 재면 가로로 긴 능선 하나가 그 띠 전체를 덮은 것으로 잡혀 과대평가된다.
베지어는 끝점 + 제어점을 낸다 — 곡선은 제어점의 볼록껍질 안에 있으므로 근접 판정에 충분하다."""
import re

_TOK = re.compile(r'([MmLlHhVvCcSsQqTtAaZz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)')


def points(d):
    toks, i = [], 0
    for m in _TOK.finditer(d):
        toks.append(m.group(1) or float(m.group(2)))
    out, cx, cy, sx, sy, cmd = [], 0.0, 0.0, 0.0, 0.0, None
    i = 0
    while i < len(toks):
        t = toks[i]
        if isinstance(t, str):
            cmd = t
            i += 1
            if cmd in 'Zz':
                cx, cy = sx, sy
                out.append((cx, cy))
                continue
        if cmd is None:
            i += 1
            continue
        rel = cmd.islower()
        c = cmd.upper()
        need = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6, 'S': 4, 'Q': 4, 'T': 2, 'A': 7}[c]
        args = toks[i:i + need]
        if len(args) < need or any(isinstance(a, str) for a in args):
            break
        i += need
        if c == 'M':
            cx, cy = (cx + args[0], cy + args[1]) if rel else (args[0], args[1])
            sx, sy = cx, cy
            out.append((cx, cy))
            cmd = 'l' if rel else 'L'          # 이후 좌표쌍은 L로 이어진다
        elif c == 'L':
            cx, cy = (cx + args[0], cy + args[1]) if rel else (args[0], args[1])
            out.append((cx, cy))
        elif c == 'H':
            cx = cx + args[0] if rel else args[0]
            out.append((cx, cy))
        elif c == 'V':
            cy = cy + args[0] if rel else args[0]
            out.append((cx, cy))
        elif c in 'CQ':
            pts = []
            for k in range(0, need, 2):
                px = cx + args[k] if rel else args[k]
                py = cy + args[k + 1] if rel else args[k + 1]
                pts.append((px, py))
            out += pts
            cx, cy = pts[-1]
        elif c in 'ST':
            pts = []
            for k in range(0, need, 2):
                px = cx + args[k] if rel else args[k]
                py = cy + args[k + 1] if rel else args[k + 1]
                pts.append((px, py))
            out += pts
            cx, cy = pts[-1]
        elif c == 'A':
            px = cx + args[5] if rel else args[5]
            py = cy + args[6] if rel else args[6]
            # 호는 시작·끝 사이를 몇 점으로 근사(반지름 방향 여유는 판정 여백이 흡수한다)
            for f in (0.25, 0.5, 0.75):
                out.append((cx + (px - cx) * f, cy + (py - cy) * f))
            out.append((px, py))
            cx, cy = px, py
    return out
