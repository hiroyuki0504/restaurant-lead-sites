#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bespoke restaurant preview profiles and visual QA helpers.

Shared code here is only the production guardrail: photo rights, responsive CSS,
motion safety, and QA. The visual direction/copy is selected per restaurant so the
output does not collapse into one fixed-looking LP.
"""
from __future__ import annotations

import html
import json
import subprocess
from pathlib import Path
from typing import Any

APPROVED_RIGHTS = {"approved", "shop-approved", "shop-owned", "owned", "licensed", "official-approved"}
BANNED_PUBLIC_TERMS = [
    "改善余地",
    "課題シグナル",
    "最初の提案物",
    "参照した公開情報",
    "コンサル",
    "提案ロジック",
    "Webサイト制作サンプル",
    "課題",
    "CSS",
    "テンプレート",
    "未取得",
    "取得計画",
    "許諾済み",
    "店舗提供",
]
VIEWPORTS = {
    "desktop": "1440,1100",
    "laptop": "1024,900",
    "tablet": "768,1024",
    "phone": "390,844",
    "small-phone": "360,780",
}

DESIGN_PROFILES: dict[str, dict[str, Any]] = {
    "hardcore-niboshi": {
        "class": "profile-hardcore-niboshi",
        "default_palette": "niboshi",
        "nav_cta": "営業確認",
        "eyebrow": "TSUKUBA / NIBOSHI RAMEN",
        "hero_title": "煮干しの緊張感を、一杯に。",
        "hero_lead": "天久保で味わう、香りの強い煮干し中華ソバ。遠方から向かう人にも、営業日・並び方・アクセスがまっすぐ伝わるページです。",
        "primary_cta": "公式Xで営業確認",
        "secondary_cta": "一杯の楽しみ方",
        "story_title": "硬派な一杯を、迷わず食べに行けるように。",
        "story_text": "人気店ほど、初めての人は営業日・売切れ・駐車場で迷います。煮干しの強さと来店前の安心を、同じ温度で見せます。",
        "cards": [
            ("煮干ソバを主役に", "香り、余韻、和え玉までの流れを短い言葉で伝えます。"),
            ("公式Xへ自然に誘導", "休み・材料切れ・臨時案内は、来店前に確認しやすく。"),
            ("遠征客にも親切", "住所、駐車場、現金、並び方を近い場所にまとめます。"),
        ],
        "menu_title": "一杯、和え玉、営業確認。",
        "menu_text": "メニューを増やして見せるより、看板の一杯と訪問前の判断材料を絞って伝えます。",
        "menu_rows": [("煮干ソバ", "香りと旨味を一杯で味わう看板。"), ("和え玉", "食べ進めた後の楽しみを案内。"), ("来店前", "営業日、売切れ、アクセスを確認。")],
        "visit_title": "行く前に、ここだけ確認。",
        "visit_text": "営業状況、休業日、材料切れ、アクセス。人気店ほど大事な情報を最短で見られるようにします。",
        "photo_slots": [("MAIN", "煮干ソバ", "香りが立つ一杯"), ("SPACE", "店前 / カウンター", "到着前の安心"), ("DETAIL", "営業案内", "迷わず向かう情報")],
    },
    "urban-counter": {
        "class": "profile-urban-counter",
        "default_palette": "niboshi",
        "nav_cta": "最新情報",
        "eyebrow": "IRIYA TOKYO / COUNTER RAMEN",
        "hero_title": "入谷で、煮干しに向き合う。",
        "hero_lead": "駅からすぐの小さなカウンター。限定、売切れ、営業時間の変化まで、来店前に知りたいことを静かに整理します。",
        "primary_cta": "最新情報を見る",
        "secondary_cta": "一杯を見る",
        "story_title": "名店の緊張感を、初来店にもやさしく。",
        "story_text": "席数の少ない人気店は、営業状況と注文前の理解が体験を左右します。都市のカウンターらしい余白で、必要な情報だけを置きます。",
        "cards": [
            ("カウンター7席の集中", "短い滞在でも期待が高まるよう、空間と一杯を絞って見せます。"),
            ("限定・冷やしも追える", "日々変わる案内は公式Xへ自然につなぎます。"),
            ("駅近の判断を早く", "徒歩・営業時間・現金・売切れ目安をスマホで確認。"),
        ],
        "menu_title": "中華そば、限定、和え玉。",
        "menu_text": "写真と短い説明で、初めてでも注文前に楽しみ方がわかる構成です。",
        "menu_rows": [("中華そば", "煮干しの輪郭を中心に。"), ("限定", "当日の提供状況を確認。"), ("和え玉", "注文の流れやタイミングを案内。")],
        "visit_title": "営業状況を見てから、入谷へ。",
        "visit_text": "臨休、売切れ、限定の有無。出発前に確認したい情報をひとつにまとめます。",
        "photo_slots": [("BOWL", "一杯", "澄んだ煮干し"), ("COUNTER", "カウンター", "小さな店の空気"), ("NOTICE", "最新案内", "当日の判断")],
    },
    "mountain-miso": {
        "class": "profile-mountain-miso",
        "default_palette": "miso",
        "nav_cta": "出発前に確認",
        "eyebrow": "KOSUGE VILLAGE / MISO RAMEN",
        "hero_title": "山あいへ、味噌を食べに行く。",
        "hero_lead": "小菅村までの道のりも楽しみに変える一杯。濃厚味噌、ドライブ、営業情報を、出発前に見やすくまとめます。",
        "primary_cta": "来店前の確認へ",
        "secondary_cta": "味噌の魅力を見る",
        "story_title": "目的地になる一杯を、旅の文脈で伝える。",
        "story_text": "山梨の山あいに向かう時間、道の駅周辺の立ち寄り、濃厚味噌の期待感。都市型ラーメンとは違う来店理由を前面に出します。",
        "cards": [
            ("濃厚味噌を大きく", "香り、太めの麺、チャーシューの存在感が伝わる写真枠を中心に。"),
            ("ドライブ客に親切", "駐車場、営業時間、支払い、周辺目印を出発前に確認。"),
            ("SNSの最新情報へ", "休みや変更は、公式SNSへ自然に進める導線にします。"),
        ],
        "menu_title": "味噌、肉、山道の楽しみ。",
        "menu_text": "味の濃さだけでなく、行く理由と帰り道の満足まで伝える構成です。",
        "menu_rows": [("味噌", "看板の力強さを最初に。"), ("チャーシュー", "肉の存在感を写真で見せる。"), ("出発前", "営業、駐車場、支払いを確認。")],
        "visit_title": "小菅村へ向かう前に。",
        "visit_text": "山あいの店だからこそ、営業時間・駐車場・最新SNSを先に確認できることが大切です。",
        "photo_slots": [("MISO", "味噌ラーメン", "湯気と濃厚さ"), ("ROAD", "小菅村への道", "旅の目的地感"), ("SHOP", "外観 / 駐車場", "到着前の安心")],
    },
    "warm-neighborhood": {
        "class": "profile-warm-neighborhood",
        "default_palette": "warm",
        "nav_cta": "来店前に確認",
        "eyebrow": "LOCAL RESTAURANT",
        "hero_title": "この店で食べる理由を、まっすぐに。",
        "hero_lead": "料理、空間、来店前の確認を、店舗らしい順番でまとめます。初めての方にも迷わず魅力が伝わるページです。",
        "primary_cta": "来店前の確認へ",
        "secondary_cta": "料理を見る",
        "story_title": "お店の強みから、ページを組み立てる。",
        "story_text": "ジャンルや立地、予約の有無、SNS運用に合わせて、見せる順番を変えます。",
        "cards": [("看板料理", "一番伝えたい一皿を大きく。"), ("来店前の安心", "住所、時間、支払いを整理。"), ("再訪導線", "SNSやお知らせにつなげます。")],
        "menu_title": "名物と来店前情報を一画面で。",
        "menu_text": "正式メニューと写真が揃えば、店舗に合わせて差し替えます。",
        "menu_rows": [("名物", "最初に食べてほしい一皿。"), ("季節", "旬や限定を短く。"), ("来店前", "確認事項を先回り。")],
        "visit_title": "行く前に必要なことを、短く。",
        "visit_text": "営業時間、住所、SNS、問い合わせをまとめます。",
        "photo_slots": [("FOOD", "料理写真", "看板の一皿"), ("SPACE", "外観 / 店内", "店の空気"), ("DETAIL", "案内", "迷わず来店")],
    },
}


def escape(value: Any) -> str:
    return html.escape(str(value), quote=False)


def escape_attr(value: Any) -> str:
    return html.escape(str(value), quote=True)


def resolve_design_profile(name: str, requested: str = "auto") -> dict[str, Any]:
    if requested != "auto":
        return DESIGN_PROFILES.get(requested, DESIGN_PROFILES["warm-neighborhood"])
    if "イチカワ" in name or "ichikawa" in name.lower():
        return DESIGN_PROFILES["hardcore-niboshi"]
    if "晴" in name or "haru" in name.lower():
        return DESIGN_PROFILES["urban-counter"]
    if "梅ノ木" in name or "umenoki" in name.lower():
        return DESIGN_PROFILES["mountain-miso"]
    return DESIGN_PROFILES["warm-neighborhood"]


def build_asset_manifest(
    name: str,
    photo_urls: list[str] | None = None,
    photo_alts: list[str] | None = None,
    photo_rights: list[str] | None = None,
    source_urls: list[str] | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    photo_urls = photo_urls or []
    photo_alts = photo_alts or []
    photo_rights = photo_rights or []
    for index, url in enumerate(photo_urls):
        rights = (photo_rights[index] if index < len(photo_rights) else "needs_review").strip()
        item = {
            "url": url.strip(),
            "alt": (photo_alts[index] if index < len(photo_alts) else f"{name}の店舗写真"),
            "rights": rights,
            "source": "scaffold_arg",
            "kind": "photo",
            "usable_in_public_html": rights in APPROVED_RIGHTS,
        }
        if item["url"]:
            candidates.append(item)
    selected = [item for item in candidates if item["usable_in_public_html"]][:6]
    return {
        "version": 1,
        "status": "ready_with_photos" if selected else "needs_shop_photos",
        "policy": (
            "Public previews must use shop-provided, self-shot, licensed, or explicitly approved photos. "
            "Do not copy Google Business, Tabelog, Hot Pepper, blog, Instagram, or X photos without permission."
        ),
        "fallback_policy": "When no approved photo exists, show photo slots; do not fake ramen/food with CSS gradients.",
        "selected_photos": selected,
        "candidates": candidates,
        "source_urls": source_urls or [],
        "recommended_shots": [
            "hero: 代表料理を大きく",
            "gallery: 外観/入口",
            "gallery: 店内/カウンター",
            "support: メニュー/券売機/アクセス",
        ],
    }


def render_site_html(
    *,
    name: str,
    industry: str,
    region: str,
    angles: list[str],
    asset_manifest: dict[str, Any],
    palette: str = "auto",
    design_profile: str = "auto",
) -> str:
    del industry, angles  # proposal-only context; public page uses the store-specific direction below.
    profile = resolve_design_profile(name, design_profile)
    palette_class = palette if palette in {"niboshi", "miso", "warm"} else profile["default_palette"]
    photo_cards = render_photo_cards(asset_manifest, name, profile)
    body_photo_class = "" if photo_cards else " no-public-photos"
    default_photo_html = f'<div class="photo-stack reveal" aria-label="店舗写真エリア">{photo_cards}</div>' if photo_cards else ""
    counter_photo_html = f'<div class="counter-photo reveal" aria-label="店舗写真エリア">{photo_cards}</div>' if photo_cards else ""
    journey_photo_html = f'<div class="photo-stack reveal journey-photo" aria-label="店舗写真エリア">{photo_cards}</div>' if photo_cards else ""
    menu_rows = "".join(
        f"<div><strong>{escape(label)}</strong><span>{escape(text)}</span></div>"
        for label, text in profile["menu_rows"]
    )
    first_card_title, first_card_text = profile["cards"][0]
    other_cards = "".join(
        f"<article class=\"feature-card reveal\"><h3>{escape(title)}</h3><p>{escape(text)}</p></article>"
        for title, text in profile["cards"][1:]
    )
    nav_html = f'<nav class="site-nav" aria-label="主要メニュー"><a class="site-brand" href="#top">{escape(name)}</a><div class="site-nav-links"><a href="#story">魅力</a><a href="#menu">料理</a><a href="#visit">来店前</a><a class="nav-action" href="#visit">{escape(profile["nav_cta"])}</a></div></nav>'

    if profile["class"] == "profile-urban-counter":
        main_html = f"""
    <section class="counter-hero" id="top" data-parallax>
      <div class="page-wrap counter-grid">
        {counter_photo_html}
        <div class="counter-copy reveal"><p class="eyebrow">{escape(profile['eyebrow'])}</p><h1>{escape(profile['hero_title'])}</h1><p class="lead-text">{escape(profile['hero_lead'])}</p><div class="button-row"><a class="button button-primary" href="#visit">{escape(profile['primary_cta'])}</a><a class="button button-secondary" href="#menu">{escape(profile['secondary_cta'])}</a></div></div>
      </div>
    </section>
    <section class="content-section counter-menu" id="menu"><div class="page-wrap counter-menu-grid"><div class="section-heading reveal"><p class="section-kicker">MENU FIRST</p><h2>{escape(profile['menu_title'])}</h2><p>{escape(profile['menu_text'])}</p></div><div class="menu-list reveal">{menu_rows}</div></div></section>
    <section class="content-section" id="story"><div class="page-wrap section-heading reveal"><p class="section-kicker">COUNTER STORY</p><h2>{escape(profile['story_title'])}</h2><p>{escape(profile['story_text'])}</p></div><div class="page-wrap feature-grid counter-feature"><article class="feature-card feature-wide reveal"><h3>{escape(first_card_title)}</h3><p>{escape(first_card_text)}</p></article>{other_cards}</div></section>
    <section class="visit-section" id="visit"><div class="page-wrap visit-grid"><div class="visit-panel reveal"><p class="section-kicker">VISIT GUIDE</p><h2>{escape(profile['visit_title'])}</h2><p>{escape(profile['visit_text'])}</p><div class="button-row"><a class="button button-primary" href="#top">上へ戻る</a></div></div><div class="info-list reveal"><div><strong>エリア</strong><span>{escape(region)}</span></div><div><strong>来店前</strong><span>臨休・売切れ・最新情報を確認</span></div><div><strong>写真</strong><span>一杯・カウンター・案内を掲載</span></div></div></div></section>
"""
    elif profile["class"] == "profile-mountain-miso":
        main_html = f"""
    <section class="journey-hero" id="top" data-parallax>
      <div class="page-wrap journey-grid">
        <div class="hero-copy reveal"><p class="eyebrow">{escape(profile['eyebrow'])}</p><h1>{escape(profile['hero_title'])}</h1><p class="lead-text">{escape(profile['hero_lead'])}</p><div class="button-row"><a class="button button-primary" href="#visit">{escape(profile['primary_cta'])}</a><a class="button button-secondary" href="#menu">{escape(profile['secondary_cta'])}</a></div></div>
        <aside class="journey-board reveal"><span>ROUTE NOTE</span><strong>{escape(region)}</strong><p>出発前に営業・駐車場・最新情報を確認。</p></aside>
      </div>
    </section>
    <section class="content-section" id="story"><div class="page-wrap journey-story"><div class="section-heading reveal"><p class="section-kicker">TRIP STORY</p><h2>{escape(profile['story_title'])}</h2><p>{escape(profile['story_text'])}</p></div>{journey_photo_html}</div><div class="page-wrap feature-grid mountain-feature"><article class="feature-card feature-wide reveal"><h3>{escape(first_card_title)}</h3><p>{escape(first_card_text)}</p></article>{other_cards}</div></section>
    <section class="content-section menu-section mountain-menu" id="menu"><div class="page-wrap menu-layout"><div class="section-heading reveal"><p class="section-kicker">MISO MAP</p><h2>{escape(profile['menu_title'])}</h2><p>{escape(profile['menu_text'])}</p></div><div class="menu-list reveal">{menu_rows}</div></div></section>
    <section class="visit-section" id="visit"><div class="page-wrap visit-grid"><div class="visit-panel reveal"><p class="section-kicker">BEFORE DRIVE</p><h2>{escape(profile['visit_title'])}</h2><p>{escape(profile['visit_text'])}</p><div class="button-row"><a class="button button-primary" href="#top">上へ戻る</a></div></div><div class="info-list reveal"><div><strong>エリア</strong><span>{escape(region)}</span></div><div><strong>出発前</strong><span>営業状況・駐車場・支払いを確認</span></div><div><strong>写真</strong><span>味噌・外観・道のりを掲載</span></div></div></div></section>
"""
    else:
        main_html = f"""
    <section class="hero-section" id="top" data-parallax>
      <div class="page-wrap hero-grid">
        <div class="hero-copy reveal"><p class="eyebrow">{escape(profile['eyebrow'])}</p><h1>{escape(profile['hero_title'])}</h1><p class="lead-text">{escape(profile['hero_lead'])}</p><div class="button-row"><a class="button button-primary" href="#visit">{escape(profile['primary_cta'])}</a><a class="button button-secondary" href="#menu">{escape(profile['secondary_cta'])}</a></div></div>
        {default_photo_html}
      </div>
    </section>
    <section class="content-section" id="story"><div class="page-wrap section-heading reveal"><p class="section-kicker">STORY</p><h2>{escape(profile['story_title'])}</h2><p>{escape(profile['story_text'])}</p></div><div class="page-wrap feature-grid"><article class="feature-card feature-wide reveal"><h3>{escape(first_card_title)}</h3><p>{escape(first_card_text)}</p></article>{other_cards}</div></section>
    <section class="content-section menu-section" id="menu"><div class="page-wrap menu-layout"><div class="section-heading reveal"><p class="section-kicker">MENU</p><h2>{escape(profile['menu_title'])}</h2><p>{escape(profile['menu_text'])}</p></div><div class="menu-list reveal">{menu_rows}</div></div></section>
    <section class="visit-section" id="visit"><div class="page-wrap visit-grid"><div class="visit-panel reveal"><p class="section-kicker">VISIT GUIDE</p><h2>{escape(profile['visit_title'])}</h2><p>{escape(profile['visit_text'])}</p><div class="button-row"><a class="button button-primary" href="#top">上へ戻る</a></div></div><div class="info-list reveal"><div><strong>エリア</strong><span>{escape(region)}</span></div><div><strong>来店前</strong><span>営業状況・アクセス・最新情報をまとめて確認</span></div><div><strong>写真</strong><span>料理・外観・店内をわかりやすく掲載</span></div></div></div></section>
"""

    html_text = f"""<!doctype html>
<html lang="ja" class="no-js">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(name)} | {escape(region)}の店舗案内</title>
  <meta name="description" content="{escape_attr(name)}の料理、空間、来店前の確認をスマホで見やすくまとめた店舗ページ。" />
  <meta name="robots" content="noindex" />
  <script>document.documentElement.classList.replace('no-js','js');</script>
  <style>{design_css(profile['class'])}</style>
</head>
<body class="{escape_attr(profile['class'])} palette-{escape_attr(palette_class)}{body_photo_class}" data-photo-status="{escape_attr(asset_manifest['status'])}">
  {nav_html}
  <main>{main_html}</main>
  <footer class="site-footer"><div class="page-wrap"><span>© {escape(name)}</span><span>最新情報は店舗告知をご確認ください。</span></div></footer>
  <script>{motion_js()}</script>
</body>
</html>
"""
    return "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"

def render_photo_cards(asset_manifest: dict[str, Any], name: str, profile: dict[str, Any]) -> str:
    del profile
    selected = asset_manifest.get("selected_photos") or []
    if not selected:
        return ""
    return "\n".join(
        f'<figure class="photo-card photo-card-{index}"><img src="{escape_attr(item["url"])}" alt="{escape_attr(item.get("alt") or name + "の店舗写真")}" loading="{"eager" if index == 1 else "lazy"}"><figcaption>{escape(item.get("alt") or "店舗写真")}</figcaption></figure>'
        for index, item in enumerate(selected[:3], start=1)
    )


def design_css(profile_class: str = "profile-warm-neighborhood") -> str:
    common = """
:root{--ink:#16110d;--muted:#6d625a;--paper:#fffaf2;--cream:#f5ecdf;--deep:#17100b;--accent:#b85b32;--gold:#d5a65b;--line:rgba(57,35,21,.16);--shadow:0 24px 70px rgba(35,22,12,.14);--radius-lg:28px;--ease:cubic-bezier(.16,1,.3,1);--sans:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",system-ui,sans-serif;--serif:"Hiragino Mincho ProN","Yu Mincho",YuMincho,"Noto Serif JP",serif}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;overflow-x:hidden;background:var(--cream);color:var(--ink);font-family:var(--serif)}a{color:inherit}.page-wrap{width:min(1160px,calc(100% - 40px));margin-inline:auto}.site-nav{position:fixed;z-index:30;top:16px;left:50%;transform:translateX(-50%);width:min(1160px,calc(100% - 32px));display:flex;align-items:center;justify-content:space-between;gap:18px;padding:12px 14px 12px 18px;background:rgba(23,16,11,.92);color:white;border:1px solid rgba(255,255,255,.14);box-shadow:0 18px 50px rgba(0,0,0,.18)}.site-brand{font:900 .95rem var(--sans);letter-spacing:.12em;text-decoration:none}.site-nav-links{display:flex;align-items:center;gap:4px}.site-nav-links a{font:800 .9rem var(--sans);text-decoration:none;padding:10px 12px;color:rgba(255,255,255,.78);border-radius:12px}.site-nav-links a:hover{background:rgba(255,255,255,.10);color:white}.site-nav-links .nav-action{background:var(--gold);color:var(--deep)}.eyebrow,.section-kicker{font:900 .78rem var(--sans);letter-spacing:.18em;color:var(--gold);text-transform:uppercase}.lead-text{font:500 clamp(1rem,1.45vw,1.22rem)/2.05 var(--sans);color:rgba(255,255,255,.84);max-width:650px}.button-row{display:flex;gap:12px;flex-wrap:wrap;margin-top:30px}.button{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:13px 17px;border-radius:14px;text-decoration:none;font:900 .96rem var(--sans);border:1px solid rgba(255,255,255,.22);transition:transform .25s var(--ease),box-shadow .25s var(--ease)}.button:hover{transform:translateY(-2px)}.button-primary{background:white;color:var(--deep);box-shadow:0 18px 40px rgba(0,0,0,.18)}.button-secondary{color:white;background:rgba(255,255,255,.08)}.photo-stack{display:grid;grid-template-columns:1fr .72fr;grid-template-rows:1fr 1fr;gap:16px;min-height:620px}.photo-card{position:relative;overflow:hidden;border-radius:var(--radius-lg);border:1px solid rgba(255,255,255,.22);box-shadow:0 30px 90px rgba(0,0,0,.24);background:#2b1a11}.photo-card-1{grid-row:1/3}.photo-card img{width:100%;height:100%;object-fit:cover;transition:transform .75s var(--ease)}.photo-card:hover img{transform:scale(1.045)}.photo-card figcaption{position:absolute;left:18px;bottom:16px;color:white;font:900 .82rem var(--sans);letter-spacing:.12em;text-shadow:0 10px 30px rgba(0,0,0,.45)}.content-section{padding:96px 0}.section-heading{display:grid;grid-template-columns:.74fr 1fr;gap:42px;align-items:end;margin-bottom:34px}.section-heading h2{margin:8px 0 0;font-size:clamp(2.15rem,4.8vw,5.2rem);line-height:.96;letter-spacing:-.075em;text-wrap:balance}.section-heading p{font:500 1.03rem/2 var(--sans);color:var(--muted);margin:0}.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.feature-card{min-height:260px;padding:26px;border-radius:var(--radius-lg);background:var(--paper);border:1px solid var(--line);box-shadow:0 16px 45px rgba(35,22,12,.07)}.feature-wide{grid-column:span 2;background:linear-gradient(135deg,#fffaf2,#ead4b5)}.feature-card h3{margin:0 0 12px;font-size:1.48rem;letter-spacing:-.04em}.feature-card p{font:500 .98rem/1.92 var(--sans);color:var(--muted)}.menu-section{background:#fffaf2}.menu-layout{display:grid;grid-template-columns:1fr .78fr;gap:42px;align-items:start}.menu-list{border-radius:var(--radius-lg);padding:26px;background:white;border:1px solid var(--line);box-shadow:var(--shadow)}.menu-list div{display:grid;grid-template-columns:92px 1fr;gap:18px;padding:18px 0;border-bottom:1px solid var(--line);font-family:var(--sans)}.menu-list div:last-child{border-bottom:0}.menu-list span{color:var(--muted);line-height:1.8}.visit-section{padding:96px 0;background:var(--deep);color:white;position:relative;overflow:hidden}.visit-grid{display:grid;grid-template-columns:.9fr 1.1fr;gap:26px}.visit-panel,.info-list{border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.08);border-radius:var(--radius-lg);padding:30px}.visit-panel h2{margin:8px 0 14px;font-size:clamp(2.1rem,4.5vw,4.8rem);line-height:.98;letter-spacing:-.075em}.visit-panel p{font:500 1rem/1.9 var(--sans);color:rgba(255,255,255,.76)}.info-list{display:grid;gap:0}.info-list div{display:grid;grid-template-columns:110px 1fr;gap:18px;padding:17px 0;border-bottom:1px solid rgba(255,255,255,.12);font-family:var(--sans)}.info-list div:last-child{border-bottom:0}.info-list strong{color:var(--gold)}.info-list span{color:rgba(255,255,255,.8);line-height:1.7}.site-footer{padding:28px 0;background:#0f0a07;color:rgba(255,255,255,.66);font:500 .86rem var(--sans)}.site-footer .page-wrap{display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap}.reveal{opacity:1;transform:none}.js .reveal{opacity:1;transform:none;transition:transform .75s var(--ease)}.js .reveal.is-visible{opacity:1;transform:none}.no-public-photos .hero-grid,.no-public-photos .counter-grid,.no-public-photos .journey-grid{grid-template-columns:1fr;max-width:900px}.no-public-photos .counter-copy,.no-public-photos .hero-copy{max-width:820px}.no-public-photos .hero-section,.no-public-photos .counter-hero,.no-public-photos .journey-hero{min-height:auto;padding-bottom:72px}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.button,.photo-card img,.js .reveal{transition:none}.js .reveal{opacity:1;transform:none}}@media(max-width:980px){.hero-grid,.section-heading,.menu-layout,.visit-grid{grid-template-columns:1fr}.photo-stack{grid-template-columns:1fr;min-height:auto;transform:none}.photo-card-1{grid-row:auto;min-height:440px}.feature-grid{grid-template-columns:1fr}.feature-wide{grid-column:span 1}.site-nav-links a:not(.nav-action){display:none}}@media(max-width:640px){.page-wrap{width:min(100% - 28px,1160px)}.site-nav{top:10px;width:calc(100% - 20px);padding:10px 10px 10px 14px}.site-brand{font-size:.86rem;letter-spacing:.06em}.hero-copy h1,.counter-copy h1{font-size:clamp(2.85rem,17vw,5.2rem)}.content-section,.visit-section{padding:72px 0}.button{width:100%}.button-row{width:100%}.section-heading h2,.visit-panel h2{font-size:2.35rem}.menu-list div,.info-list div{grid-template-columns:1fr;gap:6px}.feature-card,.visit-panel,.info-list,.menu-list{border-radius:24px;padding:22px}}
""".strip()
    profile_overrides = {
        "profile-hardcore-niboshi": ".profile-hardcore-niboshi{--cream:#efe5d5;--deep:#100b08;--accent:#8fa6a8;--gold:#d8a84f;--radius-lg:20px}.profile-hardcore-niboshi .site-nav{border-radius:0}.hero-section{position:relative;min-height:100svh;display:grid;align-items:center;padding:128px 0 78px;background:linear-gradient(112deg,#0d0907,#28150d 45%,#31434a);color:white;isolation:isolate}.hero-section:before{content:\"\";position:absolute;inset:0;z-index:-1;background:radial-gradient(circle at 18% 72%,rgba(47,70,55,.45),transparent 32rem),radial-gradient(circle at 82% 18%,rgba(213,166,91,.32),transparent 28rem),linear-gradient(180deg,rgba(0,0,0,0),rgba(0,0,0,.36));opacity:.9}.hero-grid{display:grid;grid-template-columns:.92fr 1.08fr;gap:48px;align-items:center}.hero-copy h1{margin:22px 0 18px;font-size:clamp(3.2rem,8.8vw,8.8rem);line-height:.92;letter-spacing:-.085em;text-wrap:balance}.profile-hardcore-niboshi .feature-wide{background:linear-gradient(135deg,#fffaf2,#e4d5bf)}@media(max-width:640px){.hero-section{padding:106px 0 58px}}",
        "profile-urban-counter": ".profile-urban-counter{--cream:#f3eadc;--deep:#17110e;--accent:#98a9aa;--gold:#d6a04d;--radius-lg:22px}.profile-urban-counter .site-nav{border-radius:0}.counter-hero{min-height:100svh;padding:110px 0 70px;background:#20100c;color:white;position:relative;overflow:hidden}.counter-hero:before{content:\"\";position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,255,255,.08) 1px,transparent 1px);background-size:42px 100%}.counter-grid{position:relative;display:grid;grid-template-columns:.84fr 1fr;gap:42px;align-items:center}.counter-copy h1{margin:22px 0 18px;font-size:clamp(3.2rem,9vw,8.6rem);line-height:.9;letter-spacing:-.055em}.counter-photo{display:grid;gap:14px}.counter-photo .photo-card-1{min-height:520px}.counter-menu{background:#f8f0e4}.counter-menu-grid{display:grid;grid-template-columns:.85fr 1.15fr;gap:44px;align-items:start}.counter-feature .feature-card{border-radius:10px}@media(max-width:980px){.counter-grid,.counter-menu-grid{grid-template-columns:1fr}.counter-photo .photo-card-1{min-height:360px}}",
        "profile-mountain-miso": ".profile-mountain-miso{--cream:#f5ead9;--deep:#1f1009;--accent:#b75a2b;--gold:#df9842;--radius-lg:34px}.profile-mountain-miso .site-nav{border-radius:22px}.journey-hero{min-height:92svh;padding:120px 0 72px;background:linear-gradient(112deg,#1b0e08,#4a2413 52%,#7a421d);color:white}.journey-grid{display:grid;grid-template-columns:1fr .62fr;gap:38px;align-items:end}.journey-grid .hero-copy h1{margin:22px 0 18px;font-size:clamp(3.2rem,8.7vw,8.4rem);line-height:.92;letter-spacing:-.075em}.journey-board{border-radius:34px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.16);padding:28px;box-shadow:0 28px 80px rgba(0,0,0,.22)}.journey-board span{font:900 .76rem var(--sans);letter-spacing:.18em;color:var(--gold)}.journey-board strong{display:block;margin:16px 0;font-size:clamp(2rem,5vw,4rem);line-height:.95}.journey-board p{font:700 1rem/1.8 var(--sans);color:rgba(255,255,255,.78)}.journey-story{display:grid;grid-template-columns:.88fr 1.12fr;gap:34px;align-items:start}.journey-photo{min-height:520px;transform:rotate(-.8deg)}.mountain-feature .feature-wide,.mountain-menu .menu-list{background:linear-gradient(135deg,#fffaf2,#f0d2a6)}@media(max-width:980px){.journey-grid,.journey-story{grid-template-columns:1fr}.journey-photo{transform:none}}",
        "profile-warm-neighborhood": ".profile-warm-neighborhood{--cream:#f5ecdf;--deep:#17100b;--accent:#9f5f3d;--gold:#d3a766}.hero-section{min-height:100svh;display:grid;align-items:center;padding:128px 0 78px;background:linear-gradient(120deg,#1a100b,#3b2115 52%,#604025);color:white}.hero-grid{display:grid;grid-template-columns:.92fr 1.08fr;gap:48px;align-items:center}.hero-copy h1{margin:22px 0 18px;font-size:clamp(3.2rem,8.8vw,8.8rem);line-height:.92;letter-spacing:-.085em}",
    }
    return common + "\n" + profile_overrides.get(profile_class, profile_overrides["profile-warm-neighborhood"])


def motion_js() -> str:
    return """
(() => { const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; const items = document.querySelectorAll('.reveal'); if (!reduce && 'IntersectionObserver' in window) { const io = new IntersectionObserver((entries) => { for (const entry of entries) { if (entry.isIntersecting) { entry.target.classList.add('is-visible'); io.unobserve(entry.target); } } }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' }); items.forEach((item) => io.observe(item)); } else { items.forEach((item) => item.classList.add('is-visible')); } })();
""".strip()


def write_asset_plan(path: Path, name: str, manifest: dict[str, Any]) -> None:
    lines = [
        f"# {name} 写真取得・権利メモ",
        "",
        "- CSSの偽料理・偽ラーメンは使わない。",
        "- 公開HTMLに入れるのは、店舗提供・自前撮影・商用ライセンス・明示許可済み素材だけ。",
        "- 第三者媒体/SNS写真は候補URLとして記録しても無断コピーしない。",
        "",
        f"状態: `{manifest['status']}`",
        "",
        "## 使用写真",
    ]
    selected = manifest.get("selected_photos") or []
    if selected:
        lines += [f"- {item['url']} ({item['rights']})" for item in selected]
    else:
        lines.append("- 未設定。店舗提供写真または撮影素材が必要。")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_static_qa(code_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    html_text = (code_dir / "index.html").read_text(encoding="utf-8")
    result = {
        "ok": True,
        "banned_terms": [term for term in BANNED_PUBLIC_TERMS if term in html_text],
        "photo_status": manifest["status"],
        "selected_photo_count": len(manifest.get("selected_photos") or []),
        "has_motion": "IntersectionObserver" in html_text and "reveal" in html_text,
        "no_fake_food_classes": not any(token in html_text for token in ["ramen-art", "bowl-panel", "fake-ramen"]),
    }
    result["ok"] = not result["banned_terms"] and result["has_motion"] and result["no_fake_food_classes"]
    qa_dir = code_dir / "qa"
    qa_dir.mkdir(exist_ok=True)
    (qa_dir / "static-check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (qa_dir / "visual-review-rubric.md").write_text(
        "# Visual QA Rubric\n\n- PC/スマホで横スクロールなし。\n- 店ごとの立地・業態・営業導線が反映されている。\n- 写真がある場合は主役になっている。写真がない場合も偽料理でごまかしていない。\n- 公開ページに内部営業分析語が出ていない。\n- pill/ガラス/巨大グラデだけのAI LP顔になっていない。\n",
        encoding="utf-8",
    )
    return result


def run_playwright_visual_qa(code_dir: Path) -> dict[str, Any]:
    qa_dir = code_dir / "qa"
    qa_dir.mkdir(exist_ok=True)
    url = (code_dir / "index.html").resolve().as_uri()
    screenshots: dict[str, str] = {}
    errors: dict[str, str] = {}
    for label, viewport in VIEWPORTS.items():
        out = qa_dir / f"{label}.png"
        cmd = ["playwright", "screenshot", "--full-page", "--browser", "chromium", "--viewport-size", viewport, "--wait-for-timeout", "500", url, str(out)]
        res = subprocess.run(cmd, text=True, capture_output=True, timeout=45)
        if res.returncode == 0 and out.exists():
            screenshots[label] = str(out)
        else:
            errors[label] = res.stderr or res.stdout or f"exit={res.returncode}"
    result = {"ok": not errors, "screenshots": screenshots, "errors": errors}
    (qa_dir / "playwright-check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
