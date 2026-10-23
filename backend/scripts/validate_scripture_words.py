"""data/scripture_words/words.json이 AUTHORING.md 규칙을 지키는지 기계검증한다.

검사: ① refs가 정본 절 사전(bible/verses.json)에서 풀리고 그 절 textKo에 word나 forms 하나가 있음(용례)
② meaning·look·features 근거가 근거 단계 머리말([직접]·[추론]·[저작](이유))로 시작
③ look L1·L2·L3 en 낱말 수 8·30·60 이하, 추상어 금지 목록 없음 ④ meaning.ko 2문장·80자 이하
⑤ criteria.features 3개 이상, 문항마다 「?」로 끝남 ⑥ verified_level 꼴
⑦ drawable:false 항목은 signs 1개 이상, 각 id가 사전에 실재하는 그리는 항목. id·word 중복 금지.
위반이 있으면 목록 출력 + 종료 코드 1, 사전 파일이 없으면 종료 코드 2.
--selftest: 내장 정상 사본이 통과하고, 일부러 깨뜨린 사본 여섯이 각각 불통해야 종료 0.
"""
import copy
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
WORDS_PATH = DATA / "scripture_words" / "words.json"

# AUTHORING.md §3 규칙 3과 이중 관리
FORBIDDEN = {"pretend", "feign", "feigning", "sacred", "holy", "ceremonial", "symbolic", "ritual", "divine"}
LEVEL_MAX = {"L1": 8, "L2": 30, "L3": 60}
SIZE_REFS = {"man-height"}   # look.size.ref — 사람 키에 견줌(task 405)
MEANING_MAX_CHARS = 80
MEANING_MAX_SENTENCES = 2
MIN_FEATURES = 3
STATUSES = {"확정", "조건부"}

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GROUNDS_RE = re.compile(r"^\[(직접|추론)\]|^\[저작\]\([^)]+\)")
_REF = re.compile(r"^(\S+)\s+(\d+):(\d+)(?:-(\d+))?$")


def _build_resolver():
    books = json.loads((DATA / "names_ko" / "books.json").read_text())
    verses = json.loads((DATA / "bible" / "verses.json").read_text())
    alias2bb = {}
    for i, (_, v) in enumerate(books.items(), 1):
        for a in v.get("alias", []):
            alias2bb[a] = i
        alias2bb[v["ko"]] = i

    def resolve(ref: str):
        """참조 → 절 본문(textKo) 목록. 풀리지 않으면 None."""
        m = _REF.match((ref or "").strip())
        if not m:
            return None
        bb = alias2bb.get(m.group(1))
        if not bb:
            return None
        ch, start = int(m.group(2)), int(m.group(3))
        end = int(m.group(4)) if m.group(4) else start
        if end < start:
            return None
        texts = []
        for vs in range(start, end + 1):
            v = verses.get(f"{bb:02d}{ch:03d}{vs:03d}")
            if v is None:
                return None
            texts.append(v["textKo"])
        return texts

    return resolve


def _nospace(s):
    return re.sub(r"\s+", "", s or "")


def _sentences(s):
    return [p for p in re.split(r"[.!?。]+", s or "") if p.strip()]


def check(data, resolve):
    errors = []
    words = data.get("words") if isinstance(data, dict) else None
    if not isinstance(words, list):
        return ["최상위 words 배열 없음"]

    by_id = {}
    seen_word = set()
    for i, e in enumerate(words):
        eid = e.get("id")
        if not (isinstance(eid, str) and ID_RE.match(eid)):
            errors.append(f"[{i}]: id kebab 아님 '{eid}'")
        elif eid in by_id:
            errors.append(f"{eid}: id 중복")
        else:
            by_id[eid] = e
        if e.get("word") in seen_word:
            errors.append(f"{eid}: word 중복 '{e.get('word')}' (한 낱말 한 항목)")
        seen_word.add(e.get("word"))

    for e in words:
        tag = e.get("id")
        word = e.get("word")
        forms = e.get("forms")
        if not (isinstance(word, str) and word):
            errors.append(f"{tag}: word 결손")
            continue
        if not isinstance(forms, list):
            errors.append(f"{tag}: forms 배열 아님")
            forms = []
        if not (isinstance(e.get("kjv"), str) and e["kjv"]):
            errors.append(f"{tag}: kjv 결손")

        # ① 용례 검증
        needles = [_nospace(x) for x in [word, *forms] if x]
        refs = e.get("refs")
        if not (isinstance(refs, list) and refs):
            errors.append(f"{tag}: refs 비어있음")
            refs = []
        for ref in refs:
            texts = resolve(ref)
            if texts is None:
                errors.append(f"{tag}: refs 해석 실패 '{ref}'")
            elif not any(n in _nospace(t) for t in texts for n in needles):
                errors.append(f"{tag}: '{ref}' 본문에 word·forms 없음")

        # ②④ 뜻
        meaning = e.get("meaning")
        if not isinstance(meaning, dict):
            errors.append(f"{tag}: meaning 객체 결손")
        else:
            ko = meaning.get("ko") or ""
            if not ko:
                errors.append(f"{tag}: meaning.ko 결손")
            if len(ko) > MEANING_MAX_CHARS:
                errors.append(f"{tag}: meaning.ko {len(ko)}자 (허용 ≤{MEANING_MAX_CHARS})")
            if len(_sentences(ko)) > MEANING_MAX_SENTENCES:
                errors.append(f"{tag}: meaning.ko {len(_sentences(ko))}문장 (허용 ≤{MEANING_MAX_SENTENCES})")
            if not GROUNDS_RE.match(meaning.get("grounds") or ""):
                errors.append(f"{tag}: meaning.grounds 근거 단계 머리말 없음")

        drawable = e.get("drawable", True)
        if drawable is False:
            # ⑦ 그릴 수 없는 낱말 — 보이는 표지로
            if "look" in e or "criteria" in e:
                errors.append(f"{tag}: drawable:false 항목에 look·criteria 있음")
            signs = e.get("signs")
            if not (isinstance(signs, list) and signs):
                errors.append(f"{tag}: drawable:false인데 signs 없음")
                signs = []
            for sid in signs:
                s = by_id.get(sid)
                if s is None:
                    errors.append(f"{tag}: signs의 '{sid}'가 사전에 없음")
                elif s.get("drawable", True) is False or "look" not in s:
                    errors.append(f"{tag}: signs의 '{sid}'가 그리는 항목 아님")
            continue
        if "signs" in e:
            errors.append(f"{tag}: signs는 drawable:false 항목에만")

        # ②③ 모양
        look = e.get("look")
        if not isinstance(look, dict):
            errors.append(f"{tag}: look 객체 결손")
        else:
            for lv, mx in LEVEL_MAX.items():
                step = look.get(lv)
                if not (isinstance(step, dict) and step.get("ko") and step.get("en")):
                    errors.append(f"{tag}: look.{lv} ko·en 결손")
                    continue
                toks = re.findall(r"[A-Za-z']+", step["en"])
                if len(toks) > mx:
                    errors.append(f"{tag}: look.{lv}.en {len(toks)}낱말 (허용 ≤{mx})")
                bad = sorted({t.lower() for t in toks} & FORBIDDEN)
                if bad:
                    errors.append(f"{tag}: look.{lv}.en 금지어 {bad}")
            if not GROUNDS_RE.match(look.get("grounds") or ""):
                errors.append(f"{tag}: look.grounds 근거 단계 머리말 없음")
            size = look.get("size")   # 크기(사람 몸에 견줌, task 405 — 규칙 derive.prop-size-relative): 있으면 꼴과 L2 문구를 잰다
            if size is not None:
                if size.get("ref") not in SIZE_REFS or not isinstance(size.get("ratio"), (int, float)) or not 0 < size["ratio"] <= 3:
                    errors.append(f"{tag}: look.size ref({'·'.join(sorted(SIZE_REFS))})·ratio(0~3) 결손")
                if not (size.get("ko") and size.get("en")) or not GROUNDS_RE.match(size.get("grounds") or ""):
                    errors.append(f"{tag}: look.size ko·en·근거 머리말 결손")
                for ph in [size.get("en", "")] + [pp.get("en", "") for pp in (size.get("parts") or {}).values()]:
                    if ph and ph not in (look.get("L2") or {}).get("en", ""):
                        errors.append(f"{tag}: look.size 문구 「{ph}」가 L2 en에 없음")

        # ②⑤ 판정 기준
        crit = e.get("criteria")
        if not isinstance(crit, dict):
            errors.append(f"{tag}: criteria 객체 결손")
        else:
            if not crit.get("ko"):
                errors.append(f"{tag}: criteria.ko 결손")
            feats = crit.get("features")
            if not (isinstance(feats, list) and len(feats) >= MIN_FEATURES):
                n = len(feats) if isinstance(feats, list) else 0
                errors.append(f"{tag}: criteria.features {n}개 (최소 {MIN_FEATURES})")
                feats = feats if isinstance(feats, list) else []
            for j, f in enumerate(feats):
                if not (f.get("q") or "").rstrip().endswith("?"):
                    errors.append(f"{tag}: features[{j}].q 「?」로 안 끝남")
                if not GROUNDS_RE.match(f.get("grounds") or ""):
                    errors.append(f"{tag}: features[{j}].grounds 근거 단계 머리말 없음")

        # ⑥ 그림 증거
        vl = e.get("verified_level")
        if vl is not None:
            if not (isinstance(vl, dict) and vl.get("level") in LEVEL_MAX and vl.get("status") in STATUSES
                    and isinstance(vl.get("with"), list)):
                errors.append(f"{tag}: verified_level 꼴 위반 {vl}")
            else:
                for wid in vl["with"]:
                    if wid not in by_id:
                        errors.append(f"{tag}: verified_level.with의 '{wid}'가 사전에 없음")
    return errors


# --selftest용 정상 사본 — 실제 본문(삼상 16:13·21:13)에 기대므로 정본 절 사전이 바뀌면 같이 본다
_FIXTURE = {"version": 1, "words": [
    {"id": "oil-horn", "word": "기름 뿔", "forms": ["기름 뿔을"], "kjv": "horn of oil", "refs": ["삼상 16:13"],
     "meaning": {"ko": "기름을 담는 짐승의 뿔이에요.", "grounds": "[직접] 삼상 16:13 「기름 뿔을 취하여」"},
     "look": {"L1": {"ko": "기름 뿔", "en": "an animal horn of oil"},
              "L2": {"ko": "기름이 든 굽은 짐승 뿔", "en": "a curved animal horn filled with olive oil"},
              "L3": {"ko": "손에 쥔 굽은 뿔", "en": "a curved animal horn as long as a forearm, held in one hand, oil pouring from its tip"},
              "grounds": "[추론] 삼상 16:1 「기름을 뿔에 채워」 — 뿔이 그릇으로 쓰임"},
     "criteria": {"ko": "굽은 짐승 뿔에서 기름이 흐른다.",
                  "features": [{"q": "뿔이 한쪽으로 굽었나?", "grounds": "[추론] 짐승 뿔"},
                               {"q": "끝이 좁아지나?", "grounds": "[추론] 짐승 뿔"},
                               {"q": "끝에서 기름이 흐르나?", "grounds": "[직접] 삼상 16:13 「부었더니」"}]}},
    {"id": "scrabble-on-gate-doors", "word": "대문짝에 그적거리다", "forms": ["대문짝에 그적거리며"],
     "kjv": "scrabbled on the doors of the gate", "refs": ["삼상 21:13"],
     "meaning": {"ko": "성문 문짝을 손으로 마구 긁적이는 거예요.", "grounds": "[직접] 삼상 21:13 「대문짝에 그적거리며」"},
     "look": {"L1": {"ko": "문짝 긁기", "en": "scratching on a gate door"},
              "L2": {"ko": "손톱으로 큰 나무 문을 긁음", "en": "a man scratching marks on a big wooden gate door with his fingers"},
              "L3": {"ko": "자세히", "en": "a man bent at a tall wooden city gate door, scraping lines into the wood with his fingernails"},
              "grounds": "[직접] 삼상 21:13"},
     "criteria": {"ko": "성문 문짝을 손가락으로 긁는다.",
                  "features": [{"q": "문이 나무 문짝인가?", "grounds": "[저작](성문 재료 고증)"},
                               {"q": "손가락이 문에 닿았나?", "grounds": "[직접] 삼상 21:13"},
                               {"q": "문에 긁힌 자국이 있나?", "grounds": "[추론] 그적거림의 결과"}]}},
    {"id": "feign-madness", "word": "미친 체", "forms": ["미친 체 하고"], "kjv": "feigned himself mad",
     "refs": ["삼상 21:13"], "drawable": False, "signs": ["scrabble-on-gate-doors"],
     "meaning": {"ko": "미친 사람처럼 꾸며 보이는 거예요.", "grounds": "[직접] 삼상 21:13 「미친 체 하고」"}},
]}


def _break(fx, how):
    d = copy.deepcopy(fx)
    w = {e["id"]: e for e in d["words"]}
    if how == "낱말 없는 절":
        w["oil-horn"]["refs"].append("창 1:1")
    elif how == "금지어":
        w["oil-horn"]["look"]["L2"]["en"] = "a sacred curved animal horn filled with oil"
    elif how == "근거 단계 뺌":
        w["oil-horn"]["look"]["grounds"] = "삼상 16:1 — 뿔이 그릇으로 쓰임"
    elif how == "L2 31낱말":
        w["oil-horn"]["look"]["L2"]["en"] = " ".join(["horn"] * 31)
    elif how == "features 2개":
        w["oil-horn"]["criteria"]["features"] = w["oil-horn"]["criteria"]["features"][:2]
    elif how == "signs 없는 id":
        w["feign-madness"]["signs"] = ["no-such-word"]
    return d


def selftest(resolve):
    ok = True
    base = check(_FIXTURE, resolve)
    if base:
        print(f"[validate_scripture_words] selftest 정상 사본이 불통: {base}")
        ok = False
    for how in ("낱말 없는 절", "금지어", "근거 단계 뺌", "L2 31낱말", "features 2개", "signs 없는 id"):
        errs = check(_break(_FIXTURE, how), resolve)
        print(f"  {'✅' if errs else '❌'} {how}: 위반 {len(errs)}건{' — ' + errs[0] if errs else ' (잡지 못함)'}")
        ok = ok and bool(errs)
    print(f"[validate_scripture_words] selftest {'OK' if ok else '실패'}")
    sys.exit(0 if ok else 1)


def main():
    resolve = _build_resolver()
    if "--selftest" in sys.argv[1:]:
        selftest(resolve)
    if not WORDS_PATH.exists():
        print(f"[validate_scripture_words] {WORDS_PATH} 없음")
        sys.exit(2)
    try:
        data = json.loads(WORDS_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"[validate_scripture_words] JSON 파싱 실패 — {e}")
        sys.exit(1)
    errors = check(data, resolve)
    if errors:
        print(f"[validate_scripture_words] 위반 {len(errors)}건:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    n = len(data["words"])
    nd = sum(1 for e in data["words"] if e.get("drawable", True) is False)
    print(f"[validate_scripture_words] OK — 항목 {n}개(그릴 수 없음 {nd}) · 위반 0")


if __name__ == "__main__":
    main()
