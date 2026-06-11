#!/usr/bin/env python3
"""
build.py — reads trackers.csv and generates index.html
Usage: python build.py
"""

import csv
import html
import os
from datetime import date

CSV_FILE = "trackers.csv"
OUT_FILE = "index.html"
CATEGORICAL_THRESHOLD = 10


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = list(reader.fieldnames)
    return columns, rows


def classify_columns(columns, rows):
    kinds = {}
    for col in columns:
        if col == "URL":
            kinds[col] = "hidden"
            continue
        unique = set(r.get(col, "").strip() for r in rows if r.get(col, "").strip())
        kinds[col] = "dropdown" if len(unique) <= CATEGORICAL_THRESHOLD else "text"
    return kinds


def build_header_row(columns):
    cells = "".join(f"<th>{html.escape(col)}</th>" for col in columns)
    return f"<tr>{cells}</tr>"


def build_data_row(columns, row):
    cells = []
    for col in columns:
        val = row.get(col, "")
        if col == "Name" and "URL" in row and row["URL"].strip():
            content = f'<a href="{html.escape(row["URL"].strip())}" target="_blank" rel="noopener">{html.escape(val)}</a>'
        else:
            content = html.escape(val)
        cells.append(f"<td>{content}</td>")
    return "<tr>" + "".join(cells) + "</tr>"


def build_column_filters(columns, rows, kinds):
    filter_cells = []
    js_bindings = []

    for i, col in enumerate(columns):
        kind = kinds.get(col, "text")
        if kind == "hidden":
            filter_cells.append("<th></th>")
            continue

        if kind == "dropdown":
            unique = sorted(
                set(r.get(col, "").strip() for r in rows if r.get(col, "").strip())
            )
            options = '<option value="">— all —</option>' + "".join(
                f'<option value="{html.escape(v)}">{html.escape(v)}</option>'
                for v in unique
            )
            fid = f"col-filter-{i}"
            filter_cells.append(
                f'<th><select id="{fid}" class="col-filter col-filter-select" data-col="{i}">'
                f"{options}</select></th>"
            )
            js_bindings.append(
                f"""
  document.getElementById('{fid}').addEventListener('change', function() {{
    table.column({i}).search(this.value ? '^' + escapeRegex(this.value) + '$' : '', true, false).draw();
  }});"""
            )
        else:
            fid = f"col-filter-{i}"
            filter_cells.append(
                f'<th><input type="text" id="{fid}" class="col-filter col-filter-text" '
                f'data-col="{i}" placeholder="filter…" autocomplete="off" /></th>'
            )
            js_bindings.append(
                f"""
  document.getElementById('{fid}').addEventListener('input', function() {{
    table.column({i}).search(this.value).draw();
  }});"""
            )

    filter_row = "<tr class='filter-row'>" + "".join(filter_cells) + "</tr>"
    js_block = "".join(js_bindings)
    return filter_row, js_block


def build_html(columns, rows):
    today = date.today().isoformat()
    kinds = classify_columns(columns, rows)

    header = build_header_row(columns)
    filter_row, js_filter_bindings = build_column_filters(columns, rows, kinds)
    body_rows = "\n".join(build_data_row(columns, row) for row in rows)

    url_col_index = columns.index("URL") if "URL" in columns else None
    hide_url_js = f"table.column({url_col_index}).visible(false);" if url_col_index is not None else ""

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Awesome Trackers</title>
  <link rel="stylesheet" href="https://cdn.datatables.net/2.0.8/css/dataTables.dataTables.min.css" />
  <link rel="stylesheet" href="style-dark.css" />
  <link rel="stylesheet" href="style-light.css" />
  <link rel="stylesheet" href="style.css" />
</head>
<body>

<header>
  <div class="header-text">
    <h1>🎯 Awesome Trackers</h1>
    <p class="author"><strong>Author</strong> Rodrigo J. Gonçalves</p>
    <p>A curated list of tools for 2D/3D object and trajectory tracking &mdash;
       <a href="https://github.com/rodrigo-j-goncalves/awesome-trackers">contribute on GitHub</a>
       &nbsp;|&nbsp; last updated: {today}
    </p>
  </div>
  <button id="theme-toggle" aria-label="Toggle light/dark theme">☀️ Light</button>
</header>

<main>
  <div id="search-box">
    <input type="text" id="global-search" placeholder="Search all columns…" autocomplete="off" />
    <button id="clear-btn">Clear all filters</button>
  </div>

  <table id="trackers" class="dataTable" style="width:100%">
    <thead>
      {header}
      {filter_row}
    </thead>
    <tbody>
{body_rows}
    </tbody>
  </table>
</main>

<footer>
  Generated from <code>trackers.csv</code> on {today} &mdash;
  <a href="https://github.com/rodrigo-j-goncalves/awesome-trackers">awesome-trackers</a>
</footer>

<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/2.0.8/js/dataTables.min.js"></script>
<script>
  function escapeRegex(s) {{
    return s.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
  }}

  const table = new DataTable('#trackers', {{
    pageLength: 25,
    orderCellsTop: true,
    fixedHeader: true,
    order: [],
    language: {{
      search: '',
      searchPlaceholder: 'Search…',
      info: '_START_–_END_ of _TOTAL_ tools',
      infoEmpty: '0 tools',
      infoFiltered: '(filtered from _MAX_)',
    }},
  }});

  {hide_url_js}

  document.getElementById('global-search').addEventListener('input', function () {{
    table.search(this.value).draw();
  }});

  {js_filter_bindings}

  document.getElementById('clear-btn').addEventListener('click', function () {{
    table.search('').columns().search('').draw();
    document.getElementById('global-search').value = '';
    document.querySelectorAll('.col-filter-text').forEach(el => el.value = '');
    document.querySelectorAll('.col-filter-select').forEach(el => el.selectedIndex = 0);
  }});

  document.querySelector('.dataTables_filter').style.display = 'none';

  // Theme toggle
  const root = document.documentElement;
  const btn = document.getElementById('theme-toggle');

  function applyTheme(theme) {{
    root.setAttribute('data-theme', theme);
    btn.textContent = theme === 'dark' ? '☀️ Light' : '🌙 Dark';
    localStorage.setItem('theme', theme);
  }}

  btn.addEventListener('click', function () {{
    applyTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  }});

  const saved = localStorage.getItem('theme');
  if (saved) applyTheme(saved);
</script>

</body>
</html>
"""


def main():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found. Run from the repo root.")
        return
    columns, rows = load_csv(CSV_FILE)
    html_out = build_html(columns, rows)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Built {OUT_FILE} — {len(rows)} rows, {len(columns)} columns.")


if __name__ == "__main__":
    main()
