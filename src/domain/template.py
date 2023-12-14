from jinja2 import Environment, FileSystemLoader, select_autoescape
from domain.settings import BASE_DIR

TEMPLATES_DIR = BASE_DIR / 'templates'


class Renderer:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(
                disabled_extensions=('txt',),
                default_for_string=True,
                default=True,)
        )

    def render(self, template_name: str, **kwargs):
        self.template = self.env.get_template(template_name)
        return self.template.render(**kwargs)


renderer = Renderer()
