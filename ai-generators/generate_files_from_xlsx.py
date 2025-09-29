# ai-generators/generate_files_from_xlsx.py

import argparse
import os
import json
import yaml
from pathlib import Path
import pandas as pd

# Mapping: Sheet Name → Output Directory + Filename Base
SHEET_CONFIG = {
    'core_info': {
        'output_dir': 'schema-files/organization',
        'filename_base': 'main-data',
        'is_list': False  # Single object
    },
    'Services': {
        'output_dir': 'schema-files/services',
        'filename_base': 'services-list',
        'is_list': True
    },
    'Products': {
        'output_dir': 'schema-files/products',
        'filename_base': 'products-list',
        'is_list': True
    },
    'FAQs': {
        'output_dir': 'schema-files/faqs',
        'filename_base': 'faq',
        'is_list': True
    },
    'Blog Summaries': {
        'output_dir': 'schema-files/blogs',
        'filename_base': 'blogs-list',
        'is_list': True
    },
    'Reviews': {
        'output_dir': 'schema-files/reviews',
        'filename_base': 'reviews-list',
        'is_list': True
    },
    'Locations': {
        'output_dir': 'schema-files/locations',
        'filename_base': 'locations-list',
        'is_list': True
    },
    'Team': {
        'output_dir': 'schema-files/team',
        'filename_base': 'team-list',
        'is_list': True
    },
    'Awards & Certifications': {
        'output_dir': 'schema-files/awards',
        'filename_base': 'awards-list',
        'is_list': True
    },
    'Press/News Mentions': {
        'output_dir': 'schema-files/press',
        'filename_base': 'press-list',
        'is_list': True
    },
    'Case Studies': {
        'output_dir': 'schema-files/case-studies',
        'filename_base': 'case-studies-list',
        'is_list': True
    }
}

def clean_value(val):
    """Clean and convert values appropriately"""
    if pd.isna(val):
        return None
    val = str(val).strip()
    if val.lower() in ['not specified', 'n/a', '', 'none']:
        return None
    # Try converting to number
    if val.replace('.', '', 1).isdigit():
        return float(val) if '.' in val else int(val)
    # Try boolean
    if val.lower() in ['true', 'yes']:
        return True
    elif val.lower() in ['false', 'no']:
        return False
    return val

def parse_sheet_to_dict_or_list(df, is_list=False):
    """Convert sheet to dict (if key/value) or list of dicts (if table)"""
    if is_list:
        # Assume first row is header
        if df.shape[0] == 0:
            return []
        headers = df.iloc[0].apply(lambda x: str(x).strip() if pd.notna(x) else "").tolist()
        records = []
        for idx in range(1, len(df)):
            row = df.iloc[idx]
            record = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    val = clean_value(row.iloc[i])
                    if val is not None:
                        record[header] = val
            if record:  # Only add non-empty records
                records.append(record)
        return records
    else:
        # Key/value pairs (Column A = key, Column B = value)
        data = {}
        for _, row in df.iterrows():
            if len(row) < 2:
                continue
            key = clean_value(row.iloc[0])
            if not key:
                continue
            value = clean_value(row.iloc[1]) if len(row) > 1 else None
            data[key] = value
        return data

def write_json_yaml(data, output_path, filename_base):
    """Write both .json and .yaml files"""
    json_path = output_path / f"{filename_base}.json"
    yaml_path = output_path / f"{filename_base}.yaml"

    output_path.mkdir(parents=True, exist_ok=True)

    # Write JSON
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Wrote JSON: {json_path}")
    except Exception as e:
        print(f"❌ Failed to write JSON: {e}")
        return False

    # Write YAML
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"💾 Wrote YAML: {yaml_path}")
    except Exception as e:
        print(f"❌ Failed to write YAML: {e}")
        return False

    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Path to input .xlsx file')
    args = parser.parse_args()

    print(f"📂 Working directory: {os.getcwd()}")
    if not os.path.exists(args.input):
        print(f"❌ FATAL: Input file NOT FOUND: {args.input}")
        exit(1)

    print(f"✅ Processing: {args.input}")

    # Load all sheets
    try:
        xls = pd.ExcelFile(args.input)
        print(f"📄 Found sheets: {xls.sheet_names}")
    except Exception as e:
        print(f"❌ Error loading Excel file: {e}")
        exit(1)

    # Store core_info for sitemap URL
    site_url = None

    # Process each configured sheet
    for sheet_name, config in SHEET_CONFIG.items():
        if sheet_name not in xls.sheet_names:
            print(f"⚠️ Sheet '{sheet_name}' not found — skipping")
            continue

        print(f"\n--- Processing sheet: {sheet_name} ---")
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        print(f"📊 Shape: {df.shape}")

        # Parse data
        data = parse_sheet_to_dict_or_list(df, config['is_list'])

        if config['is_list']:
            print(f"📦 Parsed {len(data)} records")
        else:
            print(f"📦 Parsed {len(data)} fields")
            # If this is core_info, extract website
            if sheet_name == 'core_info':
                site_url = data.get('website')

        # Write files
        output_dir = Path(config['output_dir'])
        success = write_json_yaml(data, output_dir, config['filename_base'])

        if not success:
            print(f"❌ Failed to write output for {sheet_name}")

    # Save site URL for sitemap
    if site_url:
        config_dir = Path(".github/config")
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_dir / "site_url.txt", "w") as f:
            f.write(site_url.strip())
        print(f"\n🌐 Site URL saved for sitemap: {site_url}")
    else:
        fallback_url = os.getenv('SITE_BASE_URL')
        if fallback_url:
            config_dir = Path(".github/config")
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_dir / "site_url.txt", "w") as f:
                f.write(fallback_url.strip())
            print(f"\n🌐 Used fallback SITE_BASE_URL: {fallback_url}")
        else:
            print(f"\n⚠️ WARNING: No website found in core_info and no SITE_BASE_URL secret!")

    print("\n🎉 All sheets processed successfully!")

if __name__ == "__main__":
    main()
