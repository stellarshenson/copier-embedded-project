"""The author answer is split into first name, last name and email."""

from __future__ import annotations

import yaml
from helpers import ROOT, bake
from jinja2 import Environment

CONFIG = yaml.safe_load((ROOT / "copier.yml").read_text())


def derive(name: str, context: dict) -> str:
    """Render one derived answer the way Copier computes its default."""
    environment = Environment()
    template = environment.from_string(str(CONFIG[name]["default"]))
    return template.render(**context).strip()


def split_author(author: str) -> dict[str, str]:
    context = {"author_name": author}
    context["author_email"] = derive("author_email", context)
    context["author_name_clean"] = derive("author_name_clean", context)
    context["author_first_name"] = derive("author_first_name", context)
    context["author_last_name"] = derive("author_last_name", context)
    return {
        "first": context["author_first_name"],
        "last": context["author_last_name"],
        "email": context["author_email"],
    }


def copyright_line(path) -> str:
    for line in (path / "LICENSE").read_text().splitlines():
        if line.startswith("Copyright"):
            return line
    raise AssertionError("no copyright line")


def test_split_of_the_angle_bracket_form():
    assert split_author("Konrad Jelen <konrad.jelen@gmail.com>") == {
        "first": "Konrad",
        "last": "Jelen",
        "email": "konrad.jelen@gmail.com",
    }


def test_split_of_the_bare_email_form():
    assert split_author("Stellars Henson stellars.henson@gmail.com") == {
        "first": "Stellars",
        "last": "Henson",
        "email": "stellars.henson@gmail.com",
    }


def test_split_keeps_every_name_token_after_the_first():
    assert split_author("Mary Jane Watson") == {
        "first": "Mary",
        "last": "Jane Watson",
        "email": "",
    }


def test_split_of_a_single_name():
    assert split_author("Ada") == {"first": "Ada", "last": "", "email": ""}


def test_split_of_an_empty_author():
    assert split_author("") == {"first": "", "last": "", "email": ""}


def test_name_in_angle_brackets():
    with bake({"platform": "arduino", "author_name": "Konrad Jelen <konrad.jelen@gmail.com>"}) as path:
        assert copyright_line(path) == "Copyright (c) 2026 Konrad Jelen <konrad.jelen@gmail.com>"


def test_name_followed_by_the_email():
    with bake({"platform": "arduino", "author_name": "Stellars Henson stellars.henson@gmail.com"}) as path:
        assert copyright_line(path) == "Copyright (c) 2026 Stellars Henson <stellars.henson@gmail.com>"


def test_name_only():
    with bake({"platform": "arduino", "author_name": "Ada Lovelace"}) as path:
        assert copyright_line(path) == "Copyright (c) 2026 Ada Lovelace"
