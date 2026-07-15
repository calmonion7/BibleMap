"""전체 성경 구절↔단어 역색인 정본(data/word_verse_index/index.json) 빌드타임 산출.

data/bible/verses.json(textKo)에서 kiwipiepy로 일반명사(NNG)·고유명사(NNP)를
추출해 `단어(lemma) → [verseID, ...]` 역색인을 만든다. 단어 분포
(build_word_distribution.py)와 **동일한 토큰화 규약**을 쓰되(같은 NNG/NNP·len>=2·
STOPWORDS — 드리프트 방지를 위해 STOPWORDS를 그 스크립트에서 import),
집계가 아니라 색인이므로 MIN_COUNT 필터는 적용하지 않는다(1회 등장 단어도 조회 가능해야
함). verseID는 verses.json 키 규약 BBCCCVVV.

**매칭 특성**: 이 색인은 lemma(형태소 원형) 기반이라, 런타임 substring 매칭
(routes/words.py의 /words/{id}/verses?w=)과 커버리지가 다를 수 있다 — kiwi가
"사랑하여"를 lemma "사랑"으로 정규화하므로 활용형을 원형으로 묶어 잡지만, 부분 문자열
매칭(예: 합성어 내부)은 잡지 않는다. 기존 substring 엔드포인트 동작은 이 색인이
바꾸지 않는다(재사용 인프라로만 추가).

실행(그래프 미접근 — Neo4j 환경변수 불필요, kiwipiepy 필요):
    python -m venv /tmp/kiwi-venv && /tmp/kiwi-venv/bin/pip install kiwipiepy
    /tmp/kiwi-venv/bin/python backend/scripts/build_word_verse_index.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_word_distribution import STOPWORDS  # 토큰화 규약 정본 재사용(드리프트 방지)

DATA = Path(__file__).resolve().parents[2] / "data"
OUT_DIR = DATA / "word_verse_index"


def main():
    verses = json.loads((DATA / "bible" / "verses.json").read_text())

    from kiwipiepy import Kiwi

    kiwi = Kiwi()
    index = defaultdict(set)  # lemma → {verseID}
    processed = 0
    for key, v in verses.items():
        text = v.get("textKo")
        if not text:
            continue
        processed += 1
        for tok in kiwi.tokenize(text):
            if tok.tag in ("NNG", "NNP") and len(tok.form) >= 2 and tok.form not in STOPWORDS:
                index[tok.form].add(key)

    out = {w: sorted(ids) for w, ids in sorted(index.items())}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "index.json").write_text(json.dumps(out, ensure_ascii=False, indent=0) + "\n")

    postings = sum(len(ids) for ids in out.values())
    print(
        f"word_verse_index/index.json written: {len(out)} unique words, "
        f"{postings} postings, {processed} verses processed"
    )


if __name__ == "__main__":
    main()
