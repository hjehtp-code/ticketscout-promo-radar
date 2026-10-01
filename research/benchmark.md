# Fixed benchmark: 2026-10-01

Main: discounted theme park tickets. Three sites fixed for this cycle. Each site's ten relevant pages are a reproducible editorial sample selected from its public navigation/category pages, **not** a fabricated traffic or Google ranking of its articles. Some are commercial ticket pages. Raw My Park Tickets/FunEx text stays local in JSON and is not published or copied. Undercover Tourist read through public web tool; direct research request received 403, no access-control bypass attempted. Its robots allows public attraction/blog pages and disallows search/special paths. FunEx/My Park Tickets robots read by research.py.

“它们全都没有” below means **not found in these inspected samples**. It is not a claim about all pages of the three sites. No claim that a structural feature caused ranking. The earlier SERP established the three commercial results; their full ranking factors are unknown.

| 页面主题 | 它们讲了什么 | 它们全都没有（本次样本未见） | 我能补的独家料从哪取 |
|---|---|---|---|
| LEGOLAND ticket: current versus expired offer terms (LL-01, first) | UT: date/inclusion/refund distinctions; MPT: Florida base/Peppa/Water Park bundles and FAQs; FunEx: California inclusions and tips | Florida official overview vs detailed-page deadline conflict and expired BOGO block placed side-by-side with an explicit do-not-use conclusion | Configured official LEGOLAND Florida overview/details pages, dated receipt; independently constructed date-check matrix |
| carowinds tickets: actual visit day and add-on coverage | UT: park overview/maps and ticket widget; FunEx: weekday/any-day exclusions, season and FAQs; MPT sample has no Carowinds page | Cross-reference selected day and product scope with separately named seasonal event rather than generic discount headline | Official Six Flags Carowinds ticket/operating-calendar/event terms; verify redirected URLs before use |
| knott's berry farm tickets: daytime versus event/water park | UT: park resources and events links; FunEx: weekday group product, event exclusions and detailed FAQs; MPT sampled pages cover Orlando | One side-by-side official evidence worksheet matching intended visit/event to exact admission product | Official Six Flags Knott's product/event pages and terms; no extra savings invented |
| six flags tickets: choose exact park and restrictions | UT: Magic Mountain resources; FunEx: separate park pages and weekday restrictions/chaperone/refund FAQs; MPT sample mostly Orlando | A park-specific date/age/add-on checklist with facts marked unknown when not confirmed | Official exact-park ticket conditions/chaperone policies and parking documentation; never apply one park's terms to all parks |
| disneyland tickets discount / cheap disneyland tickets | UT: ticket filters, reservations, refund terms and saving guide; MPT: Disney World is a different destination; FunEx Disneyland redirects off host, not inspected as a FunEx page | Independently filled comparable-party matrix tied to the user's exact date/product, with perks separated from cash savings | Disneyland official tickets/offers and reservation terms; currently browser blocked/HTML empty, hold factual promises |
| costco universal studios tickets | UT/FunEx: Universal Hollywood ticket types and expiry; MPT: Orlando base/park-to-park pages; no Costco-specific page in this sample | Official Costco product validity and Universal location cross-check for the same visit, no membership assumption | Costco official product and Universal official product terms; Costco fetch currently certificate error, do not disable TLS |

## Undercover Tourist: ten read pages

1. https://www.undercovertourist.com/theme-parks/ — location/brand directory, offers and unavailable ticket states.
2. https://www.undercovertourist.com/los-angeles/disneyland-resort/ — types, reservation, redemption, expiry/refund distinctions.
3. https://www.undercovertourist.com/orlando/walt-disney-world-resort/ — ticket wizard, base/Hopper and date-specific product filters.
4. https://www.undercovertourist.com/los-angeles/universal-studios-hollywood-resort/ — one/two-day/Express products, redemption/refund/expiry.
5. https://www.undercovertourist.com/orlando/legoland-florida-resort/ — themed attraction bundles, dated visits, non-refundable product conditions.
6. https://www.undercovertourist.com/san-diego/legoland-california-resort/ — resort ticket/CityPASS bundles and revisit windows.
7. https://www.undercovertourist.com/los-angeles/knotts-berry-farm/ — attraction/map/event resources and calendar widget; no readable populated offer rows in inspected extract.
8. https://www.undercovertourist.com/charlotte/carowinds/ — overview, maps, related guides and ticket widget.
9. https://www.undercovertourist.com/los-angeles/six-flags-magic-mountain/ — attraction/map/photo resources and calendar widget.
10. https://www.undercovertourist.com/blog/save-money-on-disneyland-tickets/ — saving methods, ticket price comparison, dining benefits and FAQs; generic cost comparison is already covered here.

Attempted Universal Orlando page: initial web fetch succeeded but follow-up details failed, so it is excluded from the count of ten content-inspected pages. Do not infer absent features from an incomplete extract.

## My Park Tickets: ten read pages (shop order)

1. /shop/ — price cards and product catalog.
2. /product/legoland-1-day/ — base admission, SEA LIFE, ages, parking and rainy-day FAQ.
3. /product/seaworld-orlando-single-day-admission/ — inclusion/exclusion lists, operating days, dining and fees.
4. /product/walt-disney-world/ — one-day type/date/age selection and park descriptions.
5. /product/universal-orlando-resort/ — one-park base versus park-to-park selection.
6. /product/legoland-1-day-peppa-pig/ — two-attraction bundle.
7. /product/legoland-1-day-water-park/ — water-park combo.
8. /product/seaworld-all-day-dining-deal/ — dining intervals; admission excluded.
9. /product/2-days-walt-disney-world/ — multi-day base/Hopper choices.
10. /product/1-day-park-to-park-universal-orlando/ — two parks on the same day and age/date choice.

## FunEx: ten read pages

1. /category/theme-parks — geographic product directory.
2. /tickets/k/knotts-berry-farm — weekdays/group minimum, seasonal exclusions and FAQ.
3. /tickets/l/legoland-california-resort — bundles, attractions, age/parking/cash/weather questions.
4. /tickets/sf-dk/six-flags-discovery-kingdom — product dates, attractions, FAQs.
5. /tickets/m/six-flags-magic-mountain — Saturday restrictions, separately promoted event, parking/expiry FAQs.
6. /tickets/us/universal-studios-hollywood — one/two-day/Express/pass distinctions and product validity.
7. /tickets/sf-og/six-flags-over-georgia — weekday versus any-day ticket and seasonal event context (use exact stored URL if slug differs).
8. /tickets/sf-ww/six-flags-white-water — park overview, chaperone policy and refund FAQ.
9. /tickets/sf-ga/six-flags-great-america — weekday versus any-day and date/parking questions.
10. /tickets/cd-nc/carowinds — weekday versus any-day, dated products and event context.

Full exact URLs and read status in funex-pages.json. Disneyland link redirected to another host and is excluded; no login/private checkout was read. Do not reuse these reseller prices as official park discount evidence.

## What to learn without copying

UT: make types and use restrictions visible, link planning resources. MPT: put selectable product and inclusion/exclusion near the top. FunEx: answer practical questions by park and label product-specific dates. TicketScout should add a concise answer, official-source receipts, contradiction handling and a user-filled same-party comparison worksheet. These are design observations, not an explanation of ranking.
