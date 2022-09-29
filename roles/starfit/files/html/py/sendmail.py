import os
import smtplib
from email import encoders as Encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from socket import gethostname


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
