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
    'Help Articles': {  # Renamed from "Blog Summaries"
        'output_dir': 'schema-files/help-articles',
        'filename_base': 'articles-list',
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

def clean_value(key, val):
    """Clean and convert values appropriately"""
    if pd.isna(val):
        return None
    val = str(val).strip()
    if val.lower() in ['not specified', 'n/a', '', 'none']:
        return None

    # Special handling for sameAs field
    if key == 'sameAs' and isinstance(val, str):
        # Split by pipe and clean each URL
        urls = [url.strip() for url in val.split('|') if url.strip()]
        return urls if urls else None

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
                    val = clean_value(header, row.iloc[i]) if pd.notna(row.iloc[i]) else None
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
            key_cell = row.iloc[0]
            if pd.isna(key_cell) or str(key_cell).strip() == '':
                continue
            key = str(key_cell).strip()
            value = clean_value(key, row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else None
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
    if 
