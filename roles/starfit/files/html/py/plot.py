import os
from io import BytesIO

import matplotlib as mpl

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
