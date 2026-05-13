from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

templates_directory = Path(__file__).parent / "templates"

env = Environment(
    loader=FileSystemLoader(templates_directory),
    autoescape=select_autoescape(enabled_extensions=["html", "xml"]),
)


def render_template(template_name: str, **context: Any) -> str:
    """
    Renders a Jinja2 template with the given context.
    """
    template = env.get_template(name=template_name)
    return template.render(**context)
