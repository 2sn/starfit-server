import jinja2 as j2

env = j2.Environment(
    loader=j2.FileSystemLoader("templates"), autoescape=j2.select_autoescape()
)


def render_results(config, result, img_tags):
    if config.errors or not config.mail:
        template = env.get_template("page.html.jinja")
    else:
        template = env.get_template("email.html.jinja")

    return template.render(config=config, result=result, img_tags=img_tags)


def render_page(config):
    template = env.get_template("page.html.jinja")
    return template.render(config=config)
