import jinja2 as j2


def render_results(
    result,
    z_max,
    exc_string,
    lol_string,
    method_string,
    img_tags,
    mail,
    errors,
):
    env = j2.Environment(
        loader=j2.FileSystemLoader("templates"), autoescape=j2.select_autoescape()
    )

    if errors or not mail:
        template = env.get_template("page.html.jinja")
    else:
        template = env.get_template("email.html.jinja")

    return template.render(vars())


def render_page(
    mail,
    email,
    time_eta,
    errors,
):
    env = j2.Environment(
        loader=j2.FileSystemLoader("templates"), autoescape=j2.select_autoescape()
    )

    template = env.get_template("page.html.jinja")
    return template.render(vars())
