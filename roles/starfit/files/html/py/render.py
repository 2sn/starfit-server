import jinja2 as j2
from starfit.autils.isotope import Ion

env = j2.Environment(
    loader=j2.FileSystemLoader("templates"), autoescape=j2.select_autoescape()
)


def render_results(config, result, img_tags):
    if config.errors or not config.mail:
        template = env.get_template("page.html.jinja")
    else:
        template = env.get_template("email.html.jinja")

    exc_string = ", ".join([Ion(x).element_symbol() for x in config.z_exclude])
    lol_string = ", ".join([Ion(x).element_symbol() for x in config.z_lolim])

    if exc_string == "":
        exc_string = "None"
    if lol_string == "":
        lol_string = "None"

    return template.render(
        config=config,
        result=result,
        exc_string=exc_string,
        lol_string=lol_string,
        img_tags=img_tags,
    )


def render_page(config):
    template = env.get_template("page.html.jinja")
    return template.render(config=config)
