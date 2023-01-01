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
                    log.info(pulldom.START_ELEMENT, xml_node=xml_node)
                case [pulldom.END_ELEMENT, xml_node]:
                    log.info(pulldom.END_ELEMENT, xml_node=xml_node)
                    lineage.pop()
                    if len(lineage) > 0:
                        curr_node = lineage[-1:].pop()
                    else:
                        log.info("bodge?")
                        curr_node = root
                case [pulldom.COMMENT, node]:
                    # ignore
                    log.info(pulldom.COMMENT, node=node)
                case [pulldom.START_DOCUMENT, node]:
                    # ignore
                    log.info(pulldom.START_DOCUMENT, node=node)
                case [pulldom.END_DOCUMENT, node]:
                    # ignore
                    log.info(pulldom.END_DOCUMENT, node=node)
                case [pulldom.CHARACTERS, node]:
                    if self._collapse_whitespace is True:
                        text = node.nodeValue.strip()
                        if text != "":
                            curr_node["children"].append(text)
                    else:
                        curr_node["children"].append(node.nodeValue)
                    log.info(pulldom.CHARACTERS, node=node)
                case [pulldom.PROCESSING_INSTRUCTION, node]:
                    log.info(pulldom.PROCESSING_INSTRUCTION, node=node)
                case [pulldom.IGNORABLE_WHITESPACE, node]:
                    log.info(pulldom.IGNORABLE_WHITESPACE, node=node)
                case None:
                    log.warn("<<out of bounds>>")
                    break
        return root


if __name__ == "__main__":
    xj = Xml2Json()
    native = xj.to_native("sample/page-6.xml")
    json_data = json.dumps(native)
    log.info("eventual native", _is=native, json=json_data)
    print(json_data)