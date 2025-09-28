#!/usr/bin/env python3
"""
FINAL robust sitemap generator (v4).
- Reads client domains from Excel (.xlsx) (flexible header names).
- Rejects placeholder domains like example.com / yourdomain.com.
- Includes only EXISTING, NON-EMPTY .json/.yaml/.yml files.
- Supports either explicit file columns OR auto-scans common folders.
- Writes a detailed report at sitemaps/_report.txt and prints it to stdout.

Usage: python generate_sitemaps.py
Expected Excel at repo root: client-data.xlsx
"""

from __future__ import annotations
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

# Accept multiple header names to be forgiving
DOMAIN_CANDIDATES = ["domain", "site_url", "website", "base_url", "url"]
CLIENT_CANDIDATES = ["client_name", "name", "client", "brand"]

# File columns can contain single filename or comma/semicolon/newline-separated lists.
FILE_COLUMNS = [
    "locations_file", "products_file", "team_file",
    "locations_files", "products_files", "team_files",
    "include_files", "include_paths", "extra_paths", "paths"
]

# Default folders to auto-scan if no file columns are present
DEFAULT_FOLDERS = ["locations", "products", "team"]
VALID_EXTS = {".json", ".yaml", ".yml"}

def pick_first(df_columns, candidates):
    lower_map = {c.lower(): c for c in df_columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    return None

def split_items(val):
    if pd.isna(val):
        return []
    if isinstance(val, (int, float)):
        val = str(val)
    s = str(val)
    for sep in [",", ";", "\n"]:
        s = s.replace(sep, "|")
    return [p.strip() for p in s.split("|") if p.strip()]

def ensure_scheme(url: str) -> str:
    u = url.strip()
    if not u:
        return u
    if not (u.startswith("http://") or u.startswith("https://")):
        u = "https://" + u
    return u.rstrip("/")

def is_placeholder_domain(domain: str) -> bool:
    low = domain.lower()
    return any(p in low for p in ["example.com", "yourdomain.com", "your-domain.com"])

def file_is_nonempty(p: Path) -> bool:
    try:
        return p.exists() and p.is_file() and p.stat().st_size > 0
    except Exception:
        return False

def iso_utc_from_mtime(p: Path) -> str:
    try:
        dt = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main():
    report = []
    try:
        xlsx = Path("client-data.xlsx")
        if not xlsx.exists():
            raise FileNotFoundError("Missing client-data.xlsx at repo root. Place it next to generate_sitemaps.py.")

        try:
            df = pd.read_excel(xlsx)
        except Exception as e:
            raise RuntimeError(f"Failed to read Excel ({xlsx}). Ensure it's .xlsx (not .xls). Underlying error: {e}")

        domain_col = pick_first(df.columns, DOMAIN_CANDIDATES)
        if not domain_col:
            raise KeyError(f"Cannot find a domain column. Expected one of {DOMAIN_CANDIDATES}. Found: {list(df.columns)}")

        client_col = pick_first(df.columns, CLIENT_CANDIDATES) or domain_col
        file_cols = [c for c in FILE_COLUMNS if c in df.columns]

        out_dir = Path("sitemaps")
        out_dir.mkdir(parents=True, exist_ok=True)

        total = 0
        for i, row in df.iterrows():
            raw_dom = str(row.get(domain_col, "")).strip()
            if not raw_dom or str(raw_dom).lower() == "nan":
                report.append(f"ROW {i+1}: SKIPPED — empty domain.")
                continue

            domain = ensure_scheme(raw_dom)
            if is_placeholder_domain(domain):
                report.append(f"ROW {i+1}: ERROR — placeholder domain detected ({domain}). Update Excel with a real domain.")
                continue

            client_raw = str(row.get(client_col, f"client_{i+1}")).strip() or f"client_{i+1}"
            slug = client_raw.replace(" ", "_").replace("/", "_").lower()

            # Build candidate path list from Excel or auto-scan
            paths = []
            if file_cols:
                for col in file_cols:
                    paths.extend(split_items(row[col]))
            else:
                # Auto-scan default folders for .json/.yaml/.yml
                for folder in DEFAULT_FOLDERS:
                    base = Path(folder)
                    if base.exists():
                        for p in base.rglob("*"):
                            if p.suffix.lower() in VALID_EXTS and file_is_nonempty(p):
                                paths.append(p.as_posix())

            # Resolve actual existing nonempty files
            existing = []
            for item in paths:
                p = Path(item)
                cand = []
                if p.exists() and p.is_file():
                    cand = [p]
                else:
                    # If a bare filename was provided, try under each default folder
                    if p.name and p.suffix.lower() in VALID_EXTS and ("/" not in item and "\\" not in item):
                        for folder in DEFAULT_FOLDERS:
                            maybe = Path(folder) / p.name
                            if file_is_nonempty(maybe):
                                cand.append(maybe)

                for c in cand:
                    if c.suffix.lower() in VALID_EXTS and file_is_nonempty(c):
                        existing.append(c)

            # Deduplicate while preserving order
            seen = set()
            uniq = []
            for p in existing:
                if p.as_posix() not in seen:
                    uniq.append(p)
                    seen.add(p.as_posix())

            # Write sitemap
            sitemap_path = out_dir / f"{slug}_sitemap.xml"
            with sitemap_path.open("w", encoding="utf-8") as f:
                f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
                for p in uniq:
                    lastmod = iso_utc_from_mtime(p)
                    rel = p.as_posix().lstrip("./")
                    f.write("  <url>\n")
                    f.write(f"    <loc>{domain}/{rel}</loc>\n")
                    f.write(f"    <lastmod>{lastmod}</lastmod>\n")
                    f.write("  </url>\n")
                f.write("</urlset>\n")

            if uniq:
                report.append(f"ROW {i+1}: WROTE {sitemap_path.name} with {len(uniq)} URL(s) for {domain}.")
            else:
                report.append(f"ROW {i+1}: WROTE {sitemap_path.name} (0 URLs). "
                              f"No files found. Provide file paths in {file_cols or 'DEFAULT_FOLDERS'} or add files.")

            total += 1

        report.append(f"Done. Generated {total} sitemap file(s).")
    except Exception as e:
        report.append("ERROR: " + str(e))
        report.append("TRACEBACK:\n" + traceback.format_exc())

    # Persist and print report
    out_dir = Path("sitemaps")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))

if __name__ == "__main__":
    sys.exit(main())
