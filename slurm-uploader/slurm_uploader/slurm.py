from enum import StrEnum

from jinja2 import Environment, PackageLoader, select_autoescape


class SlurmTemplate(StrEnum):

    HELLO_WORLD = "hello-world.sh.jinja"


class SlurmGenerator:

    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("snellius_stitcher", "templates"),
            autoescape=select_autoescape()
        )
    
    def render_slurm(self, slurm_template: SlurmTemplate, **kwargs: dict) -> str:
        template = self.env.get_template(slurm_template.value)
        rendered_template = template.render(**kwargs)
        return rendered_template
