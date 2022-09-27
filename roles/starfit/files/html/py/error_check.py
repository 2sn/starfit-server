from email_validator import EmailNotValidError, validate_email
from starfit.dbtrim import TrimDB as StarDB
from starfit.read import Star


def check(filename, dbpath, sol_size, pop_size, plotformat, mail, email):
    error = []
    try:
        Star(filename)
    except:
        error += ["There is something wrong with this stellar data."]

    try:
        StarDB(dbpath)
    except:
        error += ["There is something wrong with this database."]

    # Test if the input parameters are any good
    if sol_size > 10:
        error += ["Gene sizes greater than 10 are not supported."]

    if pop_size > 1000:
        error += ["Population sizes over 1000 are not supported."]

    if mail:
        try:
            # Check that the email address is valid.
            validate_email(email, check_deliverability=True)

        except EmailNotValidError:
            error += [f"{email} is not a valid email."]

    if plotformat == "pdf" and not mail:
        error += ["PDF plot format must be emailed."]

    return error
