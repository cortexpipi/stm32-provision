

class Tag:
    def __init__(self, node):
        self.node = node
        self.attrs = {k.lower(): v for k, v in node.attributes.items()}

    @property
    def tagName(self):
        return self.node.tagName

    @property
    def children(self):
        for child in self.node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                yield Tag(child)

    @property
    def text(self):
        res = ''
        for child in self.node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                res += child.data
        return res