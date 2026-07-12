# -*- coding: utf-8 -*-
"""LPの多言語辞書を検証する。文言変更のあとに必ず実行する。

使い方:  python3 tools/check_i18n.py
検査対象: index.html / index-editorial.html
チェック内容:
  1. I18N 辞書が en/ja/ko/es/fr の5言語そろっているか
  2. 5言語のキー集合が完全に一致しているか（訳し漏れ検出）
  3. HTML側の data-i18n / data-i18n-ph キーが辞書に存在するか
  4. 文字化け（U+FFFD・???・{EM}）が混入していないか
全て通れば OK、問題があれば内容を表示して exit 1。
"""
import re, sys, os

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["index.html", "index-editorial.html"]
LANGS = ["en", "ja", "ko", "es", "fr"]

def parse_i18n(src):
    m = re.search(r'const I18N = \{(.*)\n\};', src, re.S)
    if not m:
        return None
    parts = re.split(r'\n  ([a-z]{2}):\{', m.group(1))
    langs = {}
    for i in range(1, len(parts), 2):
        pairs = re.findall(
            r'([A-Za-z_][A-Za-z0-9_]*):("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
            parts[i + 1])
        langs[parts[i]] = {k: v for k, v in pairs}
    return langs

ok = True
for f in FILES:
    path = os.path.join(PROJ, f)
    src = open(path, encoding="utf-8").read()
    errs = []

    for bad, label in [("�", "U+FFFD文字化け"), ("???", "???文字化け"), ("{EM}", "{EM}プレースホルダ")]:
        n = src.count(bad)
        if n:
            errs.append(f"{label} が {n} 箇所")

    d = parse_i18n(src)
    if d is None:
        errs.append("I18N 辞書が見つからない")
    else:
        missing_langs = [l for l in LANGS if l not in d]
        if missing_langs:
            errs.append(f"言語が不足: {missing_langs}")
        base = set(d.get("en", {}))
        for l in LANGS:
            if l in d and l != "en":
                miss = base - set(d[l])
                extra = set(d[l]) - base
                if miss:
                    errs.append(f"{l} に訳し漏れ {len(miss)}件: {sorted(miss)[:8]}")
                if extra:
                    errs.append(f"{l} に余分なキー {len(extra)}件: {sorted(extra)[:8]}")
        html_keys = set(re.findall(r'data-i18n(?:-ph)?="([^"]+)"', src))
        orphan = html_keys - base
        if orphan:
            errs.append(f"HTML側キーが辞書にない: {sorted(orphan)}")

    if errs:
        ok = False
        print(f"NG {f}")
        for e in errs:
            print(f"   - {e}")
    else:
        n = len(d["en"]) if d else 0
        print(f"OK {f}  ({n}キー x {len(LANGS)}言語)")

sys.exit(0 if ok else 1)
