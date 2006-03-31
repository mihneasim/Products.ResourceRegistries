from xml.dom.minidom import parseString

from zope.app import zapi

from Products.CMFCore.utils import getToolByName

from Products.GenericSetup.interfaces import INode
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.utils import PrettyDocument
from Products.GenericSetup.utils import I18NURI
from Products.GenericSetup.utils import XMLAdapterBase


def importResRegistry(context, reg_id, reg_title, filename):
    """
    Import resource registry.
    """
    site = context.getSite()
    logger = context.getLogger('resourceregistry')
    res_reg = getToolByName(site, reg_id)

    body = context.readDataFile(filename)
    if body is None:
        logger.info("%s: Nothing to import" % reg_title)
        return

    importer = zapi.queryMultiAdapter((res_reg, context), IBody)
    if importer is None:
        logger.warning("%s: Import adapter missing." % reg_title)
        return

    importer.body = body
    logger.info("%s imported." % reg_title)

def exportResRegistry(context, reg_id, reg_title, filename):
    """
    Export resource registry.
    """
    site = context.getSite()
    logger = context.getLogger('resourceregistry')
    res_reg = getToolByName(site, reg_id, None)
    if res_reg is None:
        logger.info("%s: Nothing to export." % reg_title)
        return

    exporter = zapi.queryMultiAdapter((res_reg, context), IBody)
    if exporter is None:
        logger.warning("%s: Export adapter missing." % reg_title)
        return

    context.writeDataFile(filename, exporter.body, exporter.mime_type)
    logger.info("%s exported" % reg_title)


class ResourceRegistryNodeAdapter(XMLAdapterBase):

    def _exportNode(self):
        """
        Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        #node.setAttribute('xmlns:i18n', I18NURI)
        child = self._extractResourceInfo()
        node.appendChild(child)
        return node

    def _importNode(self, node):
        """
        Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            registry = getToolByName(self.context, self.registry_id)
            registry.clearResources()

        self._initResources(node)

    def _extractResourceInfo(self):
        """
        Extract the information for each of the registered resources.
        """
        fragment = self._doc.createDocumentFragment()
        registry = getToolByName(self.context, self.registry_id)
        resources = registry.getResources()
        for resource in resources:
            data = resource._data.copy()
            child = self._doc.createElement(self.resource_type)
            for key, value in data.items():
                if type(value) == type(True) or type(value) == type(0):
                    value = str(value)
                child.setAttribute(key, value)
            fragment.appendChild(child)
        return fragment

    def _initResources(self, node):
        """
        Initialize the registered resources based on the contents of
        the provided DOM node.
        """
        registry = getToolByName(self.context, self.registry_id)
        reg_method = getattr(registry, self.register_method)
        for child in node.childNodes:
            if child.nodeName != self.resource_type:
                continue

            data = {}
            for key, value in child.attributes.items():
                key = str(key)
                if key == 'id':
                    res_id = str(value)
                elif value.lower() == 'false':
                    data[key] = False
                elif value.lower() == 'true':
                    data[key] = True
                else:
                    try:
                        data[key] = int(value)
                    except ValueError:
                        data[key] = str(value)

            reg_method(res_id, **data)