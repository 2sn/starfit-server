import os
import sys

import starfit
from cerberus import Validator
from error_check import check
from human import method2human
from starfit.autils.isotope import Ion


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
