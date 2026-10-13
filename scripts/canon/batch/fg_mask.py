#!/usr/bin/env python3
"""macOS Vision 전경 마스크로 인물 판(흰 단색 배경)을 알파 PNG로 오린다 (scene-anim-eval/layers/fg_mask.py 승격).

  ~/.local/biblemap-manimgx/.venv/bin/python fg_mask.py <src.png> <dst.png>      # pyobjc(Vision)는 그 venv에만 있다

Vision 마스크는 창·방패 테 같은 가는 지물을 놓친다 → 마스크를 키운 영역 안의 「배경색과 다른 픽셀」을 합집합한다.
"""
import sys
import Vision, Quartz
from Foundation import NSURL
import numpy as np
from PIL import Image, ImageFilter

GROW = 41       # 가는 지물 구조 반경(px, 홀수) — 마스크 밖 이만큼까지 비배경 픽셀을 되살린다
BG_DIFF = 28    # 모서리 배경색과의 채널 차이가 이보다 크면 비배경


def vision_mask(path):
    h = Vision.VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(path), None)
    req = Vision.VNGenerateForegroundInstanceMaskRequest.alloc().init()
    ok, err = h.performRequests_error_([req], None)
    assert ok, err
    if not req.results():
        return None
    obs = req.results()[0]
    buf, err = obs.generateScaledMaskForImageForInstances_fromRequestHandler_error_(obs.allInstances(), h, None)
    Quartz.CVPixelBufferLockBaseAddress(buf, 0)
    w, hh = Quartz.CVPixelBufferGetWidth(buf), Quartz.CVPixelBufferGetHeight(buf)
    stride = Quartz.CVPixelBufferGetBytesPerRow(buf)
    raw = np.frombuffer(Quartz.CVPixelBufferGetBaseAddress(buf).as_buffer(stride * hh), dtype=np.float32).reshape(hh, stride // 4)[:, :w]
    m = (np.clip(raw, 0, 1) * 255).astype(np.uint8).copy()
    Quartz.CVPixelBufferUnlockBaseAddress(buf, 0)
    return Image.fromarray(m)


def cutout(src, dst):
    """→ 투명 픽셀 비율. 마스크가 없으면 None."""
    img = Image.open(src).convert("RGB")
    vm = vision_mask(src)
    if vm is None:
        return None
    a = np.asarray(img).astype(int)
    bg = np.median(np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3)]), axis=0)
    nonbg = np.abs(a - bg).max(axis=2) > BG_DIFF
    near = np.asarray(vm.filter(ImageFilter.MaxFilter(GROW))) > 8
    alpha = np.maximum(np.asarray(vm), ((nonbg & near) * 255).astype(np.uint8))
    out = img.convert("RGBA")
    out.putalpha(Image.fromarray(alpha, "L"))
    out.save(dst)
    return float((alpha < 8).mean())


if __name__ == "__main__":
    print(cutout(sys.argv[1], sys.argv[2]))
