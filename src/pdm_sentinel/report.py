"""Single-file HTML dashboard report, no web server or JS required."""
from __future__ import annotations

import html
from datetime import datetime, timezone

from .pipeline import PlantReport

_COLORS = {"Good": "#2e7d32", "Watch": "#f9a825", "Warning": "#ef6c00", "Critical": "#c62828"}


def _bar(score: float, grade: str) -> str:
    color = _COLORS[grade]
    return (
        f'<div style="background:#eee;border-radius:6px;height:18px;width:100%">'
        f'<div style="background:{color};width:{score:.0f}%;height:100%;border-radius:6px">'
        f'</div></div>'
    )


def render_html(report: PlantReport, title: str = "PdM Sentinel Report") -> str:
    esc = html.escape
    cards = []
    for m in report.machines:
        rows = "".join(
            f"<tr><td>{esc(s.name)}</td><td>{m.latest.get(s.name, float('nan')):.2f} "
            f"{esc(s.unit)}</td></tr>"
            for s in m.spec.sensors
        )
        cards.append(
            f'<div class="card"><h2>{esc(m.spec.display_name)}</h2>'
            f'<p class="grade" style="color:{_COLORS[m.health.grade]}">'
            f'{m.health.score:.0f}/100 - {esc(m.health.grade)}</p>'
            f'{_bar(m.health.score, m.health.grade)}'
            f'<table>{rows}</table></div>'
        )

    alert_rows = "".join(
        f'<tr class="{esc(a.severity)}"><td>{esc(a.severity.upper())}</td>'
        f"<td>{esc(a.timestamp[:19])}</td><td>{esc(a.message)}</td>"
        f"<td>{esc(a.kind)}</td></tr>"
        for a in sorted(report.alerts, key=lambda a: a.timestamp, reverse=True)
    ) or '<tr><td colspan="4">No active alerts.</td></tr>'

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{esc(title)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #222; }}
.cards {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
.card {{ border: 1px solid #ddd; border-radius: 10px; padding: 1rem; width: 300px; }}
.grade {{ font-weight: 700; margin: .2rem 0; }}
table {{ border-collapse: collapse; width: 100%; margin-top: .5rem; }}
td, th {{ border-bottom: 1px solid #eee; padding: .3rem .4rem; text-align: left; font-size: .9rem; }}
tr.critical td {{ color: #c62828; }} tr.warning td {{ color: #ef6c00; }}
footer {{ color: #888; font-size: .8rem; margin-top: 2rem; }}
</style></head>
<body>
<h1>{esc(title)}</h1>
<div class="cards">{''.join(cards)}</div>
<h2>Alerts</h2>
<table><tr><th>Severity</th><th>Time</th><th>Alert</th><th>Detector</th></tr>{alert_rows}</table>
<footer>Generated {generated} by pdm-sentinel.</footer>
</body></html>"""


def write_html(report: PlantReport, path: str, title: str = "PdM Sentinel Report") -> str:
    content = render_html(report, title)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path
