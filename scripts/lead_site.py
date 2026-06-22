#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scaffold, verify, commit, and deploy approved restaurant lead sites.

Repo layout:
  <industry>/<region>/<lead-slug>/
    lead.json
    proposal.md
    code/index.html
    code/vercel.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import html.parser
import json
import os
import re
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from restaurant_preview import (
    build_asset_manifest,
    render_site_html,
    run_playwright_visual_qa,
    write_asset_plan,
    write_static_qa,
)

ROOT = Path(__file__).resolve().parents[1]
PAGES_BASE_URL = os.getenv("RESTAURANT_LEAD_SITES_BASE_URL", "https://hiroyuki0504.github.io/restaurant-lead-sites/")


def run(cmd: list[str], cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(cmd, cwd=str(cwd or ROOT), text=True, capture_output=True, timeout=300)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{res.stderr or res.stdout}")
    return res


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if text:
        return text[:80]
    return "lead-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def safe_part(text: str, kind: str = "part") -> str:
    """Return an ASCII directory name that GitHub Pages serves reliably.

    Keep the original Japanese industry/region in lead.json and proposal.md;
    use ASCII slugs for the filesystem/public URL.
    """
    raw = (text or "uncategorized").strip().replace("/", "-").replace(":", "-")
    known = {
        "飲食店": "restaurant",
        "レストラン": "restaurant",
        "飲食": "restaurant",
        "_demo": "demo",
    }
    if raw in known:
        return known[raw]
    slug = slugify(raw)
    if slug:
        return slug
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"{kind}-{digest}"


def lead_dir(industry: str, region: str, slug: str, industry_slug: str | None = None, region_slug: str | None = None) -> Path:
    return ROOT / safe_part(industry_slug or industry, "industry") / safe_part(region_slug or region, "region") / safe_part(slug, "lead")



def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def escape_attr(s: str) -> str:
    return escape_html(s).replace("'", "&#x27;")


def html_template(name: str, industry: str, region: str, gaps: list[str], angles: list[str], source_urls: list[str]) -> str:
    """High-quality customer-facing restaurant site preview.

    Keep consulting/proposal rationale in proposal.md and email drafts; the public URL should
    look like a polished restaurant site the prospect can imagine owning.
    """
    del gaps, source_urls  # internal-only; do not show weaknesses or citations on the public site
    angle_text = " / ".join(angles[:3]) if angles else "Web site / Reservation / LINE"
    return f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{escape_html(name)} | {escape_html(region)}のレストラン</title>
  <meta name=\"description\" content=\"{escape_attr(name)}の料理、空間、予約導線をスマホで見やすくまとめた店舗ページ。\" />
  <meta name=\"robots\" content=\"noindex\" />
  <style>
    :root {{ color-scheme: light; --ink:#18120d; --muted:#706258; --cream:#fbf4e8; --paper:#fffaf2; --deep:#24170f; --gold:#b98745; --accent:#c85f36; --line:rgba(74,49,29,.16); --shadow:0 24px 70px rgba(45,29,15,.16); }}
    * {{ box-sizing: border-box; }} html {{ scroll-behavior:smooth; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Hiragino Mincho ProN','Yu Mincho','Noto Serif JP',serif; color:var(--ink); background:var(--cream); }}
    .sans {{ font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans','Noto Sans JP',system-ui,sans-serif; }}
    .nav {{ position:fixed; inset:18px 22px auto; z-index:20; left:50%; transform:translateX(-50%); width:calc(100% - 44px); max-width:1180px; display:flex; justify-content:space-between; align-items:center; gap:16px; padding:12px 14px 12px 18px; border:1px solid rgba(255,255,255,.32); border-radius:999px; background:rgba(36,23,15,.58); color:white; backdrop-filter:blur(18px); box-shadow:0 12px 45px rgba(0,0,0,.16); }}
    .brand {{ letter-spacing:.14em; font-weight:800; text-decoration:none; }} .nav-links {{ display:flex; gap:8px; align-items:center; }} .nav-links a {{ color:rgba(255,255,255,.84); text-decoration:none; padding:9px 12px; border-radius:999px; font-size:.9rem; }} .nav-links .cta {{ background:white; color:var(--deep); font-weight:800; }}
    .hero {{ min-height:100vh; display:grid; place-items:center; position:relative; overflow:hidden; padding:130px 22px 70px; color:white; background:linear-gradient(120deg,rgba(16,12,8,.9),rgba(36,23,15,.58) 44%,rgba(247,229,204,.2)),radial-gradient(circle at 72% 26%,rgba(244,173,83,.42),transparent 32%),radial-gradient(circle at 21% 70%,rgba(71,110,80,.34),transparent 36%),linear-gradient(135deg,#2b1b10,#6f3d25 45%,#f4d7b3); }}
    .hero::before {{ content:\"\"; position:absolute; inset:0; opacity:.22; background-image:linear-gradient(45deg,rgba(255,255,255,.12) 25%,transparent 25%),linear-gradient(-45deg,rgba(255,255,255,.1) 25%,transparent 25%); background-size:48px 48px; mix-blend-mode:screen; }}
    .hero-inner {{ position:relative; z-index:1; width:min(1180px,100%); display:grid; grid-template-columns:1.08fr .92fr; align-items:center; gap:42px; }}
    .eyebrow {{ display:inline-flex; padding:8px 12px; border:1px solid rgba(255,255,255,.24); border-radius:999px; background:rgba(255,255,255,.09); color:rgba(255,255,255,.88); letter-spacing:.18em; font-size:.78rem; }}
    h1 {{ margin:22px 0 18px; font-size:clamp(3rem,8.4vw,8.7rem); line-height:.92; letter-spacing:-.08em; font-weight:800; text-wrap:balance; }}
    .hero-copy {{ max-width:680px; color:rgba(255,255,255,.86); font-size:clamp(1rem,1.65vw,1.28rem); line-height:2.05; }}
    .cta-row {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:30px; }}
    .button {{ display:inline-flex; align-items:center; gap:10px; padding:14px 19px; border-radius:999px; text-decoration:none; font-weight:800; border:1px solid rgba(255,255,255,.26); }} .button.primary {{ background:white; color:var(--deep); box-shadow:0 20px 45px rgba(0,0,0,.22); }} .button.ghost {{ color:white; background:rgba(255,255,255,.08); }}
    .hero-card {{ position:relative; min-height:520px; border:1px solid rgba(255,255,255,.28); border-radius:38px; overflow:hidden; background:radial-gradient(circle at 50% 16%,rgba(255,255,255,.9),rgba(255,245,228,.12) 18%,transparent 26%),radial-gradient(circle at 28% 46%,rgba(255,170,80,.52),transparent 19%),radial-gradient(circle at 68% 64%,rgba(62,94,68,.64),transparent 27%),linear-gradient(150deg,rgba(255,255,255,.32),rgba(255,255,255,.06)); box-shadow:0 34px 90px rgba(0,0,0,.28); }}
    .hero-card::after {{ content:\"季節の料理\\A 予約導線\\A 上質な体験\"; white-space:pre-line; position:absolute; inset:auto 26px 24px; color:white; font-size:clamp(2rem,5vw,4.8rem); line-height:1.06; letter-spacing:-.06em; font-weight:800; text-shadow:0 12px 42px rgba(0,0,0,.38); }}
    .float-note {{ position:absolute; top:22px; right:22px; width:min(280px,calc(100% - 44px)); padding:18px; border-radius:24px; background:rgba(255,250,242,.9); color:var(--deep); box-shadow:var(--shadow); }} .float-note span {{ display:block; color:var(--muted); line-height:1.7; font-size:.92rem; }}
    section {{ padding:92px 22px; }} .wrap {{ width:min(1180px,100%); margin:0 auto; }}
    .section-head {{ display:grid; grid-template-columns:.72fr 1fr; gap:40px; align-items:end; margin-bottom:34px; }} .kicker {{ color:var(--accent); letter-spacing:.16em; font-weight:900; font-size:.78rem; }} h2 {{ margin:8px 0 0; font-size:clamp(2.1rem,4.8vw,5rem); line-height:.98; letter-spacing:-.07em; }} .section-head p {{ margin:0; color:var(--muted); line-height:2; font-size:1.04rem; }}
    .cards {{ display:grid; grid-template-columns:repeat(3,1fr); gap:18px; }} .card {{ min-height:280px; padding:26px; border-radius:30px; background:var(--paper); border:1px solid var(--line); box-shadow:0 16px 45px rgba(45,29,15,.07); }} .card h3 {{ margin:0 0 12px; font-size:1.45rem; letter-spacing:-.03em; }} .card p,.card li {{ color:var(--muted); line-height:1.9; }}
    .feature {{ grid-column:span 2; background:linear-gradient(135deg,#fffaf2,#f3dfc3); }}
    .visual-strip {{ display:grid; grid-template-columns:1.2fr .8fr; gap:18px; margin-top:18px; }} .visual {{ min-height:360px; border-radius:34px; border:1px solid var(--line); background:radial-gradient(circle at 23% 28%,rgba(255,240,205,.95),transparent 19%),radial-gradient(circle at 66% 42%,rgba(195,91,53,.72),transparent 20%),radial-gradient(circle at 47% 72%,rgba(42,77,52,.7),transparent 24%),linear-gradient(135deg,#2a1a12,#7a4328 54%,#e6bd81); box-shadow:var(--shadow); position:relative; }} .visual::after {{ content:\"{escape_html(region)} TABLE\"; position:absolute; left:24px; bottom:22px; color:rgba(255,255,255,.86); font-weight:900; letter-spacing:.16em; font-size:.82rem; }}
    .menu-item {{ display:flex; justify-content:space-between; gap:20px; padding:18px 0; border-bottom:1px solid var(--line); }} .menu-item span {{ color:var(--muted); line-height:1.7; }}
    .reservation {{ background:var(--deep); color:white; position:relative; overflow:hidden; }} .reservation::before {{ content:\"\"; position:absolute; inset:-20% -10% auto auto; width:520px; height:520px; background:radial-gradient(circle,rgba(197,137,71,.45),transparent 67%); }} .reserve-box {{ position:relative; display:grid; grid-template-columns:.85fr 1.15fr; gap:26px; }} .reserve-panel,.step {{ border:1px solid rgba(255,255,255,.12); background:rgba(255,255,255,.08); }} .reserve-panel {{ padding:30px; border-radius:34px; backdrop-filter:blur(10px); }} .steps {{ display:grid; gap:14px; }} .step {{ display:grid; grid-template-columns:42px 1fr; gap:14px; padding:18px; border-radius:22px; }} .num {{ display:grid; place-items:center; width:42px; height:42px; border-radius:50%; background:var(--gold); color:var(--deep); font-weight:900; }} .step span,.reserve-panel p {{ color:rgba(255,255,255,.74); line-height:1.8; }}
    footer {{ padding:34px 22px; background:#120d09; color:rgba(255,255,255,.66); font-size:.86rem; }} footer .wrap {{ display:flex; justify-content:space-between; gap:18px; flex-wrap:wrap; }} .demo-note {{ opacity:.62; }}
    @media (max-width:860px) {{ .nav {{ inset:12px 12px auto; width:calc(100% - 24px); }} .nav-links a:not(.cta) {{ display:none; }} .hero {{ padding-top:112px; }} .hero-inner,.section-head,.reserve-box,.visual-strip {{ grid-template-columns:1fr; }} .hero-card {{ min-height:380px; }} .cards {{ grid-template-columns:1fr; }} .feature {{ grid-column:span 1; }} section {{ padding:70px 18px; }} }}
  </style>
</head>
<body>
  <nav class=\"nav sans\"><a class=\"brand\" href=\"#top\">{escape_html(name)}</a><div class=\"nav-links\"><a href=\"#story\">こだわり</a><a href=\"#menu\">お料理</a><a href=\"#reserve\">ご予約</a><a class=\"cta\" href=\"#reserve\">予約相談</a></div></nav>
  <main id=\"top\">
    <section class=\"hero\"><div class=\"hero-inner\"><div><div class=\"eyebrow sans\">{escape_html(industry)} / {escape_html(region)}</div><h1>土地の味を、<br>美しい体験へ。</h1><p class=\"hero-copy sans\">{escape_html(name)}の魅力を、初めて訪れる方にも伝わる1ページへ。料理・雰囲気・予約まで、スマホで迷わず進める構成です。</p><div class=\"cta-row sans\"><a class=\"button primary\" href=\"#reserve\">ご予約の流れを見る</a><a class=\"button ghost\" href=\"#menu\">お料理を見る</a></div></div><div class=\"hero-card\"><div class=\"float-note sans\"><strong>予約前に伝わる情報</strong><span>{escape_html(angle_text)} を自然に体験へつなげます。</span></div></div></div></section>
    <section id=\"story\"><div class=\"wrap\"><div class=\"section-head\"><div><div class=\"kicker sans\">STORY</div><h2>お店らしさを、<br>一目で伝える。</h2></div><p class=\"sans\">料理の魅力、空間の雰囲気、予約導線をひとつの体験として整理。初めて訪れる方にも、お店の世界観が自然に伝わる構成です。</p></div><div class=\"cards\"><article class=\"card feature\"><h3>料理と体験を主役に。</h3><p class=\"sans\">ファーストビューで世界観を作り、予約前の期待値を高めます。写真が入る前でも、色・余白・言葉で上質感を出せる設計です。</p></article><article class=\"card\"><h3>スマホ最優先。</h3><p class=\"sans\">観光中・移動中でも見やすく、予約導線まで短く進める構成。</p></article><article class=\"card\"><h3>予約に迷わない。</h3><p class=\"sans\">電話、フォーム、LINEなど任意の導線を整理して、来店までの不安を減らします。</p></article><article class=\"card\"><h3>再訪につなげる。</h3><p class=\"sans\">季節メニューやお知らせ導線を作り、1回来店で終わらない関係を作ります。</p></article></div></div></section>
    <section id=\"menu\" style=\"background:#fffaf2\"><div class=\"wrap\"><div class=\"section-head\"><div><div class=\"kicker sans\">MENU</div><h2>魅力が伝わる、<br>料理紹介。</h2></div><p class=\"sans\">実際の献立・価格・写真が揃えば差し替え可能な、完成度重視のセクションです。</p></div><div class=\"visual-strip\"><div class=\"visual\"></div><div class=\"card\"><h3>見せ方の軸</h3><div class=\"sans\"><div class=\"menu-item\"><strong>名物</strong><span>最初に食べてほしい一皿を大きく見せる。</span></div><div class=\"menu-item\"><strong>コース</strong><span>予約前に分かる範囲で流れを説明。</span></div><div class=\"menu-item\"><strong>季節感</strong><span>旬・限定・地元食材の価値を演出。</span></div></div></div></div></div></section>
    <section id=\"reserve\" class=\"reservation\"><div class=\"wrap reserve-box\"><div class=\"reserve-panel\"><div class=\"kicker sans\">RESERVATION</div><h2>予約まで、<br>迷わせない。</h2><p class=\"sans\">お店に合わせて予約・問い合わせ・LINE導線を整理。人数、希望日、要望まで自然に伝えられる流れを用意します。</p><div class=\"cta-row sans\"><a class=\"button primary\" href=\"#\">予約相談する</a><a class=\"button ghost\" href=\"#top\">ページ上部へ</a></div></div><div class=\"steps sans\"><div class=\"step\"><div class=\"num\">1</div><div><strong>希望日を選ぶ</strong><span>来店前に必要な情報を簡単に伝えられる。</span></div></div><div class=\"step\"><div class=\"num\">2</div><div><strong>人数・要望を共有</strong><span>コース、席、アレルギーなども事前確認。</span></div></div><div class=\"step\"><div class=\"num\">3</div><div><strong>来店後もつながる</strong><span>LINEやお知らせで再来店導線を作る。</span></div></div></div></div></section>
  </main>
  <footer class=\"sans\"><div class=\"wrap\"><span>© {escape_html(name)}</span><span class=\"demo-note\">料理・空間・予約情報をまとめた店舗ページ。</span></div></footer>
</body>
</html>
"""


class Parser(html.parser.HTMLParser):
    pass


def verify_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    Parser().feed(text)
    for needle in ["<!doctype html>", "<html", "</html>", "<meta name=\"viewport\""]:
        if needle.lower() not in text.lower():
            raise RuntimeError(f"HTML verification failed: missing {needle}")


def generate_index() -> Path:
    """Generate a GitHub Pages-friendly top page listing all lead sites."""
    cards: list[str] = []
    for meta_path in sorted(ROOT.glob("*/*/*/lead.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        code_index = meta_path.parent / "code" / "index.html"
        if not code_index.exists():
            continue
        rel = code_index.relative_to(ROOT).as_posix()
        href = quote(rel, safe="/._-~")
        industry = meta.get("industry", meta_path.parts[-4] if len(meta_path.parts) >= 4 else "")
        region = meta.get("region", meta_path.parts[-3] if len(meta_path.parts) >= 3 else "")
        name = meta.get("name", meta_path.parent.name)
        angles = " / ".join(meta.get("proposal_angles") or [])
        deploy = meta.get("deployment") or {}
        deploy_url = deploy.get("url") if isinstance(deploy, dict) else None
        deploy_link = f'<a class="deploy" href="{escape_attr(deploy_url)}">公開URL</a>' if deploy_url else ""
        cards.append(f"""
        <article class=\"card\">
          <div class=\"meta\">{escape_html(str(industry))} / {escape_html(str(region))}</div>
          <h2>{escape_html(str(name))}</h2>
          <p>{escape_html(angles or 'サンプルサイト')}</p>
          <a href=\"{href}\">サイトを見る</a>{deploy_link}
        </article>""")
    cards_html = "\n".join(cards) or "<p>まだサイトがありません。</p>"
    html = f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Restaurant Lead Sites</title>
  <style>
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans','Noto Sans JP',system-ui,sans-serif; background:#0f172a; color:#e5e7eb; }}
    header {{ padding:56px 24px 28px; max-width:1120px; margin:auto; }}
    h1 {{ margin:0; font-size:clamp(2.2rem,7vw,4.8rem); letter-spacing:-.06em; }}
    .lead {{ color:#a7b0c0; font-size:1.1rem; line-height:1.8; max-width:760px; }}
    main {{ max-width:1120px; margin:auto; padding:20px 24px 72px; display:grid; grid-template-columns:repeat(auto-fit,minmax(270px,1fr)); gap:18px; }}
    .card {{ background:linear-gradient(180deg,#182239,#111827); border:1px solid rgba(255,255,255,.1); border-radius:24px; padding:22px; box-shadow:0 18px 55px rgba(0,0,0,.25); }}
    .meta {{ color:#fb923c; font-weight:800; font-size:.86rem; }}
    h2 {{ margin:.35em 0; font-size:1.35rem; }}
    p {{ color:#cbd5e1; line-height:1.7; }}
    a {{ display:inline-block; color:#0f172a; background:#f8fafc; text-decoration:none; font-weight:800; padding:10px 14px; border-radius:999px; margin:8px 8px 0 0; }}
    .deploy {{ background:#f97316; color:white; }}
  </style>
</head>
<body>
  <header>
    <h1>Restaurant Lead Sites</h1>
    <p class=\"lead\">承認された飲食店リード向けの提案用サンプルサイトを、業種 / 地域 / 店舗ごとに一括管理しています。</p>
  </header>
  <main>
    {cards_html}
  </main>
</body>
</html>
"""
    out = ROOT / "index.html"
    out.write_text(html, encoding="utf-8")
    verify_html(out)
    return out


def cmd_check(_: argparse.Namespace) -> int:
    checks: dict[str, Any] = {"repo_root": str(ROOT), "git": False, "vercel_cli": False, "vercel_authenticated": False}
    checks["git"] = run(["git", "--version"]).returncode == 0
    checks["vercel_cli"] = run(["bash", "-lc", "command -v vercel >/dev/null || npx --yes vercel@latest --version >/dev/null"], cwd=ROOT).returncode == 0
    who = run(["bash", "-lc", "(command -v vercel >/dev/null && vercel whoami) || npx --yes vercel@latest whoami"], cwd=ROOT)
    checks["vercel_authenticated"] = who.returncode == 0
    if who.returncode == 0:
        checks["vercel_user"] = who.stdout.strip().splitlines()[-1]
    else:
        checks["vercel_auth_note"] = "Run `npx vercel login` once, or provide VERCEL_TOKEN outside Hermes secrets output."
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    slug = args.slug or slugify(args.name)
    base = lead_dir(args.industry, args.region, slug, args.industry_slug, args.region_slug)
    code = base / "code"
    code.mkdir(parents=True, exist_ok=True)
    gaps = args.gap or []
    angles = args.angle or []
    urls = args.source_url or []
    asset_manifest = build_asset_manifest(
        args.name,
        photo_urls=args.photo_url or [],
        photo_alts=args.photo_alt or [],
        photo_rights=args.photo_rights or [],
        source_urls=urls,
    )
    (code / "assets").mkdir(exist_ok=True)
    (code / "assets" / "asset-manifest.json").write_text(
        json.dumps(asset_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_asset_plan(base / "asset-plan.md", args.name, asset_manifest)
    (code / "index.html").write_text(
        render_site_html(
            name=args.name,
            industry=args.industry,
            region=args.region,
            angles=angles,
            asset_manifest=asset_manifest,
            palette=args.palette,
        ),
        encoding="utf-8",
    )
    (code / "vercel.json").write_text(json.dumps({"cleanUrls": True, "trailingSlash": False}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public_path = quote((code / "index.html").relative_to(ROOT).as_posix(), safe="/._-~")
    metadata = {
        "name": args.name,
        "industry": args.industry,
        "region": args.region,
        "slug": slug,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_urls": urls,
        "gaps": gaps,
        "proposal_angles": angles,
        "asset_policy": asset_manifest["policy"],
        "asset_status": asset_manifest["status"],
        "code_dir": str(code),
        "deployment": {
            "provider": "github_pages",
            "url": PAGES_BASE_URL.rstrip("/") + "/" + public_path,
            "source": "main:/",
        },
    }
    (base / "lead.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    proposal = [
        f"# {args.name} 提案ブリーフ",
        "",
        f"- 業種: {args.industry}",
        f"- 地域: {args.region}",
        f"- コード: `{code}`",
        "",
        "## 改善余地",
        *(f"- {g}" for g in gaps),
        "",
        "## 最初に作る提案物",
        *(f"- {a}" for a in angles),
        "",
        "## 根拠URL",
        *(f"- {u}" for u in urls),
        "",
        "## 写真取得・権利方針",
        f"- 状態: `{asset_manifest['status']}`",
        "- 料理写真を主役にする。CSSの偽料理・偽ラーメンは使わない。",
        "- 公開HTMLに入れるのは、店舗提供・自前撮影・商用ライセンス・明示許可済み素材だけ。",
        "- Google Business / 食べログ / Hot Pepper / SNS 等の第三者画像は無断コピーしない。",
        "- 詳細: `asset-plan.md` / `code/assets/asset-manifest.json`",
        "",
        "## 安全メモ",
        "- これは営業提案用の非公式サンプルであり、店舗公式サイトではありません。",
        "- 外部送信は最終承認後のみ。",
    ]
    (base / "proposal.md").write_text("\n".join(proposal) + "\n", encoding="utf-8")
    verify_html(code / "index.html")
    qa_result = write_static_qa(code, asset_manifest)
    if not qa_result["ok"]:
        raise RuntimeError(f"static visual QA failed: {qa_result}")
    if args.visual_qa:
        run_playwright_visual_qa(code)
    generate_index()
    if args.git_commit:
        ensure_git_repo()
        git_commit(f"feat: add lead site {args.industry}/{args.region}/{slug}")
    print(json.dumps({"success": True, "lead_dir": str(base), "code_dir": str(code), "index_html": str(code / "index.html"), "slug": slug}, ensure_ascii=False, indent=2))
    return 0


def ensure_git_repo() -> None:
    if not (ROOT / ".git").exists():
        run(["git", "init", "-b", "main"], cwd=ROOT, check=True)


def git_commit(message: str) -> None:
    run(["git", "add", "."], cwd=ROOT, check=True)
    diff = run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if diff.returncode == 0:
        return
    run(["git", "commit", "-m", message], cwd=ROOT, check=True)


def cmd_commit(args: argparse.Namespace) -> int:
    ensure_git_repo()
    git_commit(args.message)
    print(json.dumps({"success": True, "git_status": run(["git", "status", "--short"], cwd=ROOT).stdout}, ensure_ascii=False, indent=2))
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    out = generate_index()
    if args.git_commit:
        ensure_git_repo()
        git_commit(args.message)
    print(json.dumps({"success": True, "index_html": str(out)}, ensure_ascii=False, indent=2))
    return 0


def cmd_visual_qa(args: argparse.Namespace) -> int:
    code = Path(args.code_dir)
    if not code.is_absolute():
        code = ROOT / code
    manifest_path = code / "assets" / "asset-manifest.json"
    if not (code / "index.html").exists():
        print(json.dumps({"success": False, "error": f"No index.html at {code}"}, ensure_ascii=False), file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"status": "unknown", "selected_photos": []}
    static = write_static_qa(code, manifest)
    result: dict[str, Any] = {"success": static["ok"], "static": static}
    if args.screenshots:
        result["playwright"] = run_playwright_visual_qa(code)
        result["success"] = bool(result["success"] and result["playwright"].get("ok"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] else 1


def update_deployment(industry: str, region: str, slug: str, provider: str, url: str) -> None:
    meta_path = lead_dir(industry, region, slug) / "lead.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["deployment"] = {"provider": provider, "url": url, "deployed_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_deploy_vercel(args: argparse.Namespace) -> int:
    slug = args.slug or slugify(args.name or "")
    code = lead_dir(args.industry, args.region, slug) / "code"
    if not (code / "index.html").exists():
        print(json.dumps({"success": False, "error": f"No index.html at {code}"}, ensure_ascii=False), file=sys.stderr)
        return 2
    who = run(["bash", "-lc", "(command -v vercel >/dev/null && vercel whoami) || npx --yes vercel@latest whoami"], cwd=ROOT)
    if who.returncode != 0:
        print(json.dumps({"success": False, "error": "Vercel CLI is not authenticated", "next_step": "Run `npx vercel login` once, then rerun deploy-vercel."}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 3
    cmd = "vercel" if run(["bash", "-lc", "command -v vercel >/dev/null"], cwd=ROOT).returncode == 0 else "npx --yes vercel@latest"
    deploy = run(["bash", "-lc", f"{cmd} --yes {'--prod' if args.prod else ''}"], cwd=code)
    if deploy.returncode != 0:
        print(json.dumps({"success": False, "error": deploy.stderr or deploy.stdout}, ensure_ascii=False), file=sys.stderr)
        return deploy.returncode or 1
    lines = [ln.strip() for ln in deploy.stdout.splitlines() if ln.strip().startswith("https://")]
    url = lines[-1] if lines else deploy.stdout.strip().splitlines()[-1]
    update_deployment(args.industry, args.region, slug, "vercel", url)
    git_commit(f"chore: record Vercel deploy for {slug}")
    print(json.dumps({"success": True, "provider": "vercel", "url": url, "code_dir": str(code)}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("scaffold")
    p.add_argument("--industry", default="飲食店")
    p.add_argument("--industry-slug", help="ASCII public path segment; original industry is kept in lead.json")
    p.add_argument("--region", required=True)
    p.add_argument("--region-slug", help="ASCII public path segment; original region is kept in lead.json")
    p.add_argument("--name", required=True)
    p.add_argument("--slug")
    p.add_argument("--gap", action="append", default=[])
    p.add_argument("--angle", action="append", default=[])
    p.add_argument("--source-url", action="append", default=[])
    p.add_argument("--photo-url", action="append", default=[], help="approved/local/licensed photo URL or path; paired with --photo-rights")
    p.add_argument("--photo-alt", action="append", default=[])
    p.add_argument("--photo-rights", action="append", default=[], help="must be approved/shop-approved/owned/licensed to render in public HTML")
    p.add_argument("--palette", default="niboshi", choices=["niboshi", "miso", "warm"])
    p.add_argument("--visual-qa", action="store_true", help="also run Playwright screenshots for responsive QA")
    p.add_argument("--git-commit", action="store_true")
    p.set_defaults(func=cmd_scaffold)
    p = sub.add_parser("commit")
    p.add_argument("--message", default="chore: update lead sites")
    p.set_defaults(func=cmd_commit)
    p = sub.add_parser("index")
    p.add_argument("--git-commit", action="store_true")
    p.add_argument("--message", default="chore: update lead site index")
    p.set_defaults(func=cmd_index)
    p = sub.add_parser("visual-qa")
    p.add_argument("code_dir", help="lead code directory, e.g. restaurant/.../code")
    p.add_argument("--screenshots", action="store_true", help="capture Playwright screenshots at standard viewports")
    p.set_defaults(func=cmd_visual_qa)
    p = sub.add_parser("deploy-vercel")
    p.add_argument("--industry", default="飲食店")
    p.add_argument("--region", required=True)
    p.add_argument("--slug")
    p.add_argument("--name")
    p.add_argument("--prod", action="store_true")
    p.set_defaults(func=cmd_deploy_vercel)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
