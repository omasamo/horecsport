"""Build the Horec Sport site from the archived pages in archive/.

    python3 tools/build.py

Writes index.html and stranky/*.html. Needs the `markdown` package.
"""
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "archive"
PAGES = ARCHIVE / "pages"
OUT = ROOT / "stranky"
WAYBACK_IMG = "https://web.archive.org/web/2023im_/http://horecsport.sk/"

# Friendly file names for the pages linked from the menu.
SLUGS = {
    "onas__onas": "o-nas",
    "onas__ktosme": "kto-sme",
    "onas__stanovy": "stanovy",
    "links": "uzitocne-linky",
    "dan": "dan-2-percenta",
    "nove_akcie": "archiv-akcii",
}
SKIP = {"index", "index_files__mainmenu", "index_files__index_left", "nove_akcie_index"}

REGIONS = [
    ("Slovenské hory", "Slovensko", "slovenske_hory__slovenske_hory", "index-slovenske_hory.jpg"),
    ("Alpy", "Rakúsko, Švajčiarsko, Taliansko, Francúzsko", "alpy__alpy", "index-alpy.jpg"),
    ("Himaláje", "Nepál", "himalaje__himalaje", "index-himalaje.jpg"),
    ("Kaukaz", "Gruzínsko, Rusko", "kaukaz__kaukaz", "index-kaukaz.jpg"),
    ("Mexiko", "Severná Amerika", "mexico__mexico", "index-mexico.jpg"),
    ("Rumunsko", "Retezat", "rumunsko__retezat__0", "index-rumunsko.jpg"),
    ("Guatemala", "Stredná Amerika", "guatemala__vt", None),
    ("Thajsko", "Ázia", "thajsko__vt", None),
    ("Jordánsko", "Blízky východ", "jordansko__vt", None),
]

NAV = [
    ("Domov", "index.html"),
    ("O nás", "stranky/o-nas.html"),
    ("Expedície", "index.html#expedicie"),
    ("Archív akcií", "stranky/archiv-akcii.html"),
    ("Linky", "stranky/uzitocne-linky.html"),
    ("Daň 2 %", "stranky/dan-2-percenta.html"),
    ("Kontakt", "index.html#kontakt"),
]


def slug(stem):
    return SLUGS.get(stem, stem.replace("__", "-").replace("_", "-"))


def load_titles():
    titles = {}
    for line in (ARCHIVE / "trips.md").read_text().splitlines():
        m = re.match(r"\| (\d{4}) \| (.+?) \| (.*?) \| \[.*?\]\(pages/(.+?)\.md\)", line)
        if m:
            titles[m.group(4)] = (m.group(2).strip(), f"{m.group(1)} · {m.group(3).strip()}")
    for name, sub, stem, _ in REGIONS:
        titles.setdefault(stem, (name, sub))
    titles.update({
        "onas__onas": ("O nás", "Kto sme"),
        "onas__ktosme": ("Kto sme", "Členovia klubu"),
        "onas__stanovy": ("Stanovy", "Výňatok zo stanov klubu"),
        "links": ("Užitočné linky", ""),
        "dan": ("Daň 2 %", "Podporte klub"),
        "nove_akcie": ("Archív akcií", "Text a foto z našich výstupov"),
    })
    return titles


def guess_title(md):
    for line in md.splitlines():
        line = re.sub(r"[*_#>\[\]]|\(.*?\)", "", line).strip()
        if line and not line.startswith("!") and line.lower() not in ("horecsport", "horecsport home page", "links hst"):
            return line[:80]
    return "Horec Sport"


def clean(md):
    md = re.sub(r"^# .*\n", "", md, count=1)
    source = ""
    m = re.search(r"^> Zdroj: (\S+) — Wayback snapshot (\d+) \((\S+)\)\s*$", md, re.M)
    if m:
        source = m.group(3)
        md = md.replace(m.group(0), "")
    md = re.sub(r"^\[HorecSport Home Page\]\(index\.md\)\s*$", "", md, flags=re.M)
    md = re.sub(r"\]\(file:///[^)]*\)", "]()", md)
    md = re.sub(r"!\[Highslide JS\]", "![]", md)
    return md, source


def fix_links(body, prefix):
    def link(m):
        target = m.group(1)
        if target == "index.md":
            return f'href="{prefix}index.html"'
        stem = target[:-3]
        if (PAGES / target).exists() and stem not in SKIP:
            return f'href="{prefix}stranky/{slug(stem)}.html"'
        return f'href="{prefix}index.html"'
    body = re.sub(r'href="([^"/:]+\.md)"', link, body)
    body = body.replace('src="../images/', f'src="{prefix}archive/images/')
    body = re.sub(r'<a href="">(.*?)</a>', r"\1", body)
    body = body.replace("<img ", '<img loading="lazy" ')
    # runs of image-only paragraphs become a photo grid
    body = re.sub(
        r"(?:<p>\s*(?:<a [^>]*>)?<img [^>]*>(?:</a>)?\s*</p>\s*){2,}",
        lambda m: '<div class="photos">' + re.sub(r"</?p>", "", m.group(0)) + "</div>",
        body,
    )
    return body


def page(title, body, prefix, description="", body_class=""):
    nav = "\n      ".join(f'<a href="{prefix}{href}">{label}</a>' for label, href in NAV)
    return f"""<!doctype html>
<html lang="sk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description or 'Horec Sport Team – horolezecký klub z Bratislavy. Horám zdar!')}">
  <link rel="icon" href="{prefix}assets/logo.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Source+Sans+3:ital,wght@0,400;0,600;1,400;1,700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body class="{body_class}">
  <div class="scenery" aria-hidden="true">
    <div class="sky"></div>
    <svg class="range" data-depth="0.25" viewBox="0 0 1440 400" preserveAspectRatio="none">
      <path d="M0 400V240l60-30 40 20 70-90 30 30 50-60 60 80 40-20 80 70 70-100 40 40 60-70 90 110 60-30 70 50 80-90 50 40 70-60 90 100 60-40 70 40 60-50 50 30 90-40v280z"/>
    </svg>
    <svg class="range" data-depth="0.45" viewBox="0 0 1440 400" preserveAspectRatio="none">
      <path d="M0 400V270l90-60 30 20 80-120 40 50 30-30 90 120 60-40 50 30 90-150 30 40 40-20 110 140 50-20 90-110 40 50 50-30 120 140 80-60 60 40 100-100 110 60v230z"/>
      <path class="snow" d="M200 110l-30 46 18-6 12 14 14-20 16 8zM530 80l-32 52 20-8 12 16 16-22 18 10zM900 110l-28 44 16-6 14 14 12-18 16 6zM1340 130l-26 40 16-4 12 10 12-16 14 4z"/>
    </svg>
    <svg class="range" data-depth="0.7" viewBox="0 0 1440 400" preserveAspectRatio="none">
      <path d="M0 400V310l70-30 60-110 30 30 40-60 70 100 50-20 40 30 80-140 30 40 30-20 70 110 60-50 50 40 90-120 40 50 60-40 90 130 70-60 50 30 80-90 40 40 80-30 90-60 70 40v320z"/>
      <path class="snow" d="M230 140l-24 36 14-4 10 10 12-14 12 4zM510 120l-28 44 16-6 12 12 14-18 14 6zM940 140l-26 40 16-6 10 12 12-16 14 6z"/>
    </svg>
    <svg class="range line" data-depth="1" viewBox="0 0 1440 400" preserveAspectRatio="none">
      <path d="M0 400V340l220-120 90 70 120-90 230 170 160-110 200 120 170-90 250 80v330z"/>
      <path class="ridge" d="M0 340l220-120 90 70 120-90 230 170 160-110 200 120 170-90 250 80"/>
    </svg>
  </div>

  <header class="topbar">
    <a class="brand" href="{prefix}index.html">
      <img src="{prefix}assets/logo.svg" alt="" width="54" height="40">
      <span>Horec <b>Sport</b></span>
    </a>
    <button class="menu-toggle" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav id="nav">
      {nav}
    </nav>
  </header>

  <main>
{body}
  </main>

  <footer class="footer">
    <p>Horám zdar! · Občianske združenie Horec Sport Team · Sibírska 52, 831 02 Bratislava · <a href="mailto:info@horecsport.sk">info@horecsport.sk</a></p>
    <p class="small">Kopírovanie a šírenie je doporučené, ba až žiadúce.</p>
  </footer>

  <script src="{prefix}assets/main.js"></script>
</body>
</html>
"""


def thumb(file):
    return WAYBACK_IMG + "index_files/" + file


def news_items():
    md = (PAGES / "index.md").read_text()
    items = []
    pattern = (r"!\[\]\((\S+?aktuality/\S+?)\)\s+\*\*(.+?)\*\* pridané ([\d.]+)\s+(.+?)\s+"
               r"\[\.\.\.\.viacej na\.\.\.\]\((\S+?)\.md\)")
    for img, title, date, teaser, stem in re.findall(pattern, md, re.S):
        items.append((img, title, date, teaser.strip(" .\n").replace("\n", " "), stem))
    return items


def build_index(titles):
    regions = "\n".join(
        f'''        <a class="region" href="stranky/{slug(stem)}.html">
          <div class="region-img"{f' style="background-image:url({thumb(img)})"' if img else ''}></div>
          <span>{html.escape(sub)}</span><h3>{html.escape(name)}</h3>
        </a>'''
        for name, sub, stem, img in REGIONS
    )
    news = "\n".join(
        f'''        <a class="news" href="stranky/{slug(stem)}.html">
          <img loading="lazy" src="{img}" alt="">
          <div><span>pridané {date}</span><h3>{html.escape(title)}</h3><p>… {html.escape(teaser)} …</p></div>
        </a>'''
        for img, title, date, teaser, stem in news_items()
    )
    body = f"""    <section id="uvod" class="hero">
      <img class="hero-logo" src="assets/logo.svg" alt="Logo Horec Sport Team Slovakia">
      <div>
        <p class="tagline">Horám zdar …</p>
        <h1>Horec Sport Team</h1>
        <p class="lead">Partia kamarátov so záujmom o turistiku, horolezectvo, skialpinizmus, cyklistiku a ostatné športy spojené s prírodou a všeličo iné :-)</p>
        <a class="btn" href="#expedicie">Fotogalérie a túry</a>
      </div>
    </section>

    <section id="aktuality" class="panel">
      <h2>Aktuality a novinky</h2>
      <div class="news-list">
{news}
      </div>
      <p class="more">Záznamy z našich predchádzajúcich akcií sú v <a href="stranky/archiv-akcii.html">archíve akcií</a>.</p>
    </section>

    <section id="expedicie" class="panel">
      <h2>Fotogalérie a túry</h2>
      <div class="regions">
{regions}
      </div>
    </section>

    <section id="hory" class="panel">
      <h2>Počasie a podmienky na horách</h2>
      <div class="columns">
        <div>
          <h3>Slovensko</h3>
          <ul>
            <li><a href="http://www.hzs.sk/info/pocasieprehlad.php">Aktuálne počasie na horách (HZS)</a></li>
            <li><a href="http://www.hzs.sk/info/predpovedprehlad.php">Predpoveď počasia pre hory (HZS)</a></li>
            <li><a href="http://www.shmu.sk/?page=107">Predpoveď počasia pre V. Tatry (SHMÚ)</a></li>
            <li><a href="http://www.hzs.sk/info/podmienkyprehlad.php">Podmienky na túry</a></li>
            <li><a href="http://www.hzs.sk/info/lavinyprehlad.php">Lavínová situácia (HZS)</a></li>
          </ul>
        </div>
        <div>
          <h3>Zahraničie</h3>
          <ul>
            <li><a href="http://www.wetter.at/">Počasie v Rakúsku</a></li>
            <li><a href="http://www.wetteronline.de/">Wetteronline</a></li>
            <li><a href="http://www.yr.no/place/Slovakia/Other/Gerlach/">Nórsky server (Gerlach)</a></li>
            <li><a href="http://www.mountain-forecast.com/">Mountain Forecast</a></li>
            <li><a href="http://www.summitpost.org/">Summitpost</a></li>
          </ul>
        </div>
        <div>
          <h3>Užitočné</h3>
          <ul>
            <li><a href="http://www.tatry.nfo.sk/">Horolezecký sprievodca Vysoké Tatry</a></li>
            <li><a href="http://www.james.sk/">Horolezecký spolok James</a></li>
            <li><a href="http://www.hzs.sk">Horská záchranná služba</a></li>
            <li><a href="http://www.hory.sk">Hory.sk</a></li>
            <li><a href="stranky/uzitocne-linky.html">Všetky linky →</a></li>
          </ul>
        </div>
      </div>
    </section>

    <section id="kontakt" class="panel">
      <h2>Kontakt</h2>
      <div class="columns">
        <div>
          <h3>Občianske združenie Horec Sport Team</h3>
          <p>Sibírska 52<br>831 02 Bratislava<br>IČO 30793670<br>
            <a href="mailto:info@horecsport.sk">info@horecsport.sk</a></p>
          <p><a href="stranky/dan-2-percenta.html">Podporte nás 2 % z dane</a></p>
        </div>
        <div class="service">
          <h3>Horecsport ponúka a vykonáva</h3>
          <p><strong>výškové práce, zrezávanie stromov</strong></p>
          <p>Ivo Janovič<br>
            <a href="tel:+421905273736">0905 273 736</a><br>
            <a href="mailto:ivo.janovic@gmail.com">ivo.janovic@gmail.com</a></p>
        </div>
      </div>
    </section>"""
    (ROOT / "index.html").write_text(page("Horec Sport Team – horolezecký klub", body, "", body_class="home"))


def build_archive():
    """Archív akcií: trips grouped by year, with the thumbnails from the old page."""
    md = (PAGES / "nove_akcie.md").read_text()
    year, groups = None, {}
    pattern = r"\*\*(\d{4})\*\*|!\[\]\((\S+)\)\s+((?:\[[^\]]*\]\(\S+?\.md\)\s*)+)\s*((?:\*\*.+?\*\* ?)+)"
    for y, img, links, place in re.findall(pattern, md):
        if y:
            year = y
            continue
        parts = re.findall(r"\[([^\]]*)\]\((\S+?)\.md\)", links)
        title, stem = "".join(t for t, _ in parts).strip(), parts[0][1]
        place = re.sub(r"\*\*", "", place).strip().rstrip(",")
        groups.setdefault(year, []).append((img, title, stem, place))
    sections = []
    for year, trips in groups.items():
        cards = "\n".join(
            f'''          <a class="news" href="{slug(stem)}.html">
            <img loading="lazy" src="{img}" alt="">
            <div><span>{html.escape(place)}</span><h3>{html.escape(title)}</h3></div>
          </a>'''
            for img, title, stem, place in trips
            if (PAGES / f"{stem}.md").exists()
        )
        if cards:
            sections.append(f'      <h2 class="year">{year}</h2>\n      <div class="news-list">\n{cards}\n      </div>')
    body = f"""    <article class="panel visible article">
      <p class="crumbs"><a href="../index.html">Domov</a></p>
      <h1>Archív akcií</h1>
      <p class="subtitle">Výber z našich akcií, kedy sme neboli leniví to aj zaznamenať na webe :)</p>
{chr(10).join(sections)}
    </article>"""
    (OUT / "archiv-akcii.html").write_text(page("Archív akcií – Horec Sport", body, "../", body_class="inner"))
    return sum(len(t) for t in groups.values())


def build_pages(titles):
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.html"):
        old.unlink()
    count = 0
    for path in sorted(PAGES.glob("*.md")):
        stem = path.stem
        if stem in SKIP:
            continue
        md, source = clean(path.read_text())
        title, sub = titles.get(stem, (guess_title(md), ""))
        body_html = markdown.markdown(md, extensions=["tables"])
        body_html = fix_links(body_html, "../")
        src = f'<p class="source">Pôvodná stránka: <a href="{source}">archív horecsport.sk</a></p>' if source else ""
        body = f"""    <article class="panel visible article">
      <p class="crumbs"><a href="../index.html">Domov</a> › <a href="archiv-akcii.html">Archív akcií</a></p>
      <h1>{html.escape(title)}</h1>
      {f'<p class="subtitle">{html.escape(sub)}</p>' if sub else ''}
      <div class="prose">
{body_html}
      </div>
      {src}
    </article>"""
        (OUT / f"{slug(stem)}.html").write_text(page(f"{title} – Horec Sport", body, "../", body_class="inner"))
        count += 1
    return count


if __name__ == "__main__":
    titles = load_titles()
    build_index(titles)
    n = build_pages(titles)
    trips = build_archive()
    print(f"index.html + {n} pages in stranky/, {trips} trips in the archive")
