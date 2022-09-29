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

    method_string = config.get_method_string()

    return template.render(
        result=result,
        z_max=config.z_max,
        exc_string=exc_string,
        lol_string=lol_string,
        method_string=method_string,
        img_tags=img_tags,
        mail=config.mail,
        errors=config.errors,
    )


def render_page(config):
    template = env.get_template("page.html.jinja")
    return template.render(
        mail=config.mail,
        email=config.email,
        time_eta=config.time_eta,
        errors=config.errors,
    )
