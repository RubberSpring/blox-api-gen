from pathlib import Path

import json

import typer
from typing_extensions import Annotated

from rich import print as rprint

import requests
import jinja2

import sys

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

def lock_func(rblx_class: str, file: str):
    if not Path("blox-api-gen.lock").exists():
        with open("blox-api-gen.lock", "w") as f:
            f.write("{}")
    with open("blox-api-gen.lock", "r+") as f:
        lock_file = json.loads(f.read())
        lock_file["note"] = "This file was written by blox-api-gen and should not be hand edited."
        file_path = Path(file)
        lock_file[rblx_class] = str(file_path)
        f.seek(0)
        f.write(json.dumps(lock_file))
        f.truncate()

@app.command()
def lock(rblx_class: str, file: str):
    if not Path(file).exists():
        rprint("[red]File does not exist.[/red]", file=sys.stderr)
        return None
    lock_func(rblx_class, file)

@app.command()
def gen(file: str,
        dummy_error: Annotated[bool, typer.Option("--dummy-error", help="Raises an error instead of printing a message")] = False,
        no_lock: Annotated[bool, typer.Option("--no-lock", help="Prevents editing (or creation) of an blox-gen-api.lock file")] = False):
    content = ""
    with open(file, "r") as f:
        content = f.read()
    api = load(content, SafeLoader)
    extends = api["inherits"]
    lock_data = None
    dep_exists = False
    if Path("blox-api-gen.lock").exists():
        with open("blox-api-gen.lock", "r") as f:
            lock_data = json.loads(f.read())
    if not len(extends) == 0:
        if lock_data is not None:
            try:
                lock_data[extends[0]]
                dep_exists = True
            except KeyError:
                rprint(f"[red]Class file for {extends} is missing.[/red]")
    else:
        dep_exists = True
    if not dep_exists:
        return None
    env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates/"))
    template = env.get_template("class.luau.jinja")
    context = {
        "name": api["name"],
        "methods": api["methods"],
        "inherits": extends,
        "dummy_error": dummy_error
    }
    with open(f"{api["name"]}.luau", "w") as f:
        f.write(template.render(context))
    if not no_lock:
        lock_func(api["name"], f"{str(Path(file))}.luau")

if __name__ == "__main__":
    app()