#!/usr/bin/env python

import sys
import os

import cgi
import cgitb; cgitb.enable()
import matplotlib as mpl; mpl.use('Agg'); mpl.rc('text', usetex = True);

from starfit.autils.isotope import Ion
from starfit.autils.time2human import time2human

import starfit
from starfit.dbtrim import TrimDB as StarDB

from starfit.daemonize import createDaemon
from starfit.read import Star
from validate_email import validate_email

import smtplib


import base64
from io import BytesIO, StringIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders as Encoders
from datetime import datetime

global filename, dbname, sol_size, pop_size, email, mail, plotformat

def errorcheck():
    error = []
    try:
        test = Star(filename)
    except:
        error += ["There is something wrong with this stellar data."]

    try:
        test = StarDB(dbpath)
    except:
        error += ["There is something wrong with this database."]

    #Test if the input parameters are any good
    if sol_size > 10:
        error += ["Gene sizes greater than 10 are not supported."]

    if pop_size > 1000:
        error += ["Population sizes over 1000 are not supported."]

    mailcheck = validate_email(email, check_mx = False)

    if plotformat == 'pdf' and not mailcheck:
        error += ["PDF plot format must be emailed."]

    if mail and not mailcheck:
        if email == '':
            emailstr = "' '"
        else:
            emailstr = email
        error += ["{} is not a valid email.".format(emailstr)]
    return error

def method2human(
    algorithm,
    sol_size,
    z_max,
    comb,
    pop_size,
    time_limit,
    dbname,
    fixed,
    cdf,
):
    algorithm2h = 'Method: '
    if algorithm == 'ga':
        algorithm2h += 'Genetic Algorithm'
    elif algorithm == 'single':
        algorithm2h += 'Complete single star search'
    elif algorithm == 'double':
        algorithm2h += 'Complete double star search'


    z_max2h = 'Z max: ' + str(z_max)

    combine2h = 'Combined elements: '
    if comb == 0:
        combine2h += 'None'
    if comb == 1:
        combine2h += 'C+N'
    if comb == 2:
        combine2h += 'C+N+O'

    dbname2h = 'Model database: ' + dbname

    if fixed:
        fixed2h = 'Fixed offsets'
    else:
        fixed2h = 'Free offsets'

    if cdf:
        cdf2h = 'CDF upper limits'
    else:
        cdf2h = 'Simple upper limits'

    if algorithm == 'ga':
        pop_size2h = 'Population size: ' + str(pop_size)
        time_limit2h = 'Time limit: ' + str(time_limit)
        sol_size2h = 'Gene size: ' + str(sol_size)
        out = '<br />'.join((algorithm2h, sol_size2h, z_max2h, combine2h, pop_size2h, time_limit2h, dbname2h, fixed2h, cdf2h))
    else:
        out = '<br />'.join((algorithm2h, z_max2h, combine2h, dbname2h, fixed2h, cdf2h))

    return out


#this needs to print first
print("Content-Type: text/html; charset=UTF-8")

opentags = '''
<html>
<head>
<title>StarFit&trade;</title>
<link rel="stylesheet" type="text/css" href="../../index.css">
<link href='http://fonts.googleapis.com/css?family=Exo+2:300,100' rel='stylesheet' type='text/css'>
</head>
<body>
<div id="contentWrapper">
<div id="starfit">
    <a class = "title" href="/index.html">STARFIT</a>
</div>
'''
# <div id="testing">
#     <a class="subtitle" href="/index.html">TESTING</a>
# </div>
# '''
closetags = '''
<br />
<br />
<center>
<a href="http://moca.monash.edu/"><img src="../../images/mocalogo.png" width="120px"></a>
<br />
<a href="http://2sn.org/starfit/">Science Team</a>
</center>
</div>
</body>
</html>
'''

print(opentags)

# Retrieve form fields
form = cgi.FieldStorage()                     # Get POST data

try:
    stardata = form["stardata"]
except:
    sys.exit()

#filename  = str(form.getfirst("filename"))
email = str(form.getfirst("email"))
algorithm = str(form.getfirst("algorithm"))
sol_size  = int(form.getfirst("sol_size"))
z_max  = int(form.getfirst("z_max"))
comb  = int(form.getfirst("combine"))
pop_size  = int(form.getfirst("pop_size"))
time_limit  = int(form.getfirst("time_limit"))
dbname = str(form.getfirst("database"))
fixed = int(form.getfirst("fixed"))
plotformat = str(form.getfirst("plotformat"))
perfplot = form.getlist("perfplot")
z_exclude_str = str(form.getfirst("z_exclude"))
z_lolim_str = str(form.getfirst("z_lolim"))
cdf = bool(form.getfirst("cdf"))

z_exclude =  [z for z in [Ion(i).Z for i in z_exclude_str.split(',')] if z != 0]
z_lolim =  [z for z in [Ion(i).Z for i in z_lolim_str.split(',')] if z != 0]

if comb == 1:
    combine = [[6,7]]
elif comb == 2:
    combine = [[6,7,8]]
else:
    combine = [[]]

if perfplot == []:
    perfplot = 0

if email != '':
    forcemail = 1
else:
    forcemail = 0

start_time = datetime.now().strftime('%Y-%M-%d-%H-%M-%S')

#Save files to tmp
if stardata.filename:
    filename = os.path.join("/tmp", stardata.filename + start_time)
    with open(filename, 'wb') as fstar:
        fstar.write(stardata.file.read())
else:
    filename = os.path.join(starfit.DATA_DIR, 'stars', 'HE1327-2326.dat')

dbpath = os.path.join(starfit.DATA_DIR, 'db', dbname)

if ( forcemail ) or ( time_limit > 60 ) or ( plotformat in ['pdf', 'eps', 'ps'] ):
    mail = True
else:
    mail = False

error = errorcheck()
if error != []:
    for line in error:
        print(line, "<br />")
    print(closetags)
    sys.exit()

#Manually assign time_limit
if algorithm == "double":
    time_limit = 60 *15
elif algorithm == "single":
    time_limit = 0

if mail:
    print("Results will be mailed to {:} in {:}".format(
        email,
        time2human(time_limit) if (time_limit < 600) else 'the future...')
        )
    print(closetags)

    # Fork off if mailing
    sys.stdout.flush()
    createDaemon()

if algorithm == "ga":
    ## Run the fitting algorithm
    result = starfit.Ga(
        filename = filename,
        db = dbpath,
        time_limit = time_limit,
        pop_size = pop_size,
        sol_size = sol_size,
        local_search = True,
        z_max = z_max,
        z_exclude = z_exclude,
        z_lolim = z_lolim,
        combine = combine,
        fixed_offsets = fixed,
        cdf = cdf,
    )
elif algorithm == "double":
    sol_size = 2
    result = starfit.Double(
        filename = filename,
        db = dbpath,
        silent = True,
        n_top = 1000,
        combine = combine,
        fixed = fixed,
        save = True,
        webfile = start_time,
        cdf = cdf,
    )
elif algorithm == "single":
    sol_size = 1
    result = starfit.Single(
        filename = filename,
        db = dbpath,
        silent = True,
        combine = combine,
        z_max = z_max,
        z_exclude = z_exclude,
        z_lolim = z_lolim,
        cdf = cdf,
        )

#Make plots
imgfiles = []
plots = []
if algorithm in ['single', 'double']:
    plotrange = [0]
elif perfplot:
    plotrange = [0,1]
else:
    plotrange = [0]
for i in plotrange:
    result.plot(i+1)
    imgfile = BytesIO()

    #BUG
    mpl.pyplot.savefig(imgfile, format=plotformat)

    imgfiles += [imgfile]
    imgdata = imgfile.getvalue()
    plots += [str(base64.b64encode(imgdata))[2:-1]]

db = result.db

plotdatafile = os.path.join('/tmp', 'plotdata' + start_time)
with open(plotdatafile, mode = 'w') as f:
    f.write("Z      log(X/X_sun)\n")
    for z, abu in zip(result.plotdata[0], result.plotdata[1]):
        f.write("{:<2}     {:7.5f}\n".format(z, abu))

if mail:
    stringio = StringIO()
    previous_stdout = sys.stdout
    sys.stdout = stringio

print("<br />")
print('<div id="textWrapper">')

print("<b>Star:</b>")
print("<br />")
print(result.star.name)
print("<br />")
print("Max Z: ", z_max)
print("<br />")

exc_string = ', '.join([Ion(x).element_symbol() for x in z_exclude])
lol_string = ', '.join([Ion(x).element_symbol() for x in z_lolim])

if exc_string == '':
    exc_string = 'None'
if lol_string == '':
    lol_string = 'None'

print("Excluded elements: ", exc_string)
print("<br />")
print("Model lower limits: ", lol_string)
print("<br />")
print("<br />")

print("<b>Method:</b>")
print("<br />")

print(
    method2human(
        algorithm,
        sol_size,
        z_max,
        comb,
        pop_size,
        time_limit,
        dbname,
        fixed,
        cdf,
    )
)

print("<br />")
print("<br />")

print("<b>Best fitting models:</b>")
print("<br />")
print("<table>")
print(result.webtable())
print("</table>")
print('</div>')
print("<br />")

if not mail:
    print("<br />")
    for plot in plots:
        if plotformat == 'svg':
            typestr = plotformat + '+xml'
        else:
            typestr = plotformat
        img_tag = '<object data="data:image/{typestr};base64,{data}" type="image/{typestr}" width="700"></object>'.format(
            typestr = typestr,
            data = plot,
            )
        print(img_tag)
    print(closetags)


if mail:
    sys.stdout = previous_stdout
    body = stringio.getvalue()

    session = smtplib.SMTP('localhost')

    sender = 'results@starfit2.swin-dev.cloud.edu.au'

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = email
    msg['Subject'] = "StarFit Resulst"

    msg.attach( MIMEText(body, 'html') )

    #Attach images
    for i in plotrange:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( imgfiles[i].getvalue() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{:s}"'.format("plot" + str(i) + '.' + plotformat))
        msg.attach(part)

    #Attach big numbers
    if algorithm == "double":
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(os.path.join('/tmp', start_time),'rb').read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{:s}"'.format(start_time + '.txt'))
        msg.attach(part)

    #Attach plot data
    part = MIMEBase('application', "octet-stream")
    part.set_payload( open(os.path.join('/tmp', 'plotdata' + start_time),'rb').read() )
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="{:s}"'.format('plotdata_' + stardata.filename + '_' + start_time + '.txt'))
    msg.attach(part)

    #Attach input data
    if stardata.filename:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(filename,'rb').read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{:s}"'.format(stardata.filename))
        msg.attach(part)

    #Send!
    session.sendmail(sender, email, msg.as_string())
