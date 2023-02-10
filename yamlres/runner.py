import warnings


def pipeline(*args):
    arg = args[0]
    for step in args[1:]:
        arg = step(arg)
    return arg


class Runner:
    def __init__(self, trust: list = None, global_methods=None):
        self.trust = None if trust is None else set(trust)
        self.global_methods = {"pipeline": pipeline} if global_methods is None else global_methods

    def get(self, values: dict, name):
        if isinstance(name, str) and "." in name:
            parts = name.split(".")
            obj = self.get(values, parts[0])
            for part in parts[1:]:
                obj = getattr(obj, part)
            return obj
        if isinstance(name, str) and name in values:
            name = values[name]
        if isinstance(name, dict) and "method" in name:
            return self.exec(name, values)
        return name

    def exec(self, specs, values: dict = None):
        assert isinstance(specs, dict)
        values = dict() if values is None else values
        for k, v in self.global_methods.items():
            if k not in values:
                values[k] = v
        method = self.get(values, specs["method"])
        args = specs.get("args", list())
        if not isinstance(args, list):
            args = [args]
        args = [self.get(values, v) for v in args]
        kwargs = {k: self.get(values, v) for k, v in specs.get("kwargs", dict()).items()}
        return method(*args, **kwargs)

    def init(self, specs):
        def runner(**values):
            return self.run(specs, **values)
        return runner

    def run(self, specs, **values):
        results = self._run(specs, values)
        if len(results) == 1 and "" in results:
            return results[""]
        return results

    def _run(self, specs, values: dict):
        results = dict()
        if isinstance(specs, list):
            for spec in specs:
                results = results | self._run(spec, values)
        elif isinstance(specs, dict):
            if "method" in specs:
                return self.exec(specs, values)
            for key, value in specs.items():
                if key == "definitions":
                    continue
                elif key == "import":
                    for name, lib in value.items():
                        if self.trust is not None and lib not in self.trust:
                            raise Exception("Trying to import a non-trusted library: "+lib+" (should be in {"+",".join(self.trust)+"})")
                        if name in values:
                            continue
                            # raise Exception("Import name "+str(name)+" already in use")
                        values[name] = __import__(lib)
                elif key == "set" or key == "return":
                    if key == "return" and (not isinstance(value, dict) or "method" in value):
                        value = {"": value}
                    for name, val in value.items():
                        if name in values:
                            if key == "return":
                                results[name] = values[name]
                            continue
                            # raise Exception("Cannot set name "+str(name)+" already in use")
                        if isinstance(val, dict):
                            values[name] = self.exec(val, values)
                        else:
                            values[name] = self.get(values, val)
                        if key == "return":
                            results[name] = values[name]
                else:
                    raise Exception("Invalid command: "+key+" (should be in {definitions, import, set, get, method, args, kwargs})")
        else:
            raise Exception("Can only run a list or dict")
        return results
