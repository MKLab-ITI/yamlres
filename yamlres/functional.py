def pipeline(*args):
    arg = args[0]
    for step in args[1:]:
        arg = step(arg)
    return arg


def builder(method, *args, **kwargs):
    def runner(*eargs, **ekwargs):
        return method(*args, *eargs, **kwargs, **ekwargs)
    return runner
