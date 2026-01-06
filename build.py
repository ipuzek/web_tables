import pandas as pd
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

    mun["name"] = mun.apply(lambda row: row["ko_mb__name"].replace(str(row["ko_mb"]), "").strip().upper(), axis=1)

    off_dept = dept.merge(off, how="left")

    mun_complete = mun.merge(off_dept, how="left").convert_dtypes()

    df = mun_complete[["ko_mb", "name", "dept_name", "office_name"]]
    
    df = df.sort_values(["office_name", "dept_name", "name"])
    
    return df.to_dict(orient="records")

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
            .reset_index(drop=True)
            .to_dict(orient="records"))


pages = [
    
    # --- Page 1 ---------------------------------------------

    {
        "output": "index.html",
        "title": "KO data",
        "rows": fetch_tidy_ko(),
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
        "title": "Main books",
        "rows": fetch_tidy_mb(),
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
