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
CATEGORICAL_THRESHOLD = 10  # columns with <= this many unique values get a dropdown


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = list(reader.fieldnames)
    return columns, rows


def classify_columns(columns, rows):
    """Return dict: col -> 'dropdown' | 'text' | 'hidden'"""
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
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Awesome Trackers</title>
  <link rel="stylesheet" href="https://cdn.datatables.net/2.0.8/css/dataTables.dataTables.min.css" />
  <style>
    /* === Solarized Dark palette ===
       base03 #002b36  darkest bg
       base02 #073642  surface
       base01 #586e75  subtle content
       base00 #657b83  muted
       base0  #839496  body text
       base1  #93a1a1  emphasis
       base2  #eee8d5  (unused)
       base3  #fdf6e3  (unused)
       yellow #b58900  accent warm
       cyan   #2aa198  accent cool
       blue   #268bd2  links
       green  #859900
       red    #dc322f
    */

    *, *::before, *::after {{ box-sizing: border-box; }}

    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: 15px;
      line-height: 1.6;
      margin: 0;
      padding: 0;
      background: #002b36;
      color: #839496;
    }}

    header {{
      background: #073642;
      color: #93a1a1;
      padding: 2rem 2.5rem 1.5rem;
      border-bottom: 3px solid #2aa198;
    }}

    header h1 {{
      margin: 0 0 0.25rem;
      font-size: 1.8rem;
      font-weight: 600;
      letter-spacing: -0.02em;
      color: #eee8d5;
    }}

    header p {{
      margin: 0;
      font-size: 0.9rem;
      color: #586e75;
    }}

    header a {{
      color: #268bd2;
      text-decoration: none;
    }}

    header a:hover {{ color: #2aa198; text-decoration: underline; }}

    main {{
      padding: 2rem 2.5rem;
      max-width: 1400px;
      margin: 0 auto;
    }}

    #search-box {{
      margin-bottom: 1.25rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }}

    #search-box input {{
      width: 100%;
      max-width: 420px;
      padding: 0.5rem 0.85rem;
      font-size: 14px;
      border: 1px solid #586e75;
      border-radius: 6px;
      background: #073642;
      color: #93a1a1;
      outline: none;
      transition: border-color 0.15s;
    }}

    #search-box input::placeholder {{ color: #586e75; }}
    #search-box input:focus {{ border-color: #2aa198; }}

    #clear-btn {{
      padding: 0.5rem 1rem;
      font-size: 13px;
      border: 1px solid #586e75;
      border-radius: 6px;
      background: #073642;
      color: #839496;
      cursor: pointer;
      transition: border-color 0.15s, color 0.15s;
    }}

    #clear-btn:hover {{ border-color: #2aa198; color: #93a1a1; }}

    /* Override DataTables defaults */
    .dataTables_wrapper {{ color: #839496; }}

    table.dataTable {{
      width: 100% !important;
      border-collapse: collapse;
      background: #073642;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }}

    table.dataTable thead th {{
      background: #002b36;
      color: #93a1a1;
      font-weight: 500;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid #073642;
      cursor: pointer;
      white-space: nowrap;
    }}

    table.dataTable thead th:hover {{ background: #073642; color: #eee8d5; }}

    /* DataTables sort arrows — restyle for dark bg */
    table.dataTable thead th.dt-orderable-asc span.dt-column-order::before,
    table.dataTable thead th.dt-orderable-desc span.dt-column-order::after {{
      color: #586e75;
    }}

    tr.filter-row th {{
      background: #073642;
      padding: 0.4rem 0.5rem;
      border-bottom: 2px solid #2aa198;
    }}

    .col-filter-text {{
      width: 100%;
      padding: 0.3rem 0.5rem;
      font-size: 12px;
      border: 1px solid #586e75;
      border-radius: 4px;
      background: #002b36;
      color: #839496;
      outline: none;
    }}

    .col-filter-text::placeholder {{ color: #586e75; }}
    .col-filter-text:focus {{ border-color: #2aa198; }}

    .col-filter-select {{
      width: 100%;
      padding: 0.3rem 0.4rem;
      font-size: 12px;
      border: 1px solid #586e75;
      border-radius: 4px;
      background: #002b36;
      color: #839496;
      outline: none;
      cursor: pointer;
    }}

    .col-filter-select:focus {{ border-color: #2aa198; }}

    table.dataTable tbody tr {{
      border-bottom: 1px solid #002b36;
      transition: background 0.1s;
    }}

    table.dataTable tbody tr:last-child {{ border-bottom: none; }}
    table.dataTable tbody tr:hover {{ background: #003847; }}

    table.dataTable tbody tr.odd  {{ background: #073642; }}
    table.dataTable tbody tr.even {{ background: #063340; }}
    table.dataTable tbody tr.odd:hover,
    table.dataTable tbody tr.even:hover {{ background: #003847; }}

    table.dataTable tbody td {{
      padding: 0.65rem 1rem;
      font-size: 14px;
      vertical-align: top;
      color: #839496;
      border-top: none;
    }}

    table.dataTable tbody td a {{
      color: #268bd2;
      text-decoration: none;
      font-weight: 500;
    }}

    table.dataTable tbody td a:hover {{ color: #2aa198; text-decoration: underline; }}

    .dataTables_wrapper .dataTables_info {{
      font-size: 13px;
      color: #586e75;
      margin-top: 0.75rem;
    }}

    .dataTables_wrapper .dataTables_paginate {{
      margin-top: 0.75rem;
    }}

    .dataTables_wrapper .dataTables_paginate .paginate_button {{
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      cursor: pointer;
      color: #839496 !important;
      border: 1px solid transparent;
    }}

    .dataTables_wrapper .dataTables_paginate .paginate_button:hover {{
      background: #073642 !important;
      border-color: #586e75 !important;
      color: #93a1a1 !important;
    }}

    .dataTables_wrapper .dataTables_paginate .paginate_button.current,
    .dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {{
      background: #2aa198 !important;
      border-color: #2aa198 !important;
      color: #002b36 !important;
      font-weight: 600;
    }}

    .dataTables_wrapper .dataTables_paginate .paginate_button.disabled,
    .dataTables_wrapper .dataTables_paginate .paginate_button.disabled:hover {{
      color: #586e75 !important;
      cursor: default;
    }}

    footer {{
      text-align: center;
      padding: 1.5rem;
      font-size: 12px;
      color: #586e75;
    }}

    footer a {{ color: #268bd2; text-decoration: none; }}
    footer a:hover {{ color: #2aa198; }}

    footer code {{
      background: #073642;
      padding: 0.1rem 0.4rem;
      border-radius: 3px;
      font-size: 11px;
      color: #b58900;
    }}

    @media (max-width: 700px) {{
      main, header {{ padding: 1rem; }}
      table.dataTable tbody td {{ font-size: 12px; padding: 0.5rem 0.6rem; }}
    }}
  </style>
</head>
<body>

<header>
  <h1>🎯 Awesome Trackers</h1>
  <p>A curated list of tools for 2D/3D object and trajectory tracking &mdash;
     <a href="https://github.com/rodrigo-j-goncalves/awesome-trackers">contribute on GitHub</a>
     &nbsp;|&nbsp; last updated: {today}
  </p>
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

  // Global search
  document.getElementById('global-search').addEventListener('input', function () {{
    table.search(this.value).draw();
  }});

  // Per-column filters
  {js_filter_bindings}

  // Clear all filters
  document.getElementById('clear-btn').addEventListener('click', function () {{
    table.search('').columns().search('').draw();
    document.getElementById('global-search').value = '';
    document.querySelectorAll('.col-filter-text').forEach(el => el.value = '');
    document.querySelectorAll('.col-filter-select').forEach(el => el.selectedIndex = 0);
  }});

  // Hide the default DataTables search box
  document.querySelector('.dataTables_filter').style.display = 'none';
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
