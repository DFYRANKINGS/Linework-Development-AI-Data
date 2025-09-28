"""
generate_files_updated.py

This script reads a single‐client CSV file and generates a set of
structured data files (YAML, JSON, Markdown) and updates a sitemap
according to the folder layout used in the AI Visibility project.

## Usage

```
python generate_files_updated.py [path_to_csv] [output_dir]
```

If `path_to_csv` is not provided, it defaults to `data/client-data.csv`
relative to the current working directory. If `output_dir` is not
provided, it defaults to the current working directory.  The script
expects that the CSV contains exactly one row of data describing a
single client. If you have multiple clients, place each client in
their own repository and run this script separately in each repo.

## Customising the script

* **Column names:**  The script expects certain columns in the CSV,
  such as `client_name`, `website`, `category`, `tagline`,
  `description`, `business_hours`, `year_founded`,
  `number_of_employees`, `address`, `phone`, `email` and `licenses`.
  If your CSV uses different column names, update the keys in the
  `core` dictionary below accordingly.

* **Services:** Columns whose names start with `service_` will be
  treated as individual services.  Each non-empty value in a
  `service_` column will produce an entry in `services-list.yaml`
  and `services-list.json`.

* **Licenses:** The `licenses` column may contain a comma‐separated
  list of licenses or certifications.  The script splits this list
  and writes it to YAML and JSON.

* **Extending to FAQs, products, etc.:**  To generate other kinds
  of content (e.g. FAQs, products), you can either add additional
  columns to the CSV with predictable names (e.g. `faq_1_question`,
  `faq_1_answer`, etc.), or store those records in separate tabs of
  an Excel file.  You can then extend this script to parse those
  fields and write the appropriate YAML/JSON files.  The placeholder
  section marked `# TODO: handle FAQ, products, and other sections` is
  where you would add such logic.

* **Sitemap generation:**  The script scans the `schema-files` folder
  for files with YAML, JSON, TXT, or Markdown extensions and
  constructs an `ai-sitemap.xml`.  You can customise the base URL
  used in the sitemap by setting the `SITE_BASE_URL` environment
  variable when running the script (e.g. via your GitHub Action).

* **Weekly updates and search engine ping:**  If you want to update
  the generated files on a schedule (e.g. weekly) and notify search
  engines when the sitemap changes, configure your GitHub Actions
  workflow to run this script on both `push` and `schedule` events.
  After the script runs, you can use a curl command in the same
  workflow to ping search engines.  For example, see the example
  `Ping Google About Updated Sitemap` workflow which sends a GET
  request to Google to notify it of the updated sitemap【977096722945847†L44-L88】.

The script uses only the Python standard library and `pandas` for
data handling.  Make sure to add `pandas` and `pyyaml` (for YAML
support) to your `requirements.txt` file.
"""

import os
import sys
import datetime
import json
from typing import List, Dict, Any

import pandas as pd
import yaml


def ensure_directories(base_dir: str) -> None:
    """Create the directory structure expected by the AI Visibility project.

    Parameters
    ----------
    base_dir : str
        The root directory where generated files should be placed.
    """
    # Define all directories that might be needed.  You can add more
    # directories here if your project requires additional paths.
    required_dirs = [
        os.path.join(base_dir, 'schema-files', 'organization'),
        os.path.join(base_dir, 'schema-files', 'services'),
        os.path.join(base_dir, 'schema-files', 'faq'),
        os.path.join(base_dir, 'schema-files', 'products'),
        os.path.join(base_dir, 'ai-content'),
        os.path.join(base_dir, 'link-data'),
    ]
    for d in required_dirs:
        os.makedirs(d, exist_ok=True)


def parse_core_info(row: pd.Series) -> Dict[str, Any]:
    """Extract the core information for the client from the CSV row.

    Adjust the keys in this function to match your CSV columns.

    Parameters
    ----------
    row : pd.Series
        The row from the CSV representing a single client.

    Returns
    -------
    dict
        A dictionary containing the core information.
    """
    core = {
        'client_name': row.get('client_name'),
        'website': row.get('website'),
        'category': row.get('category'),
        'tagline': row.get('tagline'),
        'description': row.get('description'),
        'business_hours': row.get('business_hours'),
        'year_founded': row.get('year_founded'),
        'number_of_employees': row.get('number_of_employees'),
        'address': row.get('address'),
        'phone': row.get('phone'),
        'email': row.get('email'),
    }
    # Remove keys with missing values (NaN or None)
    return {k: v for k, v in core.items() if pd.notna(v)}


def parse_licenses(row: pd.Series) -> Dict[str, List[str]]:
    """Parse the licenses column into a list.

    Parameters
    ----------
    row : pd.Series
        The row from the CSV representing a single client.

    Returns
    -------
    dict
        A dictionary with a single key 'licenses' mapping to a list of
        license names.
    """
    licenses_raw = row.get('licenses')
    if pd.isna(licenses_raw):
        return {'licenses': []}
    # Split the licenses by comma and strip whitespace
    licenses = [lic.strip() for lic in str(licenses_raw).split(',') if lic.strip()]
    return {'licenses': licenses}


def parse_services(row: pd.Series) -> Dict[str, List[Dict[str, Any]]]:
    """Parse service information from columns prefixed with `service_`.

    Parameters
    ----------
    row : pd.Series
        The row from the CSV representing a single client.

    Returns
    -------
    dict
        A dictionary with a single key 'services' mapping to a list of
        service dictionaries.  Each service has a key 'service_name'.
    """
    services: List[Dict[str, Any]] = []
    for col in row.index:
        if isinstance(col, str) and col.lower().startswith('service_'):
            value = row[col]
            if pd.notna(value):
                services.append({'service_name': str(value).strip()})
    return {'services': services}


def write_yaml_json(data: Dict[str, Any], yaml_path: str, json_path: str) -> None:
    """Write the provided data to YAML and JSON files.

    Parameters
    ----------
    data : dict
        The data to write.
    yaml_path : str
        The path of the YAML file to write.
    json_path : str
        The path of the JSON file to write.
    """
    # YAML
    with open(yaml_path, 'w') as f_yaml:
        yaml.dump(data, f_yaml, sort_keys=False, allow_unicode=True)
    # JSON
    with open(json_path, 'w') as f_json:
        json.dump(data, f_json, indent=2, ensure_ascii=False)


def update_sitemap(base_dir: str, base_url: str) -> None:
    """Construct or update the ai-sitemap.xml file with generated content.

    Parameters
    ----------
    base_dir : str
        The root directory of the project.
    base_url : str
        The base URL for the site.  Should include the trailing slash.
    """
    sitemap_path = os.path.join(base_dir, 'ai-sitemap.xml')
    # Collect relevant file paths relative to base_dir
    urls: List[str] = []
    for root, _, files in os.walk(os.path.join(base_dir, 'schema-files')):
        for file in files:
            if file.endswith(('.yaml', '.json', '.txt', '.md')):
                rel_path = os.path.relpath(os.path.join(root, file), base_dir)
                urls.append(rel_path.replace(os.sep, '/'))  # normalise to forward slashes

    # Build the XML content
    lines: List[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    for url in urls:
        lines.append('  <url>')
        lines.append(f'    <loc>{base_url}{url}</loc>')
        lines.append(f'    <lastmod>{now}</lastmod>')
        lines.append('    <changefreq>weekly</changefreq>')
        lines.append('    <priority>0.5</priority>')
        lines.append('  </url>')
    lines.append('</urlset>')
    # Write the sitemap
    with open(sitemap_path, 'w') as f:
        f.write('\n'.join(lines))


def main(csv_path: str, output_dir: str) -> None:
    """Main entry point for the generator.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file containing client data.
    output_dir : str
        Directory into which the generated files should be written.
    """
    # Ensure the directory structure exists
    ensure_directories(output_dir)
    # Load the CSV into a DataFrame
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV '{csv_path}' is empty")
    if df.shape[0] != 1:
        raise ValueError(
            f"Expected exactly one row in '{csv_path}' for one client, but got {df.shape[0]} rows."
        )
    row = df.iloc[0]
    # Parse sections
    core_info = parse_core_info(row)
    licenses_info = parse_licenses(row)
    services_info = parse_services(row)
    # Write core information
    write_yaml_json(
        core_info,
        os.path.join(output_dir, 'schema-files', 'organization', 'main-data.yaml'),
        os.path.join(output_dir, 'schema-files', 'organization', 'main-data.json'),
    )
    # Write licenses
    write_yaml_json(
        licenses_info,
        os.path.join(output_dir, 'schema-files', 'organization', 'licenses.yaml'),
        os.path.join(output_dir, 'schema-files', 'organization', 'licenses.json'),
    )
    # Write services list
    write_yaml_json(
        services_info,
        os.path.join(output_dir, 'schema-files', 'services', 'services-list.yaml'),
        os.path.join(output_dir, 'schema-files', 'services', 'services-list.json'),
    )
    # TODO: handle FAQs, products, and other sections similarly.
    #       For example, you might parse columns like 'faq_1_question',
    #       'faq_1_answer', etc. and build a list of question/answer pairs.

    # Update the sitemap; base_url should point to where the files will
    # ultimately be hosted (e.g. your client website or GitHub Pages).
    base_url = os.environ.get('SITE_BASE_URL', 'https://example.com/')
    update_sitemap(output_dir, base_url)


if __name__ == '__main__':
    # Determine the CSV path and output directory from command line arguments
    csv_arg = sys.argv[1] if len(sys.argv) > 1 else 'data/client-data.csv'
    out_arg = sys.argv[2] if len(sys.argv) > 2 else '.'
    main(csv_arg, out_arg)
