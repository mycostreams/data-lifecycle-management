from jinja2 import Environment, PackageLoader
from uuid import uuid4



def main():

    env = Environment(
        loader=PackageLoader("snellius_stitcher", "templates"),
    )

    template = env.get_template("run.sh.jinja")

    rendered_template = template.render(job_id={uuid4().hex[:6]})


main()

