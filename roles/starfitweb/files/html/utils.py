import base64
import sys
import traceback
from collections import Counter
from datetime import datetime
from itertools import chain
from os import getenv
from pathlib import Path

from cerberus import Validator
from email_validator import EmailNotValidError, validate_email
from starfit import DATA_DIR, DB, STARS, Star
from starfit.autils.human import time2human
from starfit.autils.isotope import ion as I

try:
    from starfit import __version__ as starfit_version
except ImportError:
    starfit_version = "unknown"


def convert_img_to_b64_tag(file, format):
    plot_b64 = str(base64.b64encode(file.getvalue()))[2:-1]
    if format == "pdf":
        typestr = "application/pdf"
        img_tag = f'<iframe src="data:{typestr};base64,{plot_b64}" type="{typestr}" width="100%" height="70%"></iframe>'
    else:
        typestr = f"image/{format}"
        if format == "svg":
            typestr += "+xml"
        img_tag = f'<object data="data:{typestr};base64,{plot_b64}" type="{typestr}" width="100%"></object>'
    return img_tag


def convert_element_string_to_charge_numbers(string):
    elements = list()
    for i in string.split(","):
        if len(ii := i.split("-")) > 1:
            ii = [I(k).Z for k in ii]
            if ii[0] == 0:
                ii[0] = 1
            if ii[1] == 0:
                ii[1] = 92
                ii = sorted(ii)
            elements.extend(list(range(ii[0], ii[1] + 1)))
        else:
            k = I(i).Z
            if k > 0:
                elements.append(k)
    return sorted(set(elements))


class Config(object):
    schema = dict(
        email={"type": "string", "coerce": str},
        algorithm={"type": "string", "coerce": str},
        sol_size={"type": "integer", "coerce": int},
        sol_sizes={"type": "string", "coerce": str},
        z_min={"type": "string", "coerce": str},
        z_max={"type": "string", "coerce": str},
        combine_mode={"type": "integer", "coerce": int},
        pop_size={"type": "integer", "coerce": int},
        yscale={"type": "integer", "coerce": int},
        time_limit={"type": "integer", "coerce": int},
        gen={"type": "integer", "coerce": int},
        tour_size={"type": "integer", "coerce": int},
        frac_mating_pool={"type": "integer", "coerce": int},
        frac_elite={"type": "integer", "coerce": int},
        mut_rate_index={"type": "integer", "coerce": int},
        mut_rate_offset={"type": "integer", "coerce": int},
        mut_offset_magnitude={"type": "integer", "coerce": int},
        fixed={"type": "boolean", "coerce": bool},
        plotformat={"type": "string", "coerce": str},
        stardefault={"type": "string", "coerce": str},
        z_exclude={"type": "string", "coerce": str},
        z_lolim={"type": "string", "coerce": str},
        upper_lim={"type": "boolean", "coerce": bool},
        cdf={"type": "boolean", "coerce": bool},
        det={"type": "boolean", "coerce": bool},
        cov={"type": "boolean", "coerce": bool},
        limit_solution={"type": "boolean", "coerce": bool},
        limit_solver={"type": "boolean", "coerce": bool},
        spread={"type": "boolean", "coerce": bool},
        local_search={"type": "boolean", "coerce": bool},
        group_ga={"type": "string", "coerce": str},
        group_multi={"type": "string", "coerce": str},
        pin={"type": "string", "coerce": str},
        multi={"type": "integer", "coerce": int},
        show_index={"type": "boolean", "coerce": bool},
    )

    def __init__(self, form):

        try:
            stardata = form["stardata"]
        except:
            traceback.print_exc(file=sys.stderr)
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

        dbx = form.getlist("database")
        if len(dbx) == 0:
            self.errors = ["Require at least one database selection."]
            return

        self.database = dbx

        self.gen = min(max(self.gen, 100), 10000)
        self.time_limit = min(max(self.time_limit, 1), 60)

        self.z_min = I(self.z_min)
        if not self.z_min.is_element:
            self.z_min = "H"
        else:
            self.z_min = self.z_min.Name()
        self.z_max = I(self.z_max)
        if not self.z_max.is_element:
            self.z_max = "U"
        else:
            self.z_max = self.z_max.Name()

        self.z_exclude = convert_element_string_to_charge_numbers(self.z_exclude)
        self.z_lolim = convert_element_string_to_charge_numbers(self.z_lolim)

        if self.algorithm == "ga":
            self.frac_mating_pool = self.frac_mating_pool * 0.01
            self.frac_elite = self.frac_elite * 0.01
            self.mut_rate_index = self.mut_rate_index * 0.01
            self.mut_rate_offset = self.mut_rate_offset * 0.01
            self.mut_offset_magnitude = self.mut_offset_magnitude * 0.01

        # Save files to tmp
        if stardata.filename:
            filepath = Path("/tmp") / (stardata.filename + self.start_time)
            with open(filepath, "wb") as fstar:
                fstar.write(stardata.file.read())
            filename = stardata.filename
        else:
            filename = self.stardefault
            filepath = Path(DATA_DIR) / STARS / filename

        self.filepath = filepath
        self.filename = filename
        self.dbpath = [Path(getenv("STARFIT_DATA")) / DB / db for db in self.database]
        self.mail = self.email != ""

        # Override time limit for some algorithms
        if self.algorithm == "multi":
            self.time_limit = 60 * 15
        elif self.algorithm == "single":
            self.time_limit = 0

        if self.time_limit < 1:
            eta = "now"
        elif self.time_limit > 600:
            eta = "in more than 10 minutes"
        else:
            eta = "in " + time2human(self.time_limit)
        self.time_eta = eta

        if self.algorithm not in ("ga", "multi", "single"):
            self.errors = [f"Bad choice of algorithm='{self.algorithm}'"]
            return

        if self.algorithm == "ga":
            self.group = self.group_ga
        elif self.algorithm == "multi":
            self.group = self.group_multi
        del self.group_ga
        del self.group_multi

        if self.algorithm in (
            "ga",
            "multi",
        ):
            ndb = len(self.database)
            groups = self.group.strip()
            if len(groups) > 0:
                try:
                    groups = [
                        [int(d) for d in g.split(",") if len(d) > 0]
                        for g in groups.split(";")
                    ]
                except:
                    self.errors = [
                        f"Group: Error translating string to nested list of integers: {groups}."
                    ]
                    return
                groups = [g for g in groups if len(g) > 0]
                gdb = list(chain(*groups))
                ngdb = len(gdb)
                for g in groups:
                    if len(g) <= 0:
                        self.errors = ["Group sizes must be larger than 0."]
                        return
                    if len(g) >= 10:
                        self.errors = ["Group sizes must be less than 10."]
                        return

                if len(set(gdb)) != ngdb:
                    self.errors = ["Require unique group entries."]
                    return
                if min(gdb) < 0:
                    self.errors = ["Require positive group entries."]
                    return
                if max(gdb) >= ndb:
                    self.errors = ["Require group entries in range."]
                    return
            else:
                groups = list()
            ngroup = len(groups)

        if self.algorithm == "multi":
            sol_sizes = self.sol_sizes.strip()
            try:
                sol_sizes = [int(i) for i in sol_sizes.split(";") if len(i) > 0]
            except:
                self.errors = [
                    f"Sizes: Error translating string to list of integers: {sol_sizes}"
                ]
                return
            nsol_sizes = len(sol_sizes)
            sol_size = sum(sol_sizes)

            if ngroup > 0:
                if ngdb < ndb:
                    if (nsol_sizes == ngroup + 1) or (
                        (nsol_sizes == 1) and (sol_size == ngroup + 1)
                    ):
                        # add remaining in one group
                        groups.append([d for d in range(ndb) if d not in gdb])
                        ngroup += 1
                    elif (nsol_sizes == ngroup + ndb - ngdb) or (
                        (nsol_sizes == 1) and (sol_size == ngroup + ndb - ngdb)
                    ):
                        # add remaining as separate groups
                        groups.extend([d for d in range(ndb) if d not in gdb])
                        ngroup = len(groups)
                    else:
                        # ignore nsol_size and put remaining in one group anyway
                        groups.append([d for d in range(ndb) if d not in gdb])
                        ngroup += 1
                        if nsol_sizes < ngroup:
                            sol_sizes.extend([1] * (ngroup - nsol_sizes))
                        else:
                            sol_sizes = sol_sizes[:ngroup]
                        nsol_sizes = len(sol_sizes)
                        sol_size = sum(sol_sizes)
                if (nsol_sizes == 0) or (nsol_sizes == 1 and ngroup == sol_size):
                    sol_sizes = [1] * ngroup
                    sol_size = sum(sol_sizes)
                    nsol_sizes = ngroup
                if nsol_sizes > ngroup:
                    sol_sizes = sol_sizes[:ngroup]
                    sol_size = sum(sol_sizes)
                    nsol_sizes = ngroup
                if nsol_sizes < ngroup:
                    sol_sizes = sol_sizes.extend([1] * (ngroup - nsol_sizes))
                    sol_size = sum(sol_sizes)
                    nsol_sizes = ngroup
            else:
                if nsol_sizes == 0:
                    groups = [[i] for i in range(ndb)]
                    sol_sizes = [1] * ndb
                    sol_size = ndb
                elif nsol_sizes == 1:
                    groups = [[i for i in range(ndb)]]
                elif nsol_sizes == ndb:
                    groups = [[i] for i in range(ndb)]
                elif nsol_sizes > ndb:
                    sol_sizes = sol_sizes[:ndb]
                    sol_size = sum(sol_sizes)
                else:
                    groups = groups[:nsol_sizes]

            self.group = groups
            self.sol_size = sol_size
            self.sol_sizes = sol_sizes

        elif self.algorithm == "ga":
            if ngroup > 0:
                if ngdb < ndb:
                    # add remaining as separate groups
                    groups.extend([d for d in range(ndb) if d not in gdb])
                    ngroup = len(groups)
            else:
                groups = None
                ngroup = ndb

            pin = self.pin.strip()
            try:
                pin = [int(i) for i in pin.split(";") if len(i) > 0]
            except:
                self.errors = [
                    f"Pin: Error translating string to list of integers: {pin}"
                ]
                return
            pin = [p for p in pin if p >= 0 and p < ngroup]
            if len(pin) > self.sol_size:
                pin = pin[: self.sol_size]

            self.group = groups
            self.pin = pin

        elif self.algorithm == "single":
            self.sol_size = 1

        # set vales so we can access rather than call functions
        self.combine = self.combine_elements()
        self.combined_elements_string = self.combine_elements_str(self.combine)
        self.algorithm_description = self.get_algorithm_description()
        self.database_string = ", ".join(self.database)
        self.n_database = str(len(self.database))
        if self.algorithm in (
            "multi",
            "ga",
        ):
            if self.group is None:
                self.group_string = ""
            else:
                self.group_string = "; ".join(
                    [", ".join([str(d) for d in g]) for g in self.group]
                )
        if self.algorithm == "multi":
            self.sol_sizes_string = "; ".join([str(i) for i in self.sol_sizes])
            self.grouping_string = "; ".join(
                [
                    f"{s} of ({', '.join([str(d) for d in g])})"
                    for s, g in zip(self.sol_sizes, self.group)
                ]
            )
        if self.algorithm == "ga":
            self.pin_string = "; ".join([str(p) for p in self.pin])
            c = Counter(self.pin)
            self.pinning_string = "; ".join([f"{k}:{v}" for k, v in c.items()])

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

    def combine_elements_str(self, combine):
        group_strings = []
        for group in combine:
            group_strings += ["+".join([I(i).element_symbol() for i in group])]
        output = ", ".join(group_strings)
        return output

    def get_algorithm_description(self):
        if self.algorithm == "ga":
            return "Genetic Algorithm (approximate best solution)"
        elif self.algorithm == "single":
            return "Complete search: single stars"
        elif self.algorithm == "multi":
            return "Complete multitstar search"

    def _check_for_errors(self):
        errors = []
        try:
            Star(self.filepath, silent=True)
        except:
            traceback.print_exc(file=sys.stderr)
            errors += ["There is something wrong with this stellar data."]

        # Test if the input parameters are any good
        if self.sol_size > 10:
            errors += ["Gene sizes greater than 10 are not supported."]

        if self.pop_size > 1000:
            errors += ["Population sizes over 1000 are not supported."]

        if self.time_limit > 60 and not self.mail:
            errors += ["Results must be emailed for time limit > 60s."]

        if self.mail:
            try:
                # Check that the email address is valid.
                validate_email(self.email, check_deliverability=True)

            except EmailNotValidError:
                traceback.print_exc(file=sys.stderr)
                errors += [f"{self.email} is not a valid email."]

        return errors


class JobInfo:
    def __init__(self, status=None, exc_info=None):
        self.status = status
        self.exc_info = exc_info
        self.starfit_version = starfit_version
