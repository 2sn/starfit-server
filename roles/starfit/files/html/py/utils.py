import base64
import os
import sys

import starfit
from cerberus import Validator
from error_check import check
from starfit.autils.isotope import Ion


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

    def __init__(self, form, start_time):
        try:
            self.stardata = form["stardata"]
        except:
            sys.exit()

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
        if self.stardata.filename:
            filename = os.path.join("/tmp", self.stardata.filename + start_time)
            with open(filename, "wb") as fstar:
                fstar.write(self.stardata.file.read())
        else:
            filename = os.path.join(starfit.DATA_DIR, "stars", "HE1327-2326.dat")

        self.filename = filename
        self.dbpath = os.path.join(starfit.DATA_DIR, "db", self.database)
        self.mail = self.email != ""

        self.errors = self._check_for_errors()

        if self.algorithm == "double":
            self.sol_size = 2
        elif self.algorithm == "single":
            self.sol_size = 1

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
        return check(
            self.filename,
            self.dbpath,
            self.sol_size,
            self.pop_size,
            self.time_limit,
            self.plotformat,
            self.mail,
            self.email,
        )

    def get_time_limit(self):
        # Manually assign time_limit
        if self.algorithm == "double":
            time_limit = 60 * 15
        elif self.algorithm == "single":
            time_limit = 0
        return time_limit
