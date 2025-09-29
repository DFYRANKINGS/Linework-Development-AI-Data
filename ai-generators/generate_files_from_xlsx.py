# ai-generators/generate_files_from_xlsx.py

import argparse
import os
import json
import yaml
from pathlib import Path
import pandas as pd

def load_xlsx_to_dict(xlsx_path):
    """Load first sheet of XLSX into dict assuming it's key-value in columns A/B"""
    df = pd.read_excel(xlsx_path, sheet_name=0, header=None)
    data = {}
    for _, row in df.iterrows():
        if len(row) >= 2 and pd.notna(row[0]) and pd.notna(row[1]):
            key = str(row[0]).strip()
            value = row[1]
            # Try to convert numeric/bool if possible
            if isinstance(value, str):
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                else:
                    try:
                        value = int(value)
                    except:
                        try:
                            value = float(value)
                        except:
                            pass
            data[key] = value
    return data

def write_json_yaml(data, base_output_path, filename_base):
    """Write both .json and .yaml files"""
    json_path = base_output_path / f"{filename_base}.json"
    yaml_path = base_output_path / f"{filename_base}.yaml"

    # Ensure directory exists
    base_output_path.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Write YAML
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    print(f"✅ Generated: {json_path} and {yaml_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Path to input .xlsx file')
    args = parser.parse_args()

    # Load data
    data = load_xlsx_to_dict(args.input)

    # Determine output filename from input (e.g., client-data.xlsx → main-data)
    input_stem = Path(args.input).stem
    output_name = input_stem.replace("client-", "main-")  # Customize naming logic as needed

    # Output to schema-files/organization/
    output_dir = Path("schema-files/organization")
    
    write_json_yaml(data, output_dir, output_name)

    # Also save SITE_BASE_URL if present in data (for sitemap later)
    site_url = data.get('website') or data.get('Website') or data.get('URL') or os.getenv('SITE_BASE_URL')
    if site_url:
        # Save to a shared config file so sitemap generator can access it
        config_dir = Path(".github/config")
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_dir / "site_url.txt", "w") as f:
            f.write(site_url.strip())
        print(f"🌐 Site URL saved: {site_url}")

if __name__ == "__main__":
    main()
