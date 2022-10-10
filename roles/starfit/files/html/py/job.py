import os
import smtplib
from email import encoders as Encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from socket import gethostname

import jinja2 as j2
import matplotlib as mpl
import starfit
from utils import convert_img_to_b64_tag

jinja_env = j2.Environment(loader=j2.FileSystemLoader("templates"))

mpl.use("Agg")
mpl.rc("text", usetex=True)


def compute(config):
    combine = config.combine_elements()
    if config.algorithm == "ga":
        # Run the fitting algorithm
        result = starfit.Ga(
            filename=config.filepath,
            db=config.dbpath,
            time_limit=config.time_limit,
            pop_size=config.pop_size,
            sol_size=config.sol_size,
            local_search=True,
            z_max=config.z_max,
            z_exclude=config.z_exclude,
            z_lolim=config.z_lolim,
            combine=combine,
            fixed_offsets=config.fixed,
            cdf=config.cdf,
        )
    elif config.algorithm == "double":
        result = starfit.Double(
            filename=config.filepath,
            db=config.dbpath,
            silent=True,
            n_top=1000,
            combine=combine,
            fixed=config.fixed,
            save=True,
            webfile=config.start_time,
            cdf=config.cdf,
        )
    elif config.algorithm == "single":
        result = starfit.Single(
            filename=config.filepath,
            db=config.dbpath,
            silent=True,
            combine=combine,
            z_max=config.z_max,
            z_exclude=config.z_exclude,
            z_lolim=config.z_lolim,
            cdf=config.cdf,
        )
    else:
        result = None

    return result


def make_plots(result, config):

    # File objects
    file_obj = []

    # Abundance plot
    result.plot()
    imgfile = BytesIO()
    mpl.pyplot.savefig(imgfile, format=config.plotformat)
    file_obj += [imgfile]

    if config.algorithm == "ga":
        result.plot_fitness()
        imgfile = BytesIO()
        mpl.pyplot.savefig(imgfile, format=config.plotformat)
        file_obj += [imgfile]

    # Save plot data to ASCII file
    plotdatafile = os.path.join("/tmp", "plot_data_points" + config.start_time)
    with open(plotdatafile, mode="w") as f:
        f.write("Z      log(X/X_sun)\n")
        for z, abu in zip(result.plotdata[0], result.plotdata[1]):
            f.write(f"{z:<2}     {abu:7.5f}\n")

    return file_obj


def render(config, result, img_tags, doc, jobinfo=None):
    if doc in ("configerror", "resultpage", "sendmail", "jobfail", "email"):
        template = jinja_env.get_template(f"{doc}.html")
    else:
        raise RuntimeError("Bad choice of 'doc'")

    return template.render(
        config=config, result=result, img_tags=img_tags, jobinfo=jobinfo
    )


def send_email(config, body, imgfiles):
    session = smtplib.SMTP(gethostname())
    sender = f"results@{gethostname()}"

    msg = MIMEMultipart()
    msg["From"] = f"StarFit <{sender}>"
    msg["To"] = config.email
    msg["Bcc"] = "starfit.results@gmail.com"
    msg["Subject"] = "StarFit Results"
    msg.add_header(
        "List-Unsubscribe",
        f"<mailto: starfit.results@gmail.com?subject=unsubscribe>, <https://{gethostname()}/unsubscribe>",
    )

    msg.attach(MIMEText(body, "html"))

    # Attach images
    part = MIMEBase("application", "octet-stream")
    part.set_payload(imgfiles[0].getvalue())
    Encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="abundance_plot.{config.plotformat}"',
    )
    msg.attach(part)

    if config.algorithm == "ga":
        part = MIMEBase("application", "octet-stream")
        part.set_payload(imgfiles[1].getvalue())
        Encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="ga_fitness_plot.{config.plotformat}"',
        )
        msg.attach(part)

    # Attach big numbers
    if config.algorithm == "double":
        part = MIMEBase("application", "octet-stream")
        part.set_payload(open(os.path.join("/tmp", config.start_time), "rb").read())
        Encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            'attachment; filename="full_results.txt"',
        )
        msg.attach(part)

    # Attach plot data
    part = MIMEBase("application", "octet-stream")
    part.set_payload(
        open(os.path.join("/tmp", "plot_data_points" + config.start_time), "rb").read()
    )
    Encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="plot_data_points_{config.filename}.txt"',
    )
    msg.attach(part)

    # Attach input data
    if config.filename:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(open(config.filepath, "rb").read())
        Encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{config.filename}"',
        )
        msg.attach(part)

    # Send!
    session.sendmail(sender, config.email, msg.as_string())


def run_job(config):
    result = compute(config)
    imgfiles = make_plots(result, config)
    img_tags = [convert_img_to_b64_tag(f, config.plotformat) for f in imgfiles]

    page = render(config, result, img_tags, doc="resultpage")
    email = render(config, result, img_tags, doc="email")

    if config.mail:  # Send an email with the results
        send_email(config, email, imgfiles)

    return page
