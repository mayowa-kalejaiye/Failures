import os
import sys
import re
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent

html_files = [f for f in BASE_DIR.rglob("*.html") if not f.name.endswith("_exact.html")]
print(f"Auditing {len(html_files)} HTML files in website/ ...\n")

errors = []
warnings = []

for html_file in html_files:
    content = html_file.read_text(encoding="utf-8")
    rel_path = html_file.relative_to(BASE_DIR)
    
    # 1. Check size
    if len(content) < 500:
        errors.append(f"{rel_path}: File is suspiciously small ({len(content)} bytes)")

    # 2. Check title
    if "<title>" not in content or "</title>" not in content:
        errors.append(f"{rel_path}: Missing <title> tag")

    # 3. Check CSS linkage
    css_matches = re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', content)
    for css in css_matches:
        if css.startswith("http://") or css.startswith("https://"):
            continue
        target_css = (html_file.parent / css).resolve()
        if not target_css.exists():
            errors.append(f"{rel_path}: Broken CSS link -> {css}")

    # 4. Check JS linkage
    js_matches = re.findall(r'<script[^>]+src="([^"]+)"', content)
    for js in js_matches:
        if js.startswith("http://") or js.startswith("https://"):
            continue
        target_js = (html_file.parent / js).resolve()
        if not target_js.exists():
            errors.append(f"{rel_path}: Broken JS link -> {js}")

    # 5. Check local relative links (href="...")
    href_matches = re.findall(r'href="([^"#:]+)(?:#([^"]*))?"', content)
    for href, anchor in href_matches:
        if href.startswith("http") or href.startswith("mailto") or href.startswith("javascript"):
            continue
        target_file = (html_file.parent / href).resolve()
        if not target_file.exists():
            errors.append(f"{rel_path}: Broken link -> href='{href}' (resolved to {target_file})")

print("Audit Results:")
if not errors and not warnings:
    print(f"✅ PERFECT AUDIT SCORE: All {len(html_files)} pages passed link integrity and asset validation!")
else:
    for e in errors:
        print(f"❌ ERROR: {e}")
    for w in warnings:
        print(f"⚠️ WARNING: {w}")
