import wget
import os
import yaml


class Loader:
    def __init__(self, path="res", update=False):
        self.path = path
        self.update = update

    def load(self, resource, exclude=None):
        resource = resource.replace(".yaml .", ".yaml.")
        if isinstance(resource, str) and ".yaml." in resource:
            parts = resource.split(".yaml.")
            resource = self.load(parts[0] + ".yaml", exclude)
            if exclude is not None and resource in exclude:
                raise Exception("Recursive reference of resource: " + resource)
            if len(parts) >= 2:
                for part in parts[1:]:
                    resource = resource[part]
            return resource

        if resource.startswith("https://"):
            download_path = os.path.join(self.path, resource[8:])
            os.makedirs(".".join(download_path.split(".")[:-1]), exist_ok=True)
            if not os.path.exists(download_path) or self.update:
                wget.download(resource, download_path)
            resource = download_path
        with open(resource, "r") as file:
            ret = yaml.load(file, Loader=yaml.SafeLoader)
        ret = self.extend(ret, [resource] if exclude is None else [resource] + exclude)
        return ret

    def extend(self, node, exclude):
        if isinstance(node, str) and ".yaml" in node:
            node = node.replace(".yaml .", ".yaml.")
            parts = node.split(".yaml.")
            if len(parts) >= 2:
                node = parts[0] + ".yaml"
            if node in exclude:
                raise Exception("Recursive reference of resource: " + node)
            node = self.load(node, exclude)
            if len(parts) >= 2:
                for part in parts[1].split("."):
                    node = node[part]
            return node
        if isinstance(node, list):
            return [self.extend(value, exclude) for value in node]
        if isinstance(node, dict):
            return {key: self.extend(value, exclude) for key, value in node.items()}
        return node
