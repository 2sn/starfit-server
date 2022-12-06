import os
import smtplib
from email import encoders as Encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from pathlib import Path
from socket import gethostname

import jinja2 as j2
import matplotlib as mpl
import numpy as np
from starfit import Ga, Multi, Single
from starfit.autils.human import time2human
from starfit.autils.isotope import ion as I
from utils import JobInfo, convert_img_to_b64_tag

jinja_env = j2.Environment(loader=j2.FileSystemLoader("templates"))

mpl.use("Agg")
mpl.rc("text", usetex=True)


def compute(config):
    if config.algorithm == "ga":
        # Run the fitting algorithm
        result = Ga(
            filename=config.filepath,
            db=config.dbpath,
            silent=True,
            combine=config.combine,
            z_min=config.z_min,
            z_max=config.z_max,
            z_exclude=config.z_exclude,
            z_lolim=config.z_lolim,
            upper_lim=config.upper_lim,
            cdf=config.cdf,
            det=config.det,
            cov=config.cov,
            limit_solution=config.limit_solution,
            limit_solver=config.limit_solver,
            time_limit=config.time_limit,
            fixed_offsets=config.fixed,
            sol_size=config.sol_size,
            group=config.group,
            pin=config.pin,
            gen=config.gen,
            pop_size=config.pop_size,
            spread=config.spread,
            tour_size=config.tour_size,
            frac_mating_pool=config.frac_mating_pool,
            frac_elite=config.frac_elite,
            mut_rate_index=config.mut_rate_index,
            mut_rate_offset=config.mut_rate_offset,
            mut_offset_magnitude=config.mut_offset_magnitude,
            local_search=config.local_search,
        )
    elif config.algorithm == "multi":
        result = Multi(
            filename=config.filepath,
            db=config.dbpath,
            silent=True,
            combine=config.combine,
            z_min=config.z_min,
            z_max=config.z_max,
            z_exclude=config.z_exclude,
            z_lolim=config.z_lolim,
            upper_lim=config.upper_lim,
            cdf=config.cdf,
            det=config.det,
            cov=config.cov,
            limit_solution=config.limit_solution,
            limit_solver=config.limit_solver,
            fixed_offsets=config.fixed,
            sol_size=config.sol_sizes,
            group=config.group,
            n_top=1000,
            save=True,
            webfile=config.start_time,
        )
    elif config.algorithm == "single":
        result = Single(
            filename=config.filepath,
            db=config.dbpath,
            silent=True,
            combine=config.combine,
            z_min=config.z_min,
            z_max=config.z_max,
            z_exclude=config.z_exclude,
            z_lolim=config.z_lolim,
            upper_lim=config.upper_lim,
            cdf=config.cdf,
            det=config.det,
            cov=config.cov,
            limit_solution=config.limit_solution,
            limit_solver=config.limit_solver,
        )
    else:
        result = None
    return result


def compressed_ion_list(string):
    if len(string.strip()) == 0:
        return ""
    zz = sorted([I(x).Z for x in string.split(",")])
    out = list()
    z0 = z1 = zz[0]
    for z in zz[1:]:
        if z == z1 + 1:
            z1 = z
        else:
            if z1 == z0:
                out.append(I(z1).Name())
            elif z1 == z0 + 1:
                out.extend([I(z0).Name(), I(z1).Name()])
            else:
                out.append(f"{I(z0).Name()} &mdash; {I(z1).Name()}")
            z0 = z1 = z
    if z1 == z0:
        out.append(I(z1).Name())
    elif z1 == z0 + 1:
        out.extend([I(z0).Name(), I(z1).Name()])
    else:
        out.append(f"{I(z0).Name()} &mdash; {I(z1).Name()}")
    return ", ".join(out)


def set_star_values(result, config):
    config.star_name = result.star.name
    config.star_version = int(result.star.version)
    config.star_abundance_norm = result.star.get_norm()
    config.star_input_data_format = result.star.get_input_data_format()
    config.star_n_covariances = result.star.get_n_covariances()
    config.star_covariances = compressed_ion_list(
        ", ".join(result.star.get_covariances())
    )
    config.star_detection_thresholds = compressed_ion_list(
        ", ".join(result.star.get_detection_thresholds())
    )
    config.star_upper_limits = compressed_ion_list(
        ", ".join(result.star.get_upper_limits())
    )
    config.star_elements = compressed_ion_list(", ".join(result.star.get_elements()))
    config.star_measured = compressed_ion_list(", ".join(result.star.get_measured()))
    config.star_solar = result.star.solar_ref
    if config.star_solar is None:
        config.star_solar = ""
    if isinstance(config.star_solar, Path):
        config.star_solar = config.star_solar.name
    if hasattr(result.star, "source"):
        config.star_reference = result.star.source
    if config.star_reference is None:
        config.star_reference = ""
    config.star_notes = result.star.comment
    config.star_filename = config.filename
    if config.algorithm == "ga":
        config.text_tour_size = str(config.tour_size)
        config.text_frac_mating_pool = f"{config.frac_mating_pool:4.2f}"
        config.text_frac_elite = f"{config.frac_elite:4.2f}"
        config.text_mut_rate_index = f"{config.mut_rate_index:4.2f}"
        config.text_mut_rate_offset = f"{config.mut_rate_offset:4.2f}"
        config.text_mut_offset_magnitude = f"{config.mut_offset_magnitude:4.2f}"


def set_result_values(result, config):
    config.text_result = result.text_result(
        10, format="html", show_index=config.show_index
    )
    config.text_db = result.text_db(filename=True)
    config.text_db_n_columns = str(len(config.text_db[0]))
    if config.algorithm == "ga":
        config.text_generations = str(result.gen)
        config.text_time = time2human(result.elapsed)
    if config.algorithm == "multi":
        config.multi_combinations = (
            f"{result.n_combinations:,d} combinations of {result.sol_size} stars"
        )
        if len(result.group) > 1:
            config.multi_partitions = (
                f"{' &#xd7; '.join(str(i) for i in result.group_comb)}"
            )
        else:
            config.multi_partitions = ""
    config.text_detection_thresholds = ", ".join(
        [
            x.element.Name()
            for x in result.eval_data
            if x.detection > -80.0 and x.element.Z not in config.z_exclude
        ]
    )
    config.text_detection_thresholds = compressed_ion_list(
        config.text_detection_thresholds
    )
    if len(config.text_detection_thresholds) == 0:
        config.text_detection_thresholds = "None"
    config.text_covariances = ", ".join(
        [
            x.element.Name()
            for x in result.eval_data
            if np.any(x.covariance != 0.0) and x.element.Z not in config.z_exclude
        ]
    )
    config.text_covariances = compressed_ion_list(config.text_covariances)
    if len(config.text_covariances) == 0:
        config.text_covariances = "None"

    eval_elements = [x.element.Z for x in result.eval_data]
    config.lolim_string = ", ".join(
        [
            I(x).Name()
            for x in config.z_lolim
            if x in eval_elements and x not in config.z_exclude
        ]
    )
    config.lolim_string = compressed_ion_list(config.lolim_string)

    star_elements_full = [I(x).Z for x in result.star.get_elements()]
    star_elements = [
        z
        for z in star_elements_full
        if z >= I(config.z_min).Z and z <= I(config.z_max).Z
    ]
    config.exclude_string = ", ".join(
        [I(x).Name() for x in config.z_exclude if x in star_elements]
    )
    config.exclude_string = compressed_ion_list(config.exclude_string)

    config.ignored_string = ", ".join(
        [I(x).Name() for x in star_elements_full if x not in star_elements]
    )
    config.ignored_string = compressed_ion_list(config.ignored_string)

    upper_limits = [I(x).Z for x in result.star.get_upper_limits()]
    config.matched_elements_string = ", ".join(
        [
            I(x).Name()
            for x in eval_elements
            if not (
                (x in config.z_exclude) or (x in config.z_lolim) or (x in upper_limits)
            )
        ]
    )
    config.matched_elements_string = compressed_ion_list(config.matched_elements_string)

    config.upper_limits_string = ", ".join(
        [
            I(x).Name()
            for x in upper_limits
            if x not in config.z_exclude and x in eval_elements
        ]
    )
    config.upper_limits_string = compressed_ion_list(config.upper_limits_string)

    if config.upper_lim is False:
        config.upper_exclude_string = ", ".join(
            [
                I(x).Name()
                for x in star_elements
                if not (x in config.z_exclude or x in eval_elements)
            ]
        )
    else:
        config.upper_exclude_string = ""


def make_plots(result, config):

    # File objects
    file_obj = []

    # Abundance plot
    imgfile = BytesIO()
    labels, plotdata = result.plot(
        save=imgfile,
        save_format=config.plotformat,
        return_plot_data=True,
        yscale=config.yscale,
        ynorm="Fe",
        multi=config.multi,
    )
    file_obj += [imgfile]

    if config.algorithm == "ga":
        result.plot_fitness(gen=True)
        imgfile = BytesIO()
        mpl.pyplot.savefig(imgfile, format=config.plotformat)
        file_obj += [imgfile]

    if config.plot_cov:
        result.plot_error_matrix(zoom=False)
        imgfile = BytesIO()
        mpl.pyplot.savefig(imgfile, format=config.plotformat)
        file_obj += [imgfile]

    # Save plot data to ASCII file
    plotdatafile = os.path.join("/tmp", "plot_data_points" + config.start_time)
    with open(plotdatafile, mode="w") as f:
        for l in labels:
            f.write(f"{l}\n")
        f.write("\n")
        f.write("Z      log(X/X_sun)\n")
        for z, abu in zip(plotdata[0], plotdata[1]):
            f.write(f"{z:<2}     {abu:7.5f}\n")

    return file_obj


def render(config, result, img_tags, doc, jobinfo):
    if doc in ("configerror", "resultpage", "sendmail", "jobfail", "email"):
        template = jinja_env.get_template(f"{doc}.html")
    else:
        raise RuntimeError("Bad choice of 'doc'")

    return template.render(
        config=config,
        result=result,
        img_tags=img_tags,
        jobinfo=jobinfo,
        hostname=gethostname(),
    )


def send_email(config, body, imgfiles):
    session = smtplib.SMTP(gethostname())
    sender = f"results@{gethostname()}"
    mailto = (
        "starfit.results@gmail.com?subject=Unsubscribe&body=%5BAutomated"
        "%20message%5D%0D%0APlease%20unsubscribe%20me%20from%20all%20future%20emails."
    )

    msg = MIMEMultipart()
    msg["From"] = f"StarFit <{sender}>"
    msg["To"] = config.email
    msg["Bcc"] = "starfit.results@gmail.com"
    msg["Subject"] = "StarFit Results"
    msg.add_header(
        "List-Unsubscribe",
        f"<mailto:{mailto}>, <https://{gethostname()}/unsubscribe>",
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
    if config.algorithm == "multi":
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
    set_star_values(result, config)
    set_result_values(result, config)
    imgfiles = make_plots(result, config)
    img_tags = [convert_img_to_b64_tag(f, config.plotformat) for f in imgfiles]
    jobinfo = JobInfo()

    page = render(config, result, img_tags, doc="resultpage", jobinfo=jobinfo)
    email = render(config, result, img_tags, doc="email", jobinfo=jobinfo)

    if config.mail:  # Send an email with the results
        send_email(config, email, imgfiles)

    return page
