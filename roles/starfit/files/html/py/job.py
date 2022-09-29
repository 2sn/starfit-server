import starfit
from img_utils import convert_img_to_b64_tag
from plot import make_plots
from render import render
from starfit.autils.isotope import Ion
from starfit.autils.time2human import time2human


def process(config, start_time):
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

    return page, body, imgfiles
