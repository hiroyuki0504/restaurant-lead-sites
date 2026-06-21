#!/usr/bin/env python3
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


def lead_dir(industry: str, region: str, slug: str) -> Path:
    return ROOT / safe_part(industry, "industry") / safe_part(region, "region") / safe_part(slug, "lead")


def html_template(name: str, industry: str, region: str, gaps: list[str], angles: list[str], source_urls: list[str]) -> str:
    gap_items = "\n".join(f"<li>{escape_html(g)}</li>" for g in gaps) or "<li>予約・問い合わせ導線の改善余地</li>"
    angle_items = "\n".join(f"<li>{escape_html(a)}</li>" for a in angles) or "<li>モバイル優先の1枚LP</li>"
    source_links = "\n".join(f'<li><a href="{escape_attr(u)}">{escape_html(u)}</a></li>' for u in source_urls) or "<li>公開URL未設定</li>"
    return f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{escape_html(name)} 改善サンプルLP</title>
  <meta name=\"robots\" content=\"noindex\" />
  <style>
    :root {{ color-scheme: light; --ink:#172033; --muted:#5f6b7a; --brand:#d45b35; --soft:#fff4ed; --line:#ead8ca; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans','Noto Sans JP',system-ui,sans-serif; color:var(--ink); background:#fffaf6; }}
    .hero {{ min-height:72vh; display:grid; place-items:center; padding:48px 20px; background:radial-gradient(circle at top left,#fff 0,#fff4ed 44%,#f7dac8 100%); }}
    .wrap {{ width:min(1080px,100%); }}
    .eyebrow {{ color:var(--brand); font-weight:800; letter-spacing:.12em; font-size:.86rem; }}
    h1 {{ font-size:clamp(2.1rem,7vw,5.2rem); line-height:1.02; margin:.18em 0; letter-spacing:-.06em; }}
    .lead {{ max-width:720px; font-size:clamp(1.05rem,2vw,1.35rem); line-height:1.9; color:var(--muted); }}
    .cta-row {{ display:flex; flex-wrap:wrap; gap:14px; margin-top:30px; }}
    .btn {{ display:inline-block; padding:14px 22px; border-radius:999px; text-decoration:none; font-weight:800; }}
    .btn.primary {{ color:white; background:var(--brand); box-shadow:0 12px 28px rgba(212,91,53,.25); }}
    .btn.secondary {{ color:var(--brand); background:#fff; border:1px solid var(--line); }}
    section {{ padding:64px 20px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:18px; }}
    .card {{ background:#fff; border:1px solid var(--line); border-radius:24px; padding:24px; box-shadow:0 18px 45px rgba(32,24,18,.06); }}
    h2 {{ font-size:clamp(1.5rem,3vw,2.4rem); margin:0 0 18px; letter-spacing:-.04em; }}
    li {{ margin:.55em 0; line-height:1.7; }}
    .note {{ color:var(--muted); font-size:.92rem; line-height:1.8; }}
    footer {{ padding:32px 20px; color:var(--muted); border-top:1px solid var(--line); background:#fff; }}
  </style>
</head>
<body>
  <main>
    <div class=\"hero\">
      <div class=\"wrap\">
        <div class=\"eyebrow\">{escape_html(industry)} / {escape_html(region)} / 提案用サンプル</div>
        <h1>{escape_html(name)}の魅力を、予約につながる導線へ。</h1>
        <p class=\"lead\">このページは営業提案用の非公式モックです。お店の雰囲気・強み・来店導線を1ページで整理し、スマホから予約/問い合わせ/LINE追加まで迷わず進める形を想定しています。</p>
        <div class=\"cta-row\">
          <a class=\"btn primary\" href=\"#booking\">予約導線を見る</a>
          <a class=\"btn secondary\" href=\"#proposal\">改善ポイント</a>
        </div>
      </div>
    </div>

    <section id=\"proposal\">
      <div class=\"wrap\">
        <h2>見えている改善余地</h2>
        <div class=\"grid\">
          <div class=\"card\"><h3>課題シグナル</h3><ul>{gap_items}</ul></div>
          <div class=\"card\"><h3>最初の提案物</h3><ul>{angle_items}</ul></div>
          <div class=\"card\"><h3>期待できる効果</h3><ul><li>スマホ検索から予約/問い合わせまでの離脱を減らす</li><li>営業時間・メニュー・アクセス情報を統一する</li><li>LINEや再来店施策へ自然につなげる</li></ul></div>
        </div>
      </div>
    </section>

    <section id=\"booking\" style=\"background:var(--soft)\">
      <div class=\"wrap\">
        <h2>導線イメージ</h2>
        <div class=\"grid\">
          <div class=\"card\"><strong>1. 料理/雰囲気</strong><p class=\"note\">写真・人気メニュー・利用シーンをファーストビューで訴求。</p></div>
          <div class=\"card\"><strong>2. 予約CTA</strong><p class=\"note\">電話だけでなく、フォーム/予約サービス/LINEへの分かりやすいボタンを固定。</p></div>
          <div class=\"card\"><strong>3. 再来店</strong><p class=\"note\">LINE友だち追加、季節メニュー、クーポン配信の入口を用意。</p></div>
        </div>
      </div>
    </section>

    <section>
      <div class=\"wrap\">
        <h2>参照した公開情報</h2>
        <ul>{source_links}</ul>
        <p class=\"note\">※このモックは公開情報をもとにした提案用サンプルであり、店舗公式サイトではありません。</p>
      </div>
    </section>
  </main>
  <footer>Generated by Hermes restaurant lead pipeline.</footer>
</body>
</html>
"""


def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def escape_attr(s: str) -> str:
    return escape_html(s).replace("'", "&#x27;")


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
    base = lead_dir(args.industry, args.region, slug)
    code = base / "code"
    code.mkdir(parents=True, exist_ok=True)
    gaps = args.gap or []
    angles = args.angle or []
    urls = args.source_url or []
    (code / "index.html").write_text(html_template(args.name, args.industry, args.region, gaps, angles, urls), encoding="utf-8")
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
        "## 安全メモ",
        "- これは営業提案用の非公式サンプルであり、店舗公式サイトではありません。",
        "- 外部送信は最終承認後のみ。",
    ]
    (base / "proposal.md").write_text("\n".join(proposal) + "\n", encoding="utf-8")
    verify_html(code / "index.html")
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
    p.add_argument("--region", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--slug")
    p.add_argument("--gap", action="append", default=[])
    p.add_argument("--angle", action="append", default=[])
    p.add_argument("--source-url", action="append", default=[])
    p.add_argument("--git-commit", action="store_true")
    p.set_defaults(func=cmd_scaffold)
    p = sub.add_parser("commit")
    p.add_argument("--message", default="chore: update lead sites")
    p.set_defaults(func=cmd_commit)
    p = sub.add_parser("index")
    p.add_argument("--git-commit", action="store_true")
    p.add_argument("--message", default="chore: update lead site index")
    p.set_defaults(func=cmd_index)
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
