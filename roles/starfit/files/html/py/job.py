import os
import smtplib
from email import encoders as Encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from socket import gethostname

import matplotlib as mpl
import starfit
from render import render_results
from utils import convert_img_to_b64_tag

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

    if config.algorithm in ["single", "double"]:
        plotrange = [0]
    elif config.perfplot:
        plotrange = [0, 1]
    else:
        plotrange = [0]

    # Write plots to file objects
    for i in plotrange:
        result.plot(i + 1)
        imgfile = BytesIO()
        mpl.pyplot.savefig(imgfile, format=config.plotformat)
        file_obj += [imgfile]

    # Save plot data to ASCII file
    plotdatafile = os.path.join("/tmp", "plotdata" + config.start_time)
    with open(plotdatafile, mode="w") as f:
        f.write("Z      log(X/X_sun)\n")
        for z, abu in zip(result.plotdata[0], result.plotdata[1]):
            f.write(f"{z:<2}     {abu:7.5f}\n")

    return file_obj


def send_email(config, body, imgfiles):
    session = smtplib.SMTP(gethostname())
    sender = f"results@{gethostname()}"

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = config.email
    msg["Subject"] = "StarFit Results"

    msg.attach(MIMEText(body, "html"))

    # Attach images
    for i, img in enumerate(imgfiles):
        part = MIMEBase("application", "octet-stream")
        part.set_payload(img.getvalue())
        Encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="plot{i}.{config.plotformat}"',
        )
        msg.attach(part)

    # Attach big numbers
    if config.algorithm == "double":
        part = MIMEBase("application", "octet-stream")
        part.set_payload(open(os.path.join("/tmp", config.start_time), "rb").read())
        Encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{config.start_time}.txt"',
        )
        msg.attach(part)

    # Attach plot data
    part = MIMEBase("application", "octet-stream")
    part.set_payload(
        open(os.path.join("/tmp", "plotdata" + config.start_time), "rb").read()
    )
    Encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="plotdata_{config.filename}_{config.start_time}.txt"',
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
    body = render_results(config, result, img_tags)

    if config.mail:
        if len(config.errors) == 0:
            # Send an email with the results
            send_email(config, body, imgfiles)
    else:
        # Return the page with results to be displayed immediately
        return body
