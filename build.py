import feedparser
import pandas as pd
from urllib.parse import urlparse
from os.path import basename, splitext
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

env = Environment(loader=FileSystemLoader("templates"))
out = Path("site")
out.mkdir(exist_ok=True)

def fetch_tidy_ko():

    # Load and prepare dataframe
    off = (pd.read_json("https://oss.uredjenazemlja.hr/oss/public/search-cad-parcels/offices")
        .rename(columns={"id": "office_id", "name":"office_name"}))

    dept = (pd.read_json("https://oss.uredjenazemlja.hr/oss/public/search-cad-parcels/departments")
            .rename(columns={"id": "dept_id", "name":"dept_name", "officeId": "office_id"}))

    mun = (pd.read_json("https://oss.uredjenazemlja.hr/oss/public/search-cad-parcels/municipalities")
        .rename(columns={
            "key1":"cadastreMunicipalityId",
            "value1":"ko_mb__name",
            "key2":"ko_mb",
            "value2": "office_id",
            "value3": "dept_id"})
        )
    
    off["office_name"] = off["office_name"].str.replace("PODRUČNI URED ZA KATASTAR", "PUK")
    
    dept["dept_name"] = dept["dept_name"].str.replace("ODJEL ZA KATASTAR NEKRETNINA", "OKN")

    mun["name"] = mun.apply(lambda row: row["ko_mb__name"].replace(str(row["ko_mb"]), "").strip().upper(), axis=1)

    off_dept = dept.merge(off, how="left")

    mun_complete = mun.merge(off_dept, how="left").convert_dtypes()

    df = mun_complete[["ko_mb", "name", "dept_name", "office_name"]]
    
    df = df.sort_values(["office_name", "dept_name", "name"])
    
    return df

df_ko = fetch_tidy_ko()

def fetch_tidy_mb():

    df = (
        pd.read_json('https://oss.uredjenazemlja.hr/oss/public/search-lr-parcels/main-books')
        .dropna(axis="columns", how="all")
        .convert_dtypes()
        .rename(columns={
            "key1" : "mainBookId",
            "value1" : "mainBookName",
            "key2" : "institutionId",
            "value2" : "institutionName",
            "displayValue1" : "displej"
        })
    )

    return (df
            .sort_values(["institutionName", "mainBookName"])
            .reset_index(drop=True))

df_mb = fetch_tidy_mb()


def fetch_atom_links():

    atom_feed = feedparser.parse('https://oss.uredjenazemlja.hr/oss/public/atom/atom_feed.xml')
    rows = [(entry.get("title"), entry.get("link")) for entry in atom_feed.get("entries")]

    df = pd.DataFrame(rows, columns=["ko_name", "url"])
    df["ko_name"] = df.ko_name.str.removeprefix("Cadastral municipality").str.strip()
    df["ko_mb"] = df.url.map(lambda x:splitext(basename(urlparse(x).path))[0].split('-')[1])
    df["ko_mb"] = pd.to_numeric(df["ko_mb"])
    
    return df

df_atom = fetch_atom_links()
df_atom_enriched = (df_atom
                    .merge(df_ko, how="left")
                    .drop(columns="name"))

pages = [
    
    # --- Page 1 ---------------------------------------------

    {
        "output": "index.html",
        "title": "",
        "rows": df_ko.to_dict(orient="records"),
        "columns": [
            {"key": "ko_mb", "label": "Matični broj KO"},
            {"key": "name", "label": "Naziv KO"},
            {"key": "dept_name", "label": "Naziv odjela"},
            {"key": "office_name", "label": "Naziv ureda"},
        ],
    },

    # --- Page 2 ---------------------------------------------

    {
        "output": "other.html",
        "title": "",
        "rows": df_mb.to_dict(orient="records"),
        "columns": [
            {"key": "mainBookId", "label": "MainBookId"},
            {"key": "mainBookName", "label": "Glavna knjiga"},
            {"key": "institutionName", "label": "ZK odjel"},
            {"key": "displej", "label": "Puni naziv"},
        ],
    },
    
    # --- Page 3 ---------------------------------------------

    {
        "output": "atom_links.html",
        "title": "",
        "rows": df_atom_enriched.to_dict(orient="records"),
        "columns": [
            {"key": "ko_name", "label": "Naziv KO"},
            {"key": "ko_mb", "label": "Matični broj KO"},
            {"key": "url", "label": "Preuzimanje"},
            {"key": "dept_name", "label": "Naziv odjela"},
            {"key": "office_name", "label": "Naziv ureda"},
        ],
    },


]

tpl = env.get_template("table.html.j2")

for page in pages:
    (out / page["output"]).write_text(
        tpl.render(**page),
        encoding="utf-8",
    )
