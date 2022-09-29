import jinja2 as j2

env = j2.Environment(
    loader=j2.FileSystemLoader("templates"), autoescape=j2.select_autoescape()
)


def render(config, result, img_tags, doc):
    if doc in ("webpage", "email"):
        template = env.get_template(f"{doc}.html.jinja")
    else:
        raise RuntimeError("Bad choice of 'doc'")

    return template.render(config=config, result=result, img_tags=img_tags)
