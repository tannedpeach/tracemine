"""Atomic JSON-tree edits. Paths are sequences of dict keys or list indices."""

from copy import deepcopy


def locate(document, path):
    for part in path:
        document = document[part]
    return document


def edit(document, operations):
    """Copy the input, then apply sequential operations; a failure discards the copy."""
    result = deepcopy(document)
    for operation in operations:
        kind, path = operation["op"], operation["path"]
        if kind == "test":
            if locate(result, path) != operation["value"]:
                raise ValueError("test failed")
            continue
        if kind not in {"set", "remove", "append", "copy"}:
            raise ValueError("unsupported operation")
        if kind == "copy":
            value = deepcopy(locate(result, operation["from"]))
        elif kind != "remove":
            value = deepcopy(operation["value"])
        if not path:
            if kind in {"set", "copy"}:
                result = value
            elif kind == "append":
                result.append(value)
            else:
                raise ValueError("cannot remove root")
            continue
        parent = locate(result, path[:-1])
        if kind == "remove":
            del parent[path[-1]]
        elif kind == "append":
            parent[path[-1]].append(value)
        else:
            parent[path[-1]] = value
    return result
