import json
import logging
from copy import deepcopy

import structlog
from xml.dom import pulldom

#logging.basicConfig(level=logging.INFO)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR),
)
log = structlog.get_logger()


# doc = pulldom.parse('sample/page-6.xml')
# for event, node in doc:
#     if event == pulldom.START_ELEMENT and node.tagName == 'item':
#         if int(node.getAttribute('price')) > 50:
#             doc.expandNode(node)
#             print(node.toxml())

Xml2Json_NodePrototype = {"name": None, "attr": {}, "children": []}
class Xml2Json:
    """Converts to an expanded native structure which is less easy to work with but can represent any kind of XML structure without data loss"""
    def __init__(self, collapse_whitespace=True):
        self._node_proto = Xml2Json_NodePrototype
        self._collapse_whitespace = collapse_whitespace

    def to_native(self, from_file: str):
        xmldoc = pulldom.parse(from_file)
        root = curr_node = deepcopy(self._node_proto)
        lineage = [root]
        root_flag = False
        while True:
            _event = xmldoc.getEvent()
            match _event:
                case [pulldom.START_ELEMENT, xml_node]:
                    if root_flag is False:
                        root["name"] = xml_node.nodeName
                        root["attr"] = {x: y for x, y in xml_node.attributes.items()}
                        root_flag = True
                    else:
                        myself = deepcopy(self._node_proto)
                        myself["attr"] = {x: y for x, y in xml_node.attributes.items()}
                        myself["name"] = xml_node.nodeName
                        curr_node["children"].append(myself)
                        curr_node = myself
                        lineage.append(myself)
                    log.debug(pulldom.START_ELEMENT, xml_node=xml_node)
                case [pulldom.END_ELEMENT, xml_node]:
                    log.debug(pulldom.END_ELEMENT, xml_node=xml_node)
                    lineage.pop()
                    if len(lineage) > 0:
                        curr_node = lineage[-1:].pop()
                    else:
                        log.debug("bodge?")
                        curr_node = root
                case [pulldom.COMMENT, node]:
                    # ignore
                    log.debug(pulldom.COMMENT, node=node)
                case [pulldom.START_DOCUMENT, node]:
                    # ignore
                    log.debug(pulldom.START_DOCUMENT, node=node)
                case [pulldom.END_DOCUMENT, node]:
                    # ignore
                    log.debug(pulldom.END_DOCUMENT, node=node)
                case [pulldom.CHARACTERS, node]:
                    if self._collapse_whitespace is True:
                        text = node.nodeValue.strip()
                        if text != "":
                            curr_node["children"].append(text)
                    else:
                        curr_node["children"].append(node.nodeValue)
                    log.debug(pulldom.CHARACTERS, node=node)
                case [pulldom.PROCESSING_INSTRUCTION, node]:
                    log.debug(pulldom.PROCESSING_INSTRUCTION, node=node)
                case [pulldom.IGNORABLE_WHITESPACE, node]:
                    log.debug(pulldom.IGNORABLE_WHITESPACE, node=node)
                case None:
                    log.warn("<<out of bounds>>")
                    break
        return root




class XmlToNative:
    def __init__(self):
        self._node_proto = Xml2Json_NodePrototype

    def to_native(self, from_file: str):
        def _push_lineage(key, item):
            nonlocal lineage, curr_node, curr_key
            lineage.append((key, item))
            curr_node = item
            curr_key = key
        def _pop_lineage():
            nonlocal lineage, curr_node, curr_key
            lineage.pop()
            if len(lineage) > 0:
                curr_key, curr_node = lineage[-1:].pop()
            else:
                # log.debug("bodge?")
                curr_key, curr_node = None, root

        xmldoc = pulldom.parse(from_file)
        root = curr_node = {}
        curr_key = None
        lineage = [(None, root)]
        while True:
            _event = xmldoc.getEvent()
            match _event:
                case [pulldom.START_ELEMENT, xml_node]:
                    myself = {} if len(xml_node.attributes) == 0 else {x: y for x, y in xml_node.attributes.items()}
                    if xml_node.nodeName in curr_node:
                        if isinstance(curr_node[xml_node.nodeName], list) is False:
                            curr_node[xml_node.nodeName] = [curr_node[xml_node.nodeName]]
                        curr_node[xml_node.nodeName].append(myself)
                    else:
                        curr_node[xml_node.nodeName] = myself
                    _push_lineage(xml_node.nodeName, myself)
                    log.debug(pulldom.START_ELEMENT, xml_node=xml_node)
                case [pulldom.END_ELEMENT, xml_node]:
                    _pop_lineage()
                    log.debug(pulldom.END_ELEMENT, xml_node=xml_node)
                case [pulldom.COMMENT, node]:
                    # ignore
                    log.debug(pulldom.COMMENT, node=node)
                case [pulldom.START_DOCUMENT, node]:
                    # ignore
                    log.debug(pulldom.START_DOCUMENT, node=node)
                case [pulldom.END_DOCUMENT, node]:
                    # ignore
                    log.debug(pulldom.END_DOCUMENT, node=node)
                case [pulldom.CHARACTERS, node]:
                    log.debug(pulldom.CHARACTERS, node=node)
                    text = node.nodeValue.strip()
                    if text == "":
                        continue
                    if isinstance(curr_node, dict):
                        if len(curr_node) == 0:
                            my_key = curr_key
                            _pop_lineage()
                            curr_node[my_key] = text
                            _push_lineage(my_key, text)
                            continue
                    path = [x[0] for x in lineage]
                    raise RuntimeError("This converter does not support complex content at path " + ".".join(path))
                case [pulldom.PROCESSING_INSTRUCTION, node]:
                    log.debug(pulldom.PROCESSING_INSTRUCTION, node=node)
                case [pulldom.IGNORABLE_WHITESPACE, node]:
                    log.debug(pulldom.IGNORABLE_WHITESPACE, node=node)
                case None:
                    log.warn("<<out of bounds>>")
                    break
        return root




if __name__ == "__main__":
    xj = XmlToNative()
    #native = xj.to_native2("sample/page-6.xml")
    native = xj.to_native("sample/page-6.xml")
    json_data = json.dumps(native)
    log.info("eventual native", _is=native, json=json_data)
    print(json_data)