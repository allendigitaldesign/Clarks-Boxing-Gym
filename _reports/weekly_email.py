"""Builds the Monday website report email in the "Ringside" design.

The weekly report task gathers the numbers, writes them to a JSON file shaped
like sample-week.json, then runs:

    python3 _reports/weekly_email.py week.json --html > email.html
    python3 _reports/weekly_email.py week.json --text > email.txt

Every chart is built from plain HTML tables with inline styles, so it shows in
Gmail, Apple Mail and Outlook without images or scripts.

Two rules come from the Gmail connector that sends this email. It strips the
`background:` shorthand (so use `background-color:` only) and it removes any
<img> that isn't an attached file (so the email has no pictures). Breaking
either rule makes the charts and the red boxes vanish in the inbox.

This folder starts with an underscore, so GitHub Pages does not publish it.
"""
import json
import sys
from html import escape

# ---------- Website colors and fonts (css/styles.css) ----------
RED = "#d62828"
BLACK = "#0f0f0f"
INK = "#1a1a1a"
GREY = "#5c5c5c"
LINE = "#e4e4e4"
PAPER = "#f5f4f2"
GOOD = "#1d6b35"
WARN = "#b7791f"
MUTED = "#c9c9c9"
HEAD = "Oswald,'Arial Narrow',Arial,sans-serif"
BODY = "Barlow,Helvetica,Arial,sans-serif"
ADDRESS = "601 S. 2nd Street, Killeen, TX 76541 &middot; (254) 216-1634"
FOOTER = ("Numbers are anonymous and run a little low because some visitors use ad blockers. "
          "No individual visitors can be identified.")


def e(s):
    return escape(str(s), quote=True)


def mmss(sec):
    sec = int(round(sec))
    return f"{sec // 60}:{sec % 60:02d}"


def visit_len(sec):
    sec = int(round(sec))
    if sec < 60:
        return f"{sec} sec"
    m, s = divmod(sec, 60)
    return f"{m} min {s} sec" if s else f"{m} min"


def num(v):
    return f"{v:g}" if isinstance(v, float) else str(v)


def pct(v, mx):
    if not v or not mx:
        return 0
    return max(2, min(100, round(100 * v / mx)))


def T(inner, style=""):
    st = f' style="{style}"' if style else ""
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"{st}>{inner}</table>'


# ---------- Chart pieces ----------
def bar(p, color, h=12):
    cell = f'height:{h}px;font-size:0'
    if p <= 0:
        return T(f'<tr><td style="background-color:{LINE};{cell};border-radius:3px">&nbsp;</td></tr>')
    if p >= 100:
        return T(f'<tr><td style="background-color:{color};{cell};border-radius:3px">&nbsp;</td></tr>')
    return T(f'<tr><td width="{p}%" style="background-color:{color};{cell};border-radius:3px 0 0 3px">&nbsp;</td>'
             f'<td style="background-color:{LINE};{cell};border-radius:0 3px 3px 0">&nbsp;</td></tr>')


def hbars(rows, color=RED, fmt=num, mx=None, label_w=34):
    """rows: list of (label_html, value, note). One line each: label, bar, value."""
    if not rows:
        return ""
    mx = mx or max(r[1] for r in rows) or 1
    out = ""
    for label, v, note in rows:
        sub = f'<div style="font-size:12px;color:{GREY};line-height:1.3">{note}</div>' if note else ""
        out += (f'<tr><td width="{label_w}%" style="padding:7px 10px 7px 0;font-size:15px;'
                f'color:{INK};line-height:1.25;vertical-align:middle">{label}{sub}</td>'
                f'<td style="padding:7px 0;vertical-align:middle">{bar(pct(v, mx), color)}</td>'
                f'<td width="64" align="right" style="padding:7px 0 7px 10px;font-family:{HEAD};font-size:16px;'
                f'font-weight:600;color:{INK};white-space:nowrap;vertical-align:middle">{fmt(v)}</td></tr>')
    return T(out)


def columns(days, h=110):
    mx = max((v for _, v in days), default=0) or 1
    top = bottom = ""
    w = 100 // max(1, len(days))
    for d, v in days:
        ph = max(3, round(h * v / mx)) if v else 0
        top += (f'<td valign="bottom" align="center" width="{w}%" style="padding:0 5px;height:{h + 26}px">'
                f'<div style="font-family:{HEAD};font-size:15px;font-weight:600;color:{INK};line-height:20px">{v}</div>'
                f'<div style="height:{ph}px;background-color:{RED};border-radius:3px 3px 0 0;font-size:0">&nbsp;</div></td>')
        bottom += (f'<td align="center" style="padding:6px 0 0;border-top:2px solid {LINE};font-family:{HEAD};'
                   f'font-size:12px;letter-spacing:1px;text-transform:uppercase;color:{GREY}">{e(d)}</td>')
    return T(f"<tr>{top}</tr><tr>{bottom}</tr>")


def stacked(parts, h=22):
    vis = [(v, c) for v, c in parts if v]
    total = sum(v for v, _ in vis)
    if not total:
        return T(f'<tr><td style="background-color:{LINE};height:{h}px;font-size:0;border-radius:4px">&nbsp;</td></tr>')
    cells = ""
    for i, (v, c) in enumerate(vis):
        if len(vis) == 1:
            r = "4px"
        elif i == 0:
            r = "4px 0 0 4px"
        elif i == len(vis) - 1:
            r = "0 4px 4px 0"
        else:
            r = "0"
        cells += (f'<td width="{round(100 * v / total)}%" style="background-color:{c};height:{h}px;font-size:0;'
                  f'line-height:0;border-radius:{r}">&nbsp;</td>')
    return T(f"<tr>{cells}</tr>")


def legend(items):
    cells = "".join(
        f'<td style="padding:8px 14px 0 0;font-size:14px;color:{GREY};white-space:nowrap">'
        f'<span style="display:inline-block;width:10px;height:10px;background-color:{c};border-radius:2px;'
        f'margin-right:6px;vertical-align:middle"></span>{e(label)}</td>' for label, c in items)
    return f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>{cells}</tr></table>'


# ---------- Layout pieces ----------
def eyebrow(t):
    return (f'<div style="font-family:{HEAD};font-size:12px;letter-spacing:3px;text-transform:uppercase;'
            f'color:{RED};font-weight:500">{e(t)}</div>')


def h2(title, small):
    return (eyebrow(small) +
            f'<div style="font-family:{HEAD};font-size:24px;line-height:1.1;text-transform:uppercase;'
            f'font-weight:600;color:{INK};margin:4px 0 14px">{e(title)}</div>')


def h3(t, top=20):
    return (f'<div style="font-family:{HEAD};font-size:13px;letter-spacing:2px;text-transform:uppercase;'
            f'color:{INK};margin:{top}px 0 4px">{e(t)}</div>')


def note(t, top=6):
    return f'<div style="font-size:13px;color:{GREY};margin-top:{top}px;line-height:1.45">{t}</div>'


def para(t):
    return f'<div style="font-size:15px;color:{INK};line-height:1.5;margin-bottom:6px">{t}</div>'


def sect(inner, top=28):
    return f'<tr><td class="pad" style="padding:{top}px 32px 4px;background-color:#ffffff">{inner}</td></tr>'


def rule():
    return (f'<tr><td class="pad" style="padding:24px 32px 0;background-color:#ffffff">'
            f'<div style="border-top:1px solid {LINE};font-size:0">&nbsp;</div></td></tr>')


def compare(now, before, fmt, unit):
    if before is None:
        return "Comparison starts next week"
    d = round(now - before)
    if d > 0:
        arrow = f'<span style="color:{GOOD}">&#9650; {d}{unit}</span> &nbsp;'
    elif d < 0:
        arrow = f'<span style="color:{RED}">&#9660; {-d}{unit}</span> &nbsp;'
    else:
        arrow = "Same as "
    return f"{arrow}Last week {fmt(before)}"


def tile(label, pair, fmt=num, unit=""):
    now, before = pair.get("this"), pair.get("last")
    if now is None:
        return '<td width="50%"></td>'
    return (f'<td width="50%" style="padding:6px;vertical-align:top">'
            f'<div style="background-color:{PAPER};border-radius:6px;padding:14px 16px">'
            f'<div style="font-family:{HEAD};font-size:12px;letter-spacing:2px;text-transform:uppercase;color:{GREY}">{e(label)}</div>'
            f'<div style="font-family:{HEAD};font-size:36px;line-height:1.1;font-weight:600;color:{INK}">{fmt(now)}</div>'
            f'<div style="font-size:13px;color:{GREY}">{compare(now, before, fmt, unit)}</div>'
            f'</div></td>')


# ---------- The email ----------
def render_html(d):
    v = d.get("visitors")          # None when the visitor numbers couldn't be reached

    head = (f'<tr><td style="background-color:{BLACK};padding:18px 24px">'
            + T(f'<tr><td width="60" style="vertical-align:middle"><div style="width:52px;height:52px;border-radius:50%;'
                f'background-color:{RED};color:#ffffff;font-family:{HEAD};font-size:20px;font-weight:600;'
                f'line-height:52px;text-align:center;letter-spacing:1px">CB</div></td>'
                f'<td style="vertical-align:middle;padding-left:12px"><div style="font-family:{HEAD};font-size:20px;'
                f'letter-spacing:1px;text-transform:uppercase;color:#ffffff;font-weight:600;line-height:1">Clark\'s Boxing Club</div>'
                f'<div style="font-family:{HEAD};font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#bdbdbd;'
                f'margin-top:5px">Weekly website report</div></td>'
                f'<td align="right" style="vertical-align:middle;font-family:{HEAD};font-size:14px;letter-spacing:1px;'
                f'text-transform:uppercase;color:#ffffff;white-space:nowrap">{e(d["range"])}</td></tr>')
            + f'</td></tr><tr><td style="background-color:{RED};height:4px;font-size:0">&nbsp;</td></tr>')

    period = note(e(d["period_note"]), 2) if d.get("period_note") else ""
    lines = "".join(
        f'<div style="font-size:16px;line-height:1.5;color:{INK};padding:2px 0 2px 16px;'
        f'border-left:3px solid {RED};margin-bottom:6px">{e(l)}</div>' for l in d["lines"])
    intro = sect(eyebrow("This week")
                 + f'<div style="font-family:{HEAD};font-size:32px;line-height:1.05;text-transform:uppercase;'
                   f'font-weight:600;color:{INK};margin:6px 0 12px">{e(d["headline"])}</div>'
                 + lines + period, 30)

    do = (f'<tr><td class="pad" style="padding:18px 32px 0;background-color:#ffffff">'
          f'<div style="background-color:{RED};border-radius:6px;padding:18px 20px">'
          f'<div style="font-family:{HEAD};font-size:14px;letter-spacing:3px;text-transform:uppercase;color:#ffffff;'
          f'font-weight:600">Do this week</div>'
          f'<div style="font-size:16px;line-height:1.5;color:#ffffff;margin-top:6px">{e(d["do_this_week"])}</div>'
          f'</div></td></tr>')

    # Website health
    h = d["health"]
    good, attn = h.get("working", []), h.get("attention", [])
    total = len(good) + len(attn)
    ticks = "".join(
        f'<tr><td width="28" style="padding:5px 0;vertical-align:top"><div style="width:20px;height:20px;border-radius:50%;'
        f'background-color:{GOOD};color:#ffffff;font-size:12px;line-height:20px;text-align:center;font-family:Arial,sans-serif">'
        f'&#10003;</div></td><td style="padding:5px 0;font-size:15px;color:{INK}">{e(g)}</td></tr>'
        for g in good)
    if attn:
        attn_html = "".join(
            f'<div style="background-color:#fff8ec;border:1px solid #f1dcb2;border-radius:6px;padding:12px 14px;margin-top:8px;'
            f'font-size:15px;color:{INK};line-height:1.45"><b style="color:{WARN}">&#9679;</b> '
            f'{e(a["problem"])}<br><b>Next step:</b> {e(a["next_step"])}</div>' for a in attn)
    else:
        attn_html = para("Nothing this week.")
    health = sect(h2("Website health", f"{len(good)} of {total} checks passed" if total else "Checks")
                  + (stacked([(len(good), GOOD), (len(attn), WARN)], 10) + '<div style="height:14px"></div>' if total else "")
                  + T(ticks) + h3("Needs attention", 16) + attn_html
                  + (note(f'<b>Not checked this week:</b> {e(h["not_checked"])}', 12) if h.get("not_checked") else ""))

    body = head + intro + do

    if not v:
        body += sect(f'<div style="background-color:{PAPER};border-radius:6px;padding:14px 16px;'
                     f'font-size:15px;color:{INK}"><b>Visitor numbers are missing this week.</b> '
                     f'They could not be reached when this report ran. The health checks below still ran.</div>', 22)
        body += rule() + health
    else:
        tiles = sect(h2("Visitors at a glance", "This week vs. last week")
                     + T(f'<tr>{tile("People", v["people"])}{tile("Visits", v["visits"])}</tr>'
                         f'<tr>{tile("Page views", v["page_views"])}'
                         f'{tile("A typical visit", v["typical_visit_sec"], visit_len, " sec")}</tr>', "margin:0 -6px")
                     + (note(e(v["visitors_note"]), 8) if v.get("visitors_note") else ""))
        body += tiles

        if v.get("days"):
            body += sect(h2("Visits by day", d.get("days_label", "Mon to Sun"))
                         + columns([(x["day"], x["visits"]) for x in v["days"]])
                         + (note(e(v["days_note"]), 10) if v.get("days_note") else ""))

        body += rule() + health

        sp = v.get("speed")
        if sp and (sp.get("phone_sec") is not None or sp.get("computer_sec") is not None):
            rows = [(n, sp[k], None) for n, k in (("Phones", "phone_sec"), ("Computers", "computer_sec")) if sp.get(k) is not None]
            body += sect(h2("How fast the site opens", "Real visitors")
                         + hbars(rows, GOOD, lambda s: f"{s:g} sec", mx=max(4, *[r[1] for r in rows]))
                         + note("Under 2.5 seconds is fast. Bars run from 0 to 4 seconds."), 24)

        if v.get("clicks"):
            body += rule() + sect(h2("What people tapped", "Calls, trials and messages")
                                  + hbars([(e(c["label"]), c["count"], e(c.get("where", ""))) for c in v["clicks"]], label_w=46))

        att = ""
        if v.get("sections"):
            att += hbars([(e(s["name"]), s["seconds"], e(s["page"]) + " page") for s in v["sections"]],
                         INK, mmss, label_w=46) + note("Minutes:seconds, all visitors combined.", 2)
        if v.get("pages"):
            att += h3("Pages viewed") + hbars([(e(p["page"]), p["views"], None) for p in v["pages"]])
        if v.get("scroll"):
            att += h3("How far down people scrolled") + hbars(
                [(e(s["page"]), s["percent"], None) for s in v["scroll"]], fmt=lambda p: f"{p:g}%", mx=100)
        if v.get("exits"):
            att += h3("Where visits ended") + hbars([(e(x["page"]), x["visits"], None) for x in v["exits"]], "#8d8d8d")
        if att:
            body += rule() + sect(h2("What held attention", "Time spent on each section") + att)

        who = ""
        dev = v.get("devices")
        if dev:
            ph, pc, tb = dev.get("phones", 0), dev.get("computers", 0), dev.get("tablets", 0)
            n = ph + pc + tb
            who += (para(f"<b>{ph} of {n}</b> used a phone")
                    + stacked([(ph, RED), (pc, INK), (tb, "#8d8d8d")])
                    + legend([(f"Phones {ph}", RED), (f"Computers {pc}", INK), (f"Tablets {tb}", "#8d8d8d")]))
        loc = v.get("location")
        if loc:
            near, tot = loc["killeen_area"], loc["total"]
            who += ('<div style="height:18px"></div>' + para(f"<b>{near} of {tot}</b> were from the Killeen area")
                    + stacked([(near, RED), (tot - near, MUTED)])
                    + legend([(f"Killeen area {near}", RED), (f"Elsewhere {tot - near}", MUTED)])
                    + note("Killeen area means Killeen, Fort Cavazos, Harker Heights, Copperas Cove and Temple."))
            if loc.get("top_cities"):
                who += note("<b>Top cities:</b> " + e(", ".join(f'{c["city"]} {c["people"]}' for c in loc["top_cities"])) + ".", 4)
        if v.get("sources"):
            who += h3("How they found the site") + hbars(
                [(e(s["source"]), s["people"], None) for s in v["sources"]], label_w=42)
            who += note("A person can be counted more than once.")
        if who:
            body += rule() + sect(h2("Who visited", "Devices, places and sources") + who)

    extra = f" {e(d['footer_note'])}" if d.get("footer_note") else ""
    body += (f'<tr><td style="height:32px;background-color:#ffffff;font-size:0">&nbsp;</td></tr>'
             f'<tr><td class="pad" style="background-color:{BLACK};padding:26px 32px;text-align:center">'
             f'<div style="font-family:{HEAD};font-size:16px;letter-spacing:2px;text-transform:uppercase;color:#ffffff">Clark\'s Boxing Club</div>'
             f'<div style="font-size:14px;color:#bdbdbd;margin-top:6px">{ADDRESS}</div>'
             f'<div style="font-size:12px;line-height:1.5;color:#8d8d8d;margin-top:14px">{FOOTER}{extra}</div></td></tr>')

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light only">
<title>Clark's Boxing website report</title>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&amp;family=Oswald:wght@500;600&amp;display=swap" rel="stylesheet">
<style>body{{margin:0;padding:0}} @media (max-width:480px){{.pad{{padding-left:18px!important;padding-right:18px!important}}}}</style>
</head>
<body style="margin:0;padding:0;background-color:{PAPER}">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{e(d.get("preview_text", ""))}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{PAPER}"><tr><td align="center" style="font-family:{BODY}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:620px;border-collapse:collapse">
{body}
</table></td></tr></table></body></html>"""


def render_text(d):
    v = d.get("visitors")
    out = [f"CLARK'S BOXING WEBSITE REPORT: {d['range']}", ""]
    if d.get("period_note"):
        out += [d["period_note"], ""]
    out += ["THIS WEEK"] + [f"- {l}" for l in d["lines"]] + ["", f"DO THIS WEEK: {d['do_this_week']}", ""]
    if not v:
        out += ["Visitor numbers are missing this week. The health checks still ran.", ""]
    else:
        def row(label, pair, fmt=num):
            last = "comparison starts next week" if pair.get("last") is None else f"last week {fmt(pair['last'])}"
            return f"- {label}: {fmt(pair['this'])} ({last})"
        out += ["VISITORS", row("People", v["people"]), row("Visits", v["visits"]),
                row("Page views", v["page_views"]), row("A typical visit", v["typical_visit_sec"], visit_len)]
        if v.get("visitors_note"):
            out.append(v["visitors_note"])
        if v.get("days"):
            out.append("Visits by day: " + ", ".join(f'{x["day"]} {x["visits"]}' for x in v["days"]))
        out.append("")
    h = d["health"]
    out += ["WEBSITE HEALTH", "Working well:"] + [f"- {g}" for g in h.get("working", [])] + ["Needs attention:"]
    out += [f"- {a['problem']} Next step: {a['next_step']}" for a in h.get("attention", [])] or ["- Nothing this week."]
    if h.get("not_checked"):
        out.append(f"Not checked this week: {h['not_checked']}")
    out.append("")
    if v:
        sp = v.get("speed") or {}
        if sp.get("phone_sec") is not None or sp.get("computer_sec") is not None:
            out += [f"Speed: phones {sp.get('phone_sec', '?')} sec, computers {sp.get('computer_sec', '?')} sec. Under 2.5 is fast.", ""]
        if v.get("clicks"):
            out += ["WHAT PEOPLE TAPPED"] + [f"- {c['label']}: {c['count']}" + (f" ({c['where']})" if c.get("where") else "")
                                           for c in v["clicks"]] + [""]
        if v.get("sections"):
            out += ["WHAT HELD ATTENTION (total time)"] + [f"- {s['name']}, {s['page']} page: {mmss(s['seconds'])}"
                                                         for s in v["sections"]]
        if v.get("pages"):
            out.append("Pages viewed: " + ", ".join(f'{p["page"]} {p["views"]}' for p in v["pages"]))
        if v.get("scroll"):
            out.append("How far people scrolled: " + ", ".join(f'{s["page"]} {s["percent"]:g}%' for s in v["scroll"]))
        if v.get("exits"):
            out.append("Where visits ended: " + ", ".join(f'{x["page"]} {x["visits"]}' for x in v["exits"]))
        out.append("")
        out.append("WHO VISITED")
        dev = v.get("devices")
        if dev:
            out.append(f"- Phones {dev.get('phones', 0)}, computers {dev.get('computers', 0)}, tablets {dev.get('tablets', 0)}")
        loc = v.get("location")
        if loc:
            out.append(f"- {loc['killeen_area']} of {loc['total']} were from the Killeen area")
            if loc.get("top_cities"):
                out.append("- Top cities: " + ", ".join(f'{c["city"]} {c["people"]}' for c in loc["top_cities"]))
        if v.get("sources"):
            out.append("- How they found the site (a person can be counted more than once): "
                       + ", ".join(f'{s["source"]} {s["people"]}' for s in v["sources"]))
        out.append("")
    out.append(FOOTER + (f" {d['footer_note']}" if d.get("footer_note") else ""))
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in ("--html", "--text"):
        sys.exit("usage: python3 _reports/weekly_email.py week.json --html|--text")
    with open(sys.argv[1]) as f:
        data = json.load(f)
    sys.stdout.write(render_html(data) if sys.argv[2] == "--html" else render_text(data))
