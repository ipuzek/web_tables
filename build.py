import requests
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

env = Environment(loader=FileSystemLoader("templates"))
out = Path("site")
out.mkdir(exist_ok=True)

# --- Page 1 -------------------------------------------------

data_mb = requests.get("https://oss.uredjenazemlja.hr/oss/public/search-lr-parcels/main-books").json()
data_ko = requests.get("https://oss.uredjenazemlja.hr/oss/public/search-cad-parcels/municipalities").json()

def tidy_mb(data):
    return [
        {
            "mainBookId": el.get("key1"),
            "mainBookName": el.get("value1"),
            "institutionId": el.get("key2"),
            "institutionName": el.get("value2"),
            "displej": el.get("displayValue1"),
        }
        for el in data
    ]

def tidy_ko(data):
    new_dict = [
        {
            "cadastreMunicipalityRegNum": el.get("key2"),
            "displej": el.get("displayValue1"),
        }
        for el in data 
    ]
    
    for el in new_dict:
        el["displej"] = el["displej"].removeprefix(el.get("cadastreMunicipalityRegNum")).strip()
    return new_dict

pages = [
    
    # --- Page 1 ---------------------------------------------

    {
        "output": "index.html",
        "title": "KO data",
        "rows": tidy_ko(data_ko),
        "columns": [
            {"key": "cadastreMunicipalityRegNum", "label": "Matični broj KO"},
            {"key": "displej", "label": "Puni naziv"},
        ],
    },

    # --- Page 2 ---------------------------------------------

    {
        "output": "other.html",
        "title": "Main books",
        "rows": tidy_mb(data_mb),
        "columns": [
            {"key": "mainBookId", "label": "MainBookId"},
            {"key": "mainBookName", "label": "Glavna knjiga"},
            {"key": "institutionName", "label": "ZK odjel"},
            {"key": "displej", "label": "Puni naziv"},
        ],
    },


]

tpl = env.get_template("table.html.j2")

for page in pages:
    (out / page["output"]).write_text(
        tpl.render(**page),
        encoding="utf-8",
    )
