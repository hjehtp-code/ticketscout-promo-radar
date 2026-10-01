"""Author durable original explanatory diagrams; no external dependencies."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
SLIDES = [
    ('legoland-ticket-check', 'Match the ticket to your visit',
     [('LOCATION', 'Florida and California are different resorts'),
      ('INCLUSIONS', 'Check the exact named parks on the ticket'),
      ('VISIT DATE', 'Check validity, exclusions and reservations')],
     'A resort name alone does not tell you what your ticket includes.'),
    ('legoland-date-check', 'A visible promotion can still be expired',
     [('BUY BY', 'When must the purchase be completed?'),
      ('VISIT BY', 'When must admission be used?'),
      ('CONFLICT?', 'Ask the provider before relying on the offer')],
     'Old BOGO terms ending August 16, 2026 do not prove a current deal.'),
    ('legoland-total-check', 'Compare the same party and the same day',
     [('ADMISSION', 'Use the same ages and included parks'),
      ('EXTRAS', 'Add required parking and separately sold items'),
      ('TOTAL', 'Compare confirmed totals before optional perks')],
     'Party total = admission + required extras + checkout charges'),
]

def main():
    out = ROOT / 'content' / 'assets'
    out.mkdir(parents=True, exist_ok=True)
    for slug, title, rows, note in SLIDES:
        body = []
        for i, (label, value) in enumerate(rows):
            y = 205 + i * 105
            body.append(f'<rect x="70" y="{y}" width="1060" height="85" rx="16" fill="#fff"/><text x="95" y="{y+35}" fill="#12634d" font-size="21" font-weight="700">{escape(label)}</text><text x="295" y="{y+50}" fill="#203d43" font-size="26">{escape(value)}</text>')
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675" role="img" aria-labelledby="title"><title id="title">{escape(title)}</title><rect width="1200" height="675" fill="#edf5f2"/><text x="70" y="80" font-family="Arial,sans-serif" font-size="22" fill="#12634d">TICKETSCOUT · TICKET CHECK</text><g font-family="Arial,sans-serif"><text x="70" y="150" font-size="42" font-weight="700" fill="#183c39">{escape(title)}</text>{"".join(body)}<text x="70" y="600" font-size="24" fill="#203d43">{escape(note)}</text></g></svg>'
        (out / (slug + '.svg')).write_text(svg, encoding='utf-8')
    print('Authored three ticket-check diagrams')

if __name__ == '__main__':
    main()
