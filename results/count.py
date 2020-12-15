import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

s = {
    "PREPARE",
    "PROMISE",
    "ACCEPT",
    "ACCEPTED",
    "DECIDE",
    "DENIED",
    "CONFIRMATION",
    "503",
}


def get_cat(line: str):
    for kw in s:
        if kw in line:
            return kw

    return "IGNORE"


def jsonify_logs():

    path = Path(".")

    for log in path.glob("*.log"):
        count = defaultdict(lambda: 0)

        with open(log, "r") as logfile:
            for line in logfile:
                count[get_cat(line)] += 1

        name = log.name.split(".")[0]
        with open(f"{name}.json", "w") as f:
            f.write(json.dumps(count, indent=4))
        print(log, count)


def get_table(path: Path):
    name = path.name.split(".")[0]
    serie = pd.read_json(path, typ="series")
    return pd.DataFrame(serie, columns=[name]).transpose()


def write_to_md(df, name):
    df = df.drop("IGNORE", axis=1)
    with open(name, "w") as md:
        df.to_markdown(md)


def make_tables():
    path = Path(".")
    tables = dict()
    for log in path.glob("*.json"):
        name = log.name.split(".")[0]
        tables[name] = get_table(log)

    write_to_md(tables["basic"], "basic.md")
    write_to_md(tables["ultimate"], "ultimate.md")

    one_message = pd.concat([tables["one_one_one"], tables["three_one_one"]])
    three_messages = pd.concat([tables["one_one_three"], tables["three_three_three"]])
    nine_messages = pd.concat([tables["one_one_nine"], tables["three_three_nine"]])

    write_to_md(one_message, "one.md")
    write_to_md(three_messages, "three.md")
    write_to_md(nine_messages, "nine.md")


if __name__ == "__main__":
    jsonify_logs()
    make_tables()
