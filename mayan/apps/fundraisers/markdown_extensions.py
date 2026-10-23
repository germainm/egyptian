from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


class ExternalLinkTreeprocessor(Treeprocessor):
    def run(self, root):
        for element in root.iter(tag='a'):
            element.set('target', '_blank')

        return root


class ExternalLinkExtension(Extension):
    def extendMarkdown(self, md):
        treeprocessor = ExternalLinkTreeprocessor(md)

        md.treeprocessors.register(
            item=treeprocessor, name='external_link_target', priority=0
        )
