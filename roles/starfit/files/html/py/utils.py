import base64
import os
import sys
from datetime import datetime

import starfit
from cerberus import Validator
from email_validator import EmailNotValidError, validate_email
from starfit.autils.isotope import Ion
from starfit.autils.time2human import time2human
from starfit.dbtrim import TrimDB as StarDB
from starfit.read import Star


def method2human(
    algorithm,
    sol_size,
    z_max,
    combine_mode,
    pop_size,
    time_limit,
    database,
    fixed,
    cdf,
):
    algorithm2h = "Method: "
    if algorithm == "ga":
        algorithm2h += "Genetic Algorithm"
    elif algorithm == "single":
        algorithm2h += "Complete single star search"
    elif algorithm == "double":
        algorithm2h += "Complete double star search"

    z_max2h = "Z max: " + str(z_max)

    combine2h = "Combined elements: "
    if combine_mode == 0:
        combine2h += "None"
    if combine_mode == 1:
        combine2h += "C+N"
    if combine_mode == 2:
        combine2h += "C+N+O"

    dbname2h = "Model database: " + database

    if fixed:
        fixed2h = "Fixed offsets"
    else:
        fixed2h = "Free offsets"

    if cdf:
        cdf2h = "CDF upper limits"
    else:
        cdf2h = "Simple upper limits"

    if algorithm == "ga":
        pop_size2h = "Population size: " + str(pop_size)
        time_limit2h = "Time limit: " + str(time_limit)
        sol_size2h = "Gene size: " + str(sol_size)
        out = "<br />".join(
            (
                algorithm2h,
                sol_size2h,
                z_max2h,
                combine2h,
                pop_size2h,
                time_limit2h,
                dbname2h,
                fixed2h,
                cdf2h,
            )
        )
    else:
        out = "<br />".join((algorithm2h, z_max2h, combine2h, dbname2h, fixed2h, cdf2h))

    return out


def convert_img_to_b64_tag(file, format):
    plot_b64 = str(base64.b64encode(file.getvalue()))[2:-1]
    typestr = format
    if format == "svg":
        typestr += "+xml"
    img_tag = f'<object data="data:image/{typestr};base64,{plot_b64}" type="image/{typestr}" width="700"></object>'

    return img_tag


class Config:
    schema = dict(
        email={"type": "string", "coerce": str},
        algorithm={"type": "string", "coerce": str},
        sol_size={"type": "integer", "coerce": int},
        z_max={"type": "integer", "coerce": int},
        combine_mode={"type": "integer", "coerce": int},
        pop_size={"type": "integer", "coerce": int},
        time_limit={"type": "integer", "coerce": int},
        database={"type": "string", "coerce": str},
        fixed={"type": "integer", "coerce": int},
        plotformat={"type": "string", "coerce": str},
        perfplot={"type": "boolean", "coerce": bool},
        z_exclude={"type": "string", "coerce": str},
        z_lolim={"type": "string", "coerce": str},
        cdf={"type": "boolean", "coerce": bool},
    )

    def __init__(self, form):
        try:
            stardata = form["stardata"]
        except:
            sys.exit()

        self.start_time = datetime.now().strftime("%Y-%M-%d-%H-%M-%S")

        v = Validator(require_all=True)

        conf = {}
        for key in self.schema:
            conf[key] = form.getfirst(key)

        if not v.validate(conf, self.schema):
            raise RuntimeError("Bad form input")

        for key, value in v.document.items():
            self.__setattr__(key, value)

        self.z_exclude = [
            z for z in [Ion(i).Z for i in self.z_exclude.split(",")] if z != 0
        ]
        self.z_lolim = [
            z for z in [Ion(i).Z for i in self.z_lolim.split(",")] if z != 0
        ]

        # Save files to tmp
        if stardata.filename:
            filepath = os.path.join("/tmp", stardata.filename + self.start_time)
            with open(filepath, "wb") as fstar:
                fstar.write(stardata.file.read())
            filename = stardata.filename
        else:
            filename = "HE1327-2326.dat"
            filepath = os.path.join(starfit.DATA_DIR, "stars", filename)

        self.filepath = filepath
        self.filename = filename
        self.dbpath = os.path.join(starfit.DATA_DIR, "db", self.database)
        self.mail = self.email != ""

        # Override time limit for some algorithms
        if self.algorithm == "double":
            time_limit = 60 * 15
        elif self.algorithm == "single":
            time_limit = 0
        self.time_limit = time_limit
        self.time_eta = (
            time2human(time_limit) if (time_limit < 600) else "the future..."
        )

        if self.algorithm not in ("ga", "double", "single"):
            raise RuntimeError('Bad choice of "algorithm"')

        if self.algorithm == "double":
            self.sol_size = 2
        elif self.algorithm == "single":
            self.sol_size = 1

        # Check for errors after all the config has been handled
        self.errors = self._check_for_errors()

    def combine_elements(self):
        """Preset element combinations"""
        if self.combine_mode == 1:
            combine = [[6, 7]]
        elif self.combine_mode == 2:
            combine = [[6, 7, 8]]
        else:
            combine = [[]]

        return combine

    def get_method_string(self):
        return method2human(
            self.algorithm,
            self.sol_size,
            self.z_max,
            self.combine_mode,
            self.pop_size,
            self.time_limit,
            self.database,
            self.fixed,
            self.cdf,
        )

    def _check_for_errors(self):
        errors = []
        try:
            Star(self.filename)
        except:
            errors += ["There is something wrong with this stellar data."]

        try:
            StarDB(self.dbpath)
        except:
            errors += ["There is something wrong with this database."]

        # Test if the input parameters are any good
        if self.sol_size > 10:
            errors += ["Gene sizes greater than 10 are not supported."]

        if self.pop_size > 1000:
            errors += ["Population sizes over 1000 are not supported."]

        if self.time_limit > 60 and self.mail:
            errors += ["Results must be emailed for time limit > 60s."]

        if self.mail:
            try:
                # Check that the email address is valid.
                validate_email(self.email, check_deliverability=True)

            except EmailNotValidError:
                errors += [f"{self.email} is not a valid email."]

        if self.plotformat == "pdf" and not self.mail:
            errors += ["PDF plot format must be emailed."]

        return errors
