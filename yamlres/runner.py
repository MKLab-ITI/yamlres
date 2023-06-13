import importlib


class Runner:
    def __init__(self, trust: list = None, globals=None):
        self.trust = None if trust is None else set(list(trust)+["yamlres.functional"])
        self.globals = dict() if globals is None else globals

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
        if isinstance(name, list):
            return [self.get(values, v) for v in name]
        if isinstance(name, dict):
            return {k: self.get(values, v) for k, v in name.items()}
        return name

    def exec(self, specs, values: dict = None):
        assert isinstance(specs, dict)
        values = dict() if values is None else values
        for k, v in self.globals.items():
            if k not in values:
                values[k] = v
        method = self.get(values, specs["method"])
        args = specs.get("args", list())
        if not isinstance(args, list):
            args = [args]
        args = [self.get(values, v) for v in args]
        kwargs = {
            k: self.get(values, v) for k, v in specs.get("kwargs", dict()).items()
        }
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
                            raise Exception(
                                "Trying to import a non-trusted library: "
                                + lib
                                + " (should be in {"
                                + ",".join(self.trust)
                                + "})"
                            )
                        if name in values:
                            continue
                            # raise Exception("Import name "+str(name)+" already in use")
                        values[name] = importlib.import_module(lib)
                elif key == "assign" or key == "return":
                    if key == "return" and (
                        not isinstance(value, dict) or "method" in value
                    ):
                        value = {"": value}
                    for name, val in value.items():
                        if name in values:
                            if key == "return":
                                results[name] = values[name]
                            continue
                            # raise Exception("Cannot assign name "+str(name)+" already in use")
                        if isinstance(val, dict):
                            values[name] = self.exec(val, values)
                        else:
                            values[name] = self.get(values, val)
                        if key == "return":
                            results[name] = values[name]
                else:
                    raise Exception(
                        "Invalid command: "
                        + key
                        + " (should be in {definitions, import, assign, get, method, args, kwargs})"
                    )
        else:
            raise Exception("Can only run a list or dict")
        return results
