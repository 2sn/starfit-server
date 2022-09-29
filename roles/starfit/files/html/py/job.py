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
from render import render
from starfit.autils.isotope import Ion
from starfit.autils.time2human import time2human
from utils import convert_img_to_b64_tag

mpl.use("Agg")
mpl.rc("text", usetex=True)


def make_plots(result, algorithm, perfplot, plotformat, start_time):
    # File objects
    file_obj = []

    if algorithm in ["single", "double"]:
        plotrange = [0]
    elif perfplot:
        plotrange = [0, 1]
    else:
        plotrange = [0]

    # Write plots to file objects
    for i in plotrange:
        result.plot(i + 1)
        imgfile = BytesIO()
        mpl.pyplot.savefig(imgfile, format=plotformat)
        file_obj += [imgfile]

    # Save plot data to ASCII file
    plotdatafile = os.path.join("/tmp", "plotdata" + start_time)
    with open(plotdatafile, mode="w") as f:
        f.write("Z      log(X/X_sun)\n")
        for z, abu in zip(result.plotdata[0], result.plotdata[1]):
            f.write(f"{z:<2}     {abu:7.5f}\n")

    return file_obj


def send_email(config, body, imgfiles, start_time):
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
        part.set_payload(open(os.path.join("/tmp", start_time), "rb").read())
        Encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{start_time}.txt"',
        )
        msg.attach(part)

    # Attach plot data
    part = MIMEBase("application", "octet-stream")
    part.set_payload(open(os.path.join("/tmp", "plotdata" + start_time), "rb").read())
    Encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="plotdata_{config.stardata.filename}_{start_time}.txt"',
    )
    msg.attach(part)

    # Attach input data
    if config.stardata.filename:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(open(config.filename, "rb").read())
        Encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{config.stardata.filename}"',
        )
        msg.attach(part)

    # Send!
    session.sendmail(sender, config.email, msg.as_string())


def compute_and_render(config, start_time):
    if len(config.errors) == 0:

        time_limit = config.get_time_limit()
        time_eta = time2human(time_limit) if (time_limit < 600) else "the future..."
        combine = config.combine_elements()

        if config.algorithm == "ga":
            # Run the fitting algorithm
            result = starfit.Ga(
                filename=config.filename,
                db=config.dbpath,
                time_limit=time_limit,
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
                filename=config.filename,
                db=config.dbpath,
                silent=True,
                n_top=1000,
                combine=combine,
                fixed=config.fixed,
                save=True,
                webfile=start_time,
                cdf=config.cdf,
            )
        elif config.algorithm == "single":
            result = starfit.Single(
                filename=config.filename,
                db=config.dbpath,
                silent=True,
                combine=combine,
                z_max=config.z_max,
                z_exclude=config.z_exclude,
                z_lolim=config.z_lolim,
                cdf=config.cdf,
            )
        else:
            raise RuntimeError('Bad choice of "algorithm"')

        imgfiles = make_plots(
            result, config.algorithm, config.perfplot, config.plotformat, start_time
        )

        exc_string = ", ".join([Ion(x).element_symbol() for x in config.z_exclude])
        lol_string = ", ".join([Ion(x).element_symbol() for x in config.z_lolim])

        if exc_string == "":
            exc_string = "None"
        if lol_string == "":
            lol_string = "None"

        method_string = config.get_method_string()
        img_tags = [convert_img_to_b64_tag(f, config.plotformat) for f in imgfiles]

    else:
        # Set some values for render vars
        time_eta = ""
        result = None
        exc_string = ""
        lol_string = ""
        method_string = ""
        img_tags = []

    page, body = render(
        result,
        config.z_max,
        exc_string,
        lol_string,
        method_string,
        img_tags,
        config.mail,
        time_eta,
        config.errors,
    )

    if config.mail and len(config.errors) == 0:
        send_email(config, body, imgfiles, start_time)

    return page
