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


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames
    return columns, rows


def build_header_row(columns):
    cells = "".join(f"<th>{html.escape(col)}</th>" for col in columns)
    return f"<tr>{cells}</tr>"


def build_data_row(columns, row):
    cells = []
    for col in columns:
        val = row.get(col, "")
        # If column is "Name" and URL column exists, make it a link
        if col == "Name" and "URL" in row and row["URL"].strip():
            content = f'<a href="{html.escape(row["URL"].strip())}" target="_blank" rel="noopener">{html.escape(val)}</a>'
        elif col == "URL":
            # Hide raw URL column — name column already links it
            content = html.escape(val)
        else:
            content = html.escape(val)
        cells.append(f"<td>{content}</td>")
    return "<tr>" + "".join(cells) + "</tr>"


def build_html(columns, rows):
    today = date.today().isoformat()
    header = build_header_row(columns)
    body_rows = "\n".join(build_data_row(columns, row) for row in rows)

    # Determine index of URL column to hide it (0-based)
    url_col_index = columns.index("URL") if "URL" in columns else None
    hide_url_js = ""
    if url_col_index is not None:
        hide_url_js = f'table.column({url_col_index}).visible(false);'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Awesome Trackers</title>
  <link rel="stylesheet" href="https://cdn.datatables.net/2.0.8/css/dataTables.dataTables.min.css" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}

    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: 15px;
      line-height: 1.6;
      margin: 0;
      padding: 0;
      background: #f7f8fa;
      color: #1a1a2e;
    }}

    header {{
      background: #1a1a2e;
      color: #e8e8f0;
      padding: 2rem 2.5rem 1.5rem;
      border-bottom: 3px solid #4f8ef7;
    }}

    header h1 {{
      margin: 0 0 0.25rem;
      font-size: 1.8rem;
      font-weight: 600;
      letter-spacing: -0.02em;
    }}

    header p {{
      margin: 0;
      font-size: 0.9rem;
      color: #9999bb;
    }}

    header a {{
      color: #4f8ef7;
      text-decoration: none;
    }}

    header a:hover {{ text-decoration: underline; }}

    main {{
      padding: 2rem 2.5rem;
      max-width: 1400px;
      margin: 0 auto;
    }}

    #search-box {{
      margin-bottom: 1.25rem;
    }}

    #search-box input {{
      width: 100%;
      max-width: 420px;
      padding: 0.5rem 0.85rem;
      font-size: 14px;
      border: 1px solid #ccc;
      border-radius: 6px;
      background: #fff;
      color: #1a1a2e;
      outline: none;
      transition: border-color 0.15s;
    }}

    #search-box input:focus {{ border-color: #4f8ef7; }}

    table.dataTable {{
      width: 100% !important;
      border-collapse: collapse;
      background: #fff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }}

    table.dataTable thead th {{
      background: #1a1a2e;
      color: #e8e8f0;
      font-weight: 500;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 0.75rem 1rem;
      border-bottom: none;
      cursor: pointer;
      white-space: nowrap;
    }}

    table.dataTable thead th:hover {{ background: #2a2a4e; }}

    table.dataTable tbody tr {{
      border-bottom: 1px solid #ececf3;
      transition: background 0.1s;
    }}

    table.dataTable tbody tr:last-child {{ border-bottom: none; }}
    table.dataTable tbody tr:hover {{ background: #f0f4ff; }}

    table.dataTable tbody td {{
      padding: 0.65rem 1rem;
      font-size: 14px;
      vertical-align: top;
    }}

    table.dataTable tbody td a {{
      color: #4f8ef7;
      text-decoration: none;
      font-weight: 500;
    }}

    table.dataTable tbody td a:hover {{ text-decoration: underline; }}

    .dataTables_wrapper .dataTables_info,
    .dataTables_wrapper .dataTables_paginate {{
      font-size: 13px;
      color: #666;
      margin-top: 0.75rem;
    }}

    .dataTables_wrapper .dataTables_paginate .paginate_button {{
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      cursor: pointer;
    }}

    .dataTables_wrapper .dataTables_paginate .paginate_button.current {{
      background: #4f8ef7;
      color: #fff !important;
      border: none;
    }}

    footer {{
      text-align: center;
      padding: 1.5rem;
      font-size: 12px;
      color: #999;
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
  </div>

  <table id="trackers" class="dataTable" style="width:100%">
    <thead>{header}</thead>
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
  const table = new DataTable('#trackers', {{
    pageLength: 25,
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

  // Wire up our own search box to DataTables
  document.getElementById('global-search').addEventListener('input', function () {{
    table.search(this.value).draw();
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
