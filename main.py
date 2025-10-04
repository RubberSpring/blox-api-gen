from pathlib import Path

import json

import typer
from typing_extensions import Annotated

import requests
import jinja2

from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

app = typer.Typer()

@app.command()
def fetch(gen: str):
    r = requests.get(f"https://cdn.jsdelivr.net/gh/Roblox/creator-docs/content/en-us/reference/engine/classes/{gen}.yaml")
    content = r.content
    with open(f"{gen}.yaml", "wb") as f:
        f.write(content)

def lock(rblx_class: str, file: str):
    if not Path("blox-api-gen.lock").exists():
        with open("blox-api-gen.lock", "w") as f:
            f.write("{}")
    with open("blox-api-gen.lock", "r+") as f:
        lock_file = json.loads(f.read())
        lock_file["note"] = "This file was written by blox-api-gen and should not be hand edited."
        lock_file[rblx_class] = file
        f.seek(0)
        f.write(json.dumps(lock_file))
        f.truncate()

@app.command()
def gen(file: str, dummy_error: Annotated[bool, typer.Option("--dummy_error",help="Raises an error instead of printing a message")] = False):
    content = ""
    with open(file, "r") as f:
        content = f.read()
    api = load(content, SafeLoader)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates/"))
    template = env.get_template("class.luau.jinja")
    context = {
        "name": api["name"],
        "props": api["properties"],
        "methods": api["methods"],
        "dummy_error": dummy_error
    }
    with open(f"{api["name"]}.luau", "w") as f:
        f.write(template.render(context))
    lock(api["name"], f"{api["name"]}.luau")

if __name__ == "__main__":
    app()