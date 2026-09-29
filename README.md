# TicketScout

TicketScout is a small static directory for verified attraction and theme park ticket discounts. The initial market is English (United States); the configured provider is Tiqets. A deal appears only when a public official source contains explicit discount evidence. Standard “from” ticket prices are not represented as discounts.

## Run locally

Requires Python 3 and no third-party packages.

```sh
python scraper.py
python build.py
```

The generated website is in `site/`. If no eligible discount can be verified, the site displays an honest empty state.

## Add or change a provider

Edit `.ilang/site.ilang`. Both `scraper.py` and `build.py` read its site and provider configuration, so provider names and destinations are not duplicated in code. The scraper checks public `robots.txt` rules, follows the configured public sitemap, and reads only public HTML pages. It does not use login-only content, site APIs, or anti-bot workarounds.

## GitHub Pages build / Cloudflare Pages

The GitHub Actions workflow checks sources every six hours and commits changed data and generated pages. For Cloudflare Pages, connect the repository and use build command `python build.py` and output directory `site`. The default Pages URL in `.ilang/site.ilang` is a placeholder; replace `domain` and `base_url` with the actual assigned `pages.dev` origin before publishing for correct canonical and sitemap URLs.

There is no affiliate relationship configured. Add an affiliate URL only after joining a program and confirming its published terms; the site does not imply commission or endorsement.

This project does not promise traffic or revenue. Offers, prices, and availability may change at the provider.

Site rules are described in I-Lang in `.ilang/site.ilang`; protocol information: [ilang.ai](https://ilang.ai).

