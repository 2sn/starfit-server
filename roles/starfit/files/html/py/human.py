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
    algorithm2h = "Method: "
    if algorithm == "ga":
        algorithm2h += "Genetic Algorithm"
    elif algorithm == "single":
        algorithm2h += "Complete single star search"
    elif algorithm == "double":
        algorithm2h += "Complete double star search"

    z_max2h = "Z max: " + str(z_max)

    combine2h = "Combined elements: "
    if comb == 0:
        combine2h += "None"
    if comb == 1:
        combine2h += "C+N"
    if comb == 2:
        combine2h += "C+N+O"

    dbname2h = "Model database: " + dbname

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
