import jinja2 as j2


def render(
    result,
    z_max,
    exc_string,
    lol_string,
    method_string,
    img_tags,
    mail,
    time_eta,
    error,
):
    env = j2.Environment(
        loader=j2.FileSystemLoader("templates"), autoescape=j2.select_autoescape()
    )

    template_mail = env.get_template("email.html.jinja")
    template_page = env.get_template("page.html.jinja")

    # Do not render the mail content if:
    # - an error is encountered, or
    # - mail is not selected
    if error or not mail:
        return template_page.render(vars()), None
    else:
        return template_page.render(vars()), template_mail.render(vars())
