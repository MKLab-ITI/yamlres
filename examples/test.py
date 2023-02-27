from yamlres import Loader, Runner
import pygrank as pg

specs = Loader(update=True).load("examples/hk.yaml")
algorithm = Runner().init(specs)

signal = next(pg.load_datasets_graph(["graph5"]))
print(algorithm(priors=signal))
