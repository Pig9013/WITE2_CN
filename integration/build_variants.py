r"""从简体底本生成繁体变体（台湾 / 香港 / 澳门），简体底本保持不变。

用法：python integration\build_variants.py

前置：mod\build_maps.py 已产出 mod\payload\translations.json（简体）与 payload\overlay（简体 overlay）
产出：
  mod\payload\variants\<code>\translations.bin   语言包（启动器按选择物化到 payload\translations.bin）
  mod\payload\variants\<code>\overlay\...        该变体的 overlay（字体 / Info CSV / Scen 文本）
  audit\variants.audit.json                      逐变体守卫与字形覆盖结果

设计要点：
  1. 键（英文原文）一律不转换，只转值，四套语言包键集合因此完全一致；
  2. 台湾用 s2tw、香港/澳门用 s2hk（含 HKVariants 地区用字：裏/裡、着/著、麪/麵）；
  3. 不用 s2twp：它的短语表把地名当常用词换掉（比特費爾德→位元費爾德、布爾加斯→布林加斯、
     圖庫姆斯→相簿姆斯），实测 4,000 条约 35 条被污染；本项目严禁专名按字面义直译；
  4. 词汇层（坦克/戰車、意大利/義大利）不做自动替换，留给 glossary\variants_overrides.json 人工裁决。
"""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

import opencc
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

MOD = Path(__file__).resolve().parent.parent / "mod"
PROJECT = MOD.parent
PAYLOAD = MOD / "payload"
OUT = PAYLOAD / "variants"

# code, opencc 配置, 显示名, 字体底本（都必须是 2048 upem）
VARIANTS = [
    ("zh-CN", None, "简体中文（中国大陆）", "msyh.ttc"),
    ("zh-TW", "s2tw", "繁體中文（台灣）", "msjh.ttc"),
    ("zh-HK", "s2hk", "繁體中文（香港）", "msjh.ttc"),
    ("zh-MO", "s2hk", "繁體中文（澳門）", "msjh.ttc"),
]
FONT_DIR = Path(r"C:\Windows\Fonts")
FALLBACK_FONTS = ["Deng.ttf", "arial.ttf", "ebrima.ttf", "malgun.ttf"]
ASCII = "".join(chr(i) for i in range(0x20, 0x7F))
PUNCT = "，。！？；：、“”‘’（）《》〈〉—…·【】〔〕％＋－×÷＝／＼～　"
PLACEHOLDER = re.compile(r"%(?:%|[-+ 0#]*\d*(?:\.\d+)?(?:I64|ll|l|h)?[sSdiuoxXfFeEgGcCp])")
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
KEEP_TABLES = {"GlyphOrder", "head", "hhea", "maxp", "OS/2", "hmtx", "cmap", "loca",
               "glyf", "name", "post"}


# ── 转换后修正层 ─────────────────────────────────────────────────────────
# OpenCC 的短语表在这几处会把常用字换错（都是 1:1 换字，不改长度）：
#   佈：布→佈 只该用在 宣佈/公佈/分佈 一类，地名音译必须留「布」（布雷達/佈列斯特/佈雷斯勞）；
#   併：并→併 只该用在 合併/併吞，其余（併成為、併發起）都是「並」；
#   瞭：了→瞭 只该用在 瞭解，動詞+了（參與瞭/參加瞭）是误换；
#   周：周→週 只该用在週次（幾周後），周圍/周邊 不动。
# 规则只做高置信度替换，并且先保护白名单词，宁可少改不多改。
PROTECT_BU = ["宣佈", "公佈", "發佈", "分佈", "散佈", "頒佈", "佈置", "佈防", "佈設",
              "佈局", "佈告", "佈滿", "遍佈", "密佈", "佈陣", "佈署"]
PROTECT_BING = ["合併", "併吞", "兼併", "併購", "併入", "併案", "歸併", "收併", "併合",
                "併攏", "併發症"]
LIAO_VERB = re.compile(r"(參與|參加|使用|成立|開始|結束|重返|加入|投入|進入)瞭")
WEEK_FIX = [("幾周", "幾週"), ("一周", "一週"), ("兩周", "兩週"), ("三周", "三週"),
            ("數周", "數週"), ("周後", "週後")]


def polish(text: str) -> str:
    saved = {}

    def protect(words, body):
        for index, word in enumerate(sorted(words, key=len, reverse=True)):
            if word in body:
                token = "\u0001" + str(index) + "\u0002"
                saved[token] = word
                body = body.replace(word, token)
        return body

    body = protect(PROTECT_BU, text)
    body = protect(PROTECT_BING, body)
    body = body.replace("佈", "布").replace("併", "並").replace("占領", "佔領")
    body = LIAO_VERB.sub(r"\1了", body)
    for wrong, right in WEEK_FIX:
        body = body.replace(wrong, right)
    for token, word in saved.items():
        body = body.replace(token, word)
    return body


def skeleton(text: str) -> str:
    """去掉汉字后的骨架：拉丁、数字、标点必须逐字不变。"""
    return CJK.sub("", text)


def balanced(text: str) -> bool:
    return text.count("（") == text.count("）") and text.count("(") == text.count(")")


def write_bin(entries: dict, path: Path) -> int:
    blob = bytearray(b"W2CNMAP1" + struct.pack("<I", len(entries)))
    for src, dst in sorted(entries.items()):
        a, b = src.encode("utf-16le"), dst.encode("utf-16le")
        blob += struct.pack("<II", len(a) // 2, len(b) // 2) + a + b
    path.write_bytes(blob)
    return len(blob)


def font_chars(entries: dict, overlay_text: str) -> str:
    chars = set(ASCII) | set(PUNCT) | set("\u00a0\u2013\u2014\u2026\u00b7")
    chars.update("".join(entries.keys()))
    chars.update("".join(entries.values()))
    chars.update(overlay_text)
    chars = {c for c in chars
             if ord(c) >= 0x20 and c != "\ufffd" and not (0xD800 <= ord(c) <= 0xDFFF)}
    return "".join(sorted(chars))


def subset_font(base: str, chars: str, out: Path) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    path = FONT_DIR / base
    font = TTFont(path, fontNumber=0) if base.lower().endswith((".ttc", ".otc")) else TTFont(path)
    options = Options()
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.notdef_outline = True
    options.recalc_bounds = True
    options.drop_tables += ["DSIG"]
    subsetter = Subsetter(options=options)
    subsetter.populate(text=chars)
    subsetter.subset(font)
    for record in font["name"].names:
        if record.nameID in (1, 3, 4, 6, 16, 17):
            try:
                record.string = "WitE2CN"
            except Exception:
                pass
    # 与简体版字库保持同一套表（引擎逐字光栅化，不做整形；保留 GSUB/GPOS/hdmx 只会让文件大三倍）
    for glyph in font["glyf"].glyphs.values():
        glyph.removeHinting()
    for tag in list(font.keys()):
        if tag not in KEEP_TABLES:
            del font[tag]

    missing = {ord(c) for c in chars if ord(c) not in font.getBestCmap()}
    filled = 0
    if missing:
        # 补字源必须与底本 upem 一致（2048）；SimHei 是 256，merge 会崩
        import shutil
        import tempfile
        from fontTools.merge import Merger
        temp = Path(tempfile.mkdtemp(prefix="WitE2CN-variant-font-"))
        try:
            base_file = temp / "base.ttf"
            font.save(base_file)
            inputs = [str(base_file)]
            for name in FALLBACK_FONTS:
                donor_path = FONT_DIR / name
                if not donor_path.exists():
                    continue
                donor = TTFont(donor_path)
                include = missing & set(donor.getBestCmap())
                if not include:
                    donor.close()
                    continue
                dopts = Options()
                dopts.layout_features = []
                dopts.hinting = False
                dopts.drop_tables += ["DSIG", "GSUB", "GPOS"]
                sub = Subsetter(options=dopts)
                sub.populate(unicodes=include)
                sub.subset(donor)
                for tag in list(donor.keys()):
                    if tag not in ("GlyphOrder", "head", "hhea", "maxp", "OS/2", "hmtx",
                                   "cmap", "loca", "glyf", "name", "post"):
                        del donor[tag]
                target = temp / name
                donor.save(target)
                donor.close()
                inputs.append(str(target))
                missing -= include
                filled += len(include)
            if missing:
                raise SystemExit("字体缺字且无法补齐：" + "".join(chr(c) for c in sorted(missing)))
            merged = Merger().merge(inputs)
            for record in merged["name"].names:
                if record.nameID in (1, 3, 4, 6, 16):
                    try:
                        record.string = "WitE2CN"
                    except Exception:
                        pass
            merged.save(out)
        finally:
            shutil.rmtree(temp, ignore_errors=True)
    else:
        font.save(out)
    font.close()

    final = TTFont(out)
    cmap = final.getBestCmap()
    absent = "".join(c for c in chars if ord(c) not in cmap)
    final.close()
    return {"base": base, "bytes": out.stat().st_size, "glyphs": len(cmap),
            "requested": len(chars), "filled_from_fallbacks": filled, "absent": absent}


def convert_overlay(code: str) -> tuple[list[str], int]:
    r"""把 payload\overlay 的文本文件转成该变体；字体另行子集化。"""
    src_root = PAYLOAD / "overlay"
    dst_root = OUT / code / "overlay"
    files, chars = [], 0
    for path in sorted(src_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() == ".ttf":
            continue
        rel = path.relative_to(src_root)
        raw = path.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        conv = opencc.OpenCC(VARIANTS_BY_CODE[code])
        converted = polish(conv.convert(text))
        target = dst_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(converted, encoding="utf-8-sig" if bom else "utf-8", newline="")
        files.append(str(rel).replace("\\", "/"))
        chars += len(converted)
    return files, chars


VARIANTS_BY_CODE = {code: cfg for code, cfg, _, _ in VARIANTS if cfg}


def main() -> int:
    cn_path = PAYLOAD / "translations.json"
    cn_bin = PAYLOAD / "translations.bin"
    if not cn_path.exists() or not cn_bin.exists():
        raise SystemExit("缺少 mod\\payload\\translations.json/.bin；先跑 mod\\build_maps.py")
    cn = json.loads(cn_path.read_text(encoding="utf8"))

    overrides_path = PROJECT / "glossary" / "variants_overrides.json"
    overrides = json.loads(overrides_path.read_text(encoding="utf8")) if overrides_path.exists() else {}

    OUT.mkdir(parents=True, exist_ok=True)
    audit = {"source_entries": len(cn), "overrides_file": str(overrides_path.relative_to(PROJECT)),
             "variants": []}

    for code, cfg, label, base_font in VARIANTS:
        variant_dir = OUT / code
        variant_dir.mkdir(parents=True, exist_ok=True)
        table = overrides.get(code, {}) or {}
        if not isinstance(table, dict):
            raise SystemExit(f"variants_overrides.json 的 {code} 必须是对象")

        conv = opencc.OpenCC(cfg) if cfg else None
        entries, changed, polished = {}, 0, 0
        for key, value in cn.items():
            if conv is None:
                out = value
            elif value in table:
                out = table[value]
            else:
                converted = polish(conv.convert(value))
                if converted != conv.convert(value):
                    polished += 1
                out = converted
            entries[key] = out
            if out != value:
                changed += 1

        if len(entries) != len(cn):
            raise SystemExit(f"{code}: 条目数 {len(entries)} != 简体 {len(cn)}")

        bad = []
        for key, value in entries.items():
            ref = cn[key]
            reasons = []
            if "\ufffd" in value:
                reasons.append("替换字符")
            if skeleton(value) != skeleton(ref):
                reasons.append("拉丁/数字/标点骨架被改动")
            if len(value) != len(ref):
                reasons.append("长度变化")
            if balanced(ref) and not balanced(value):
                reasons.append("括号失衡")
            if PLACEHOLDER.findall(value) != PLACEHOLDER.findall(ref):
                reasons.append("格式占位符不一致")
            if reasons:
                bad.append({"key": key, "cn": ref, "variant": value, "why": "、".join(reasons)})
        if bad:
            for row in bad[:8]:
                print(f"  [{code}] {row['why']}: {row['cn']!r} -> {row['variant']!r}")
            raise SystemExit(f"{code}: {len(bad)} 条未通过守卫")

        bin_path = variant_dir / "translations.bin"
        size = write_bin(entries, bin_path)
        if code == "zh-CN" and bin_path.read_bytes() != cn_bin.read_bytes():
            raise SystemExit("zh-CN 重新打包的 .bin 与 build_maps.py 产物不一致（格式漂移）")

        if code == "zh-CN":
            files, overlay_chars = [], 0
            overlay_text = ""
            for path in sorted((PAYLOAD / "overlay").rglob("*")):
                if path.is_file() and path.suffix.lower() in (".txt", ".csv"):
                    overlay_text += path.read_text(encoding="utf-8-sig")
            font_source = PAYLOAD / "overlay" / "Dat" / "Fonts" / "WitE2CN.ttf"
            existing = TTFont(font_source)
            cmap = existing.getBestCmap()
            existing.close()
            chars = font_chars(entries, overlay_text)
            absent = "".join(c for c in chars if ord(c) not in cmap)
            font_info = {"base": "msyh.ttc（沿用 build_maps 产物）", "bytes": font_source.stat().st_size,
                         "glyphs": len(cmap), "requested": len(chars), "filled_from_fallbacks": 0,
                         "absent": absent}
        else:
            files, overlay_chars = convert_overlay(code)
            overlay_text = "".join((variant_dir / "overlay" / rel).read_text(encoding="utf-8-sig")
                                   for rel in files)
            chars = font_chars(entries, overlay_text)
            font_info = subset_font(base_font, chars,
                                    variant_dir / "overlay" / "Dat" / "Fonts" / "WitE2CN.ttf")
        if font_info["absent"]:
            raise SystemExit(f"{code}: 字体仍缺字 {font_info['absent']!r}")

        audit["variants"].append({
            "code": code, "label": label, "converter": cfg or "none",
            "entries": len(entries), "changed_values": changed, "polished_values": polished,
            "bin_bytes": size,
            "overlay_files": files, "overlay_chars": overlay_chars,
            "font": font_info, "guards": "pass",
        })
        print(f"{code:6s} {label}: {len(entries)} 条，改动 {changed} 条（修正层 {polished} 条），"
              f"{size / 1024 / 1024:.1f} MB；字体 {font_info['glyphs']} 字 / "
              f"{font_info['bytes'] / 1024:.0f} KB，缺字 0")

    # 活动槽 payload\translations.bin 由启动器按选择物化，不随包发布（否则切换语言后校验会失败）
    if cn_bin.exists():
        cn_bin.unlink()
        print("已移除活动槽 payload\\translations.bin（由启动器按语言包物化）")

    (PROJECT / "audit").mkdir(exist_ok=True)
    (PROJECT / "audit" / "variants.audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf8")
    print("审计写入 audit\\variants.audit.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
