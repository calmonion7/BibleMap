"""77토큰 벽을 넘는 긴 프롬프트 — 조각 인코딩 + 임베딩 이어붙이기 (2026-08-26).

**왜 있는가.** CLIP은 77토큰에서 **에러 없이 자른다**(PROMPTING.md 1). 이 프로젝트의 프롬프트는
화풍 블록만 35토큰이라 늘 71~77에 붙어 있었고, 그래서 항목을 넣으려면 다른 항목을 빼야 했다
(규칙 8이 관찰한 「의상과 머리쓰개가 예산을 놓고 싸운다」의 절반은 이 벽 때문이었다).
사용자 질문("자세히 서술하면 원하는 그림이 나오지 않나")에 답하려면 먼저 이 벽을 넘어야 했다.

**방법.** 텍스트를 쉼표 단위로 묶어 각 조각이 **두 토크나이저 모두에서** 75토큰 이내가 되게 나누고,
조각마다 `pipe.encode_prompt`를 불러 임베딩을 시퀀스 축으로 이어붙인다(A1111·ComfyUI와 같은 방식).
`pooled` 임베딩은 첫 조각의 것을 쓴다. CFG는 긍정·부정의 시퀀스 길이가 같아야 하므로 짧은 쪽을
마지막 조각으로 패딩한다. **새 의존성 없음** — diffusers 0.40의 `prompt_embeds` 경로다.

**실측(같은 날, 골리앗 · 시드 11·42 · 무레퍼런스)**: 117토큰 프롬프트가 오류 없이 통과했고,
가장 자세히 쓴 항목(「베틀채 같은 굵은 자루 + 거대한 쇠 창끝」의 창)이 **2/2로 나왔다** —
짧은 프롬프트에서는 1/2였다. **그러나 같은 프롬프트의 다른 항목이 밀렸다**: 대검 0/2 · 뿔 투구 소실 ·
시드 42에서 수염이 나 5축(수염 없음)을 위반했다. 결론은 PROMPTING.md 10에 적었다 —
**벽을 넘어도 주의(attention)는 유한하다.** 한 프롬프트에 여러 지물을 자세히 넣으면 서로 밀어낸다.

Usage:
    import long_prompt as lp
    kw = lp.encode(pipe, positive, negative, device="mps")
    pipe(**kw, width=..., height=..., ...)
"""
import torch

CHUNK_LIMIT = 75   # 77 − BOS/EOS


def split_chunks(pipe, text, limit=CHUNK_LIMIT):
    """쉼표 단위로 묶어 각 조각이 두 토크나이저 모두에서 limit 이내가 되게 나눈다.
    쉼표 하나가 이미 limit을 넘으면 그 조각은 그대로 둔다(그 안에서 잘리는 것은 원문의 문제다)."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    def fits(seg):
        return (len(pipe.tokenizer(seg, add_special_tokens=False).input_ids) <= limit and
                len(pipe.tokenizer_2(seg, add_special_tokens=False).input_ids) <= limit)
    chunks, cur = [], []
    for p in parts:
        if cur and not fits(", ".join(cur + [p])):
            chunks.append(", ".join(cur))
            cur = [p]
        else:
            cur.append(p)
    if cur:
        chunks.append(", ".join(cur))
    return chunks


def encode(pipe, positive, negative, device):
    """`pipe(**kw)`에 그대로 넘길 임베딩 4종을 낸다."""
    cp, cn = split_chunks(pipe, positive), split_chunks(pipe, negative)
    n = max(len(cp), len(cn))
    cp += [cp[-1]] * (n - len(cp))     # CFG는 긍정·부정 길이가 같아야 한다
    cn += [cn[-1]] * (n - len(cn))
    pos_e, neg_e, pooled_p, pooled_n = [], [], None, None
    for i in range(n):
        pe, ne, pp, npp = pipe.encode_prompt(
            prompt=cp[i], negative_prompt=cn[i], device=device,
            num_images_per_prompt=1, do_classifier_free_guidance=True)
        pos_e.append(pe)
        neg_e.append(ne)
        if i == 0:
            pooled_p, pooled_n = pp, npp
    return {
        "prompt_embeds": torch.cat(pos_e, dim=1),
        "negative_prompt_embeds": torch.cat(neg_e, dim=1),
        "pooled_prompt_embeds": pooled_p,
        "negative_pooled_prompt_embeds": pooled_n,
    }
