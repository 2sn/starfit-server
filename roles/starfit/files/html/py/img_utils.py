import base64


def convert_img_to_b64_tag(file, format):
    plot_b64 = str(base64.b64encode(file.getvalue()))[2:-1]
    typestr = format
    if format == "svg":
        typestr += "+xml"
    img_tag = f'<object data="data:image/{typestr};base64,{plot_b64}" type="image/{typestr}" width="700"></object>'

    return img_tag
