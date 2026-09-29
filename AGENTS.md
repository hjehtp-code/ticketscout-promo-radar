::ILANG
[TYPE:project-guidance][PROJECT:TicketScout][LANG:zh]

::STATE{@PROJECT, purpose:Static directory of verified attraction and theme-park ticket discounts, runtime:Python standard library only}
::RULE{Treat .ilang/site.ilang as the single source of provider and site configuration; scraper.py and build.py must parse it}
::RULE{Use only configured public official sources, observe robots.txt, and never bypass access controls}
::RULE{Do not invent offers, prices, discounts, validity dates, affiliate relationships, or traffic}
::RULE{If no verified deal exists, show an honest empty state and preserve provider information}
::RULE{Keep the generated site static; no runtime API, server, inference, or secret key}
::BOUNDARY{never:fabricate data scrape disallowed areas inject cookies manipulate traffic|scope:permanent}
