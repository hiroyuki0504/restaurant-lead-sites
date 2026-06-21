# Restaurant Lead Sites

Approved lead sample sites are managed here as a single git repository.

## Directory layout

```text
<industry-slug>/<region-slug>/<lead-slug>/
  lead.json        # original industry/region names, source URLs, gaps, deployment info
  proposal.md      # human-readable proposal brief
  code/            # deployable static site root
    index.html
    vercel.json
```

Example:

```text
restaurant/tokyo-shibuya/sample-bistro/code/index.html
```

Japanese labels are preserved inside `lead.json` / `proposal.md`; filesystem paths use ASCII slugs so GitHub Pages serves them reliably.

## Workflow

1. Daily Hermes cron sends top 3 restaurant lead recommendations to Discord.
2. User approves one lead with `APPROVE_LEAD #N`.
3. Hermes runs `scripts/lead_site.py scaffold ...` to create this directory structure.
4. Hermes verifies the generated HTML locally.
5. Hermes commits all generated code to this repo.
6. Hermes deploys the approved site's `code/` directory to Vercel when Vercel auth exists.

## Commands

```bash
python3 scripts/lead_site.py check
python3 scripts/lead_site.py scaffold --industry 飲食店 --region 東京都渋谷区 --name "Sample Bistro" --gap "予約導線が弱い" --angle "1枚LP+予約CTA" --source-url https://example.com --git-commit
python3 scripts/lead_site.py deploy-vercel --industry 飲食店 --region 東京都渋谷区 --slug sample-bistro
```

## Deployment note

This repo is published with GitHub Pages from the `main` branch root. Each generated site is viewable under the repo Pages URL at `/<industry-slug>/<region-slug>/<lead-slug>/code/`.

Vercel can still be used later for individual lead sites. Vercel CLI credentials are not present yet on this machine; run `npx vercel login` once, then the deploy command can publish each approved lead site and record the deployment URL in `lead.json`.
