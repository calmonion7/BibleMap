"""책별 단어 분포 정본(data/word_distribution.json) 빌드타임 산출.

data/bible/verses.json(textKo)에서 kiwipiepy로 일반명사(NNG)·고유명사(NNP)를
추출해 책별 + 성경 전체("all") 상위 빈도 단어를 집계하고,
감정 극성 정본 data/word_sentiment.json(word → positive|negative|neutral)을
병합해 data/word_distribution.json을 쓴다.

실행(그래프 미접근 — Neo4j 환경변수 불필요, kiwipiepy 필요):
    python -m venv /tmp/kiwi-venv && /tmp/kiwi-venv/bin/pip install kiwipiepy
    /tmp/kiwi-venv/bin/python backend/scripts/build_word_distribution.py
    /tmp/kiwi-venv/bin/python backend/scripts/build_word_distribution.py --dump-words  # 감정 미분류 단어 목록만 출력

책 식별자: data/names_ko/books.json의 키 순서(정경 66권 순) = verses.json 키의
책 번호(BBCCCVVV의 BB, 1~66). 산출 JSON의 키는 theographic_id, 전체 집계는 "all".
"""
import json
import sys
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
TOP_PER_BOOK = 60
TOP_ALL = 120
MIN_COUNT = 2
# 구조적/기능적 명사 — 의미 신호가 약해 클라우드에서 제외
STOPWORDS = {"때문", "가운데", "그것", "무엇", "어디", "누구", "이것", "저것", "여기", "거기"}


def main():
    dump_words = "--dump-words" in sys.argv

    verses = json.loads((DATA / "bible" / "verses.json").read_text())
    books_ko = json.loads((DATA / "names_ko" / "books.json").read_text())
    book_ids = list(books_ko.keys())  # 정경 순서 1~66
    assert len(book_ids) == 66, f"names_ko/books.json expected 66 books, got {len(book_ids)}"

    from kiwipiepy import Kiwi

    kiwi = Kiwi()
    per_book = [Counter() for _ in range(66)]
    for key, v in verses.items():
        text = v.get("textKo")
        if not text:
            continue
        bi = int(key[:2]) - 1
        for tok in kiwi.tokenize(text):
            if tok.tag in ("NNG", "NNP") and len(tok.form) >= 2 and tok.form not in STOPWORDS:
                per_book[bi][tok.form] += 1

    total = Counter()
    for c in per_book:
        total.update(c)

    tops = {}  # key(id|"all") → [(word, count)]
    for bi, book_id in enumerate(book_ids):
        tops[book_id] = [(w, n) for w, n in per_book[bi].most_common(TOP_PER_BOOK) if n >= MIN_COUNT]
    tops["all"] = total.most_common(TOP_ALL)

    needed = sorted({w for words in tops.values() for w, _ in words})

    sentiment_path = DATA / "word_sentiment.json"
    sentiment = json.loads(sentiment_path.read_text()) if sentiment_path.exists() else {}
    missing = [w for w in needed if w not in sentiment]

    if dump_words:
        print("\n".join(missing))
        print(f"# unique={len(needed)} missing={len(missing)}", file=sys.stderr)
        return

    if missing:
        sys.exit(f"word_sentiment.json에 미분류 단어 {len(missing)}건 — --dump-words로 목록 확인 후 큐레이션 필요")

    out = {}
    for key, words in tops.items():
        entry = {"words": [{"word": w, "count": n, "polarity": sentiment[w]} for w, n in words]}
        if key != "all":
            entry["nameKo"] = books_ko[key]["ko"]
        out[key] = entry
    (DATA / "word_distribution.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    )
    n_words = sum(len(e["words"]) for e in out.values())
    print(f"word_distribution.json written: {len(out)} entries, {n_words} word rows, {len(needed)} unique words")


if __name__ == "__main__":
    main()
