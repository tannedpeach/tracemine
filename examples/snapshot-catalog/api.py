"""A tiny service boundary, independent of HTTP frameworks."""

from catalog import Catalog


class Service:
    def __init__(self):
        self.catalog = Catalog()

    def list_items(self):
        return {"items": self.catalog.list()}
