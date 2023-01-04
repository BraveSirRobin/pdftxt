import json
import logging

import structlog
from xml.dom import pulldom

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR),
)
log = structlog.get_logger()


def xml_to_native(from_file: str, force_list_elements: list[str]=None, aliases: dict=None, protos: dict=None):
    """Attempt a generic mapping of the given XML document to a native Python dict/list structure.

    Not all valid XML will work here, complex content is not supported.  Name clashes between attributes and child
    elements wil result in data loss - child element wins (TODO: Fix this?).

    - Elements are mapped to equivalently nested dicts, if there's more than one sub-element sharing a  name, the
    resulting dict member becomes a list.
    - Use ``force_list_elements`` to force named elements to be rendered as a list, even if there's just a single
    named sibling.
    - Use ``aliases`` to rename elements in the mapped dict
    - Use protos to force a particular named element to always be mapped to a given dict structure, the default is
    an empty dict

    Args:
        from_file (str): XML data is in this file
        force_list_element (list[str], optional): Optional forced list map
        aliases (dict, optional): Optional aliases map
        protos (dict, optional): Optional prototype objects map
    """
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
            curr_key, curr_node = None, root

    aliases = {} if aliases is None else aliases
    protos = {} if protos is None else protos
    force_list_elements = [] if force_list_elements is None else force_list_elements
    xmldoc = pulldom.parse(from_file)
    root = curr_node = {}
    curr_key = None
    lineage = [(None, root)]
    while True:
        _event = xmldoc.getEvent()
        match _event:
            case [pulldom.START_ELEMENT, xml_node]:
                myself = protos[xml_node.nodeName] if xml_node.nodeName in protos else {}
                myself = myself | {x: y for x, y in xml_node.attributes.items()}
                node_name = aliases[xml_node.nodeName] if xml_node.nodeName in aliases else xml_node.nodeName
                if node_name in curr_node:
                    if isinstance(curr_node[node_name], list) is False:
                        curr_node[node_name] = [curr_node[node_name]]
                    curr_node[node_name].append(myself)
                elif node_name in force_list_elements:
                    curr_node[node_name] = [myself]
                else:
                    curr_node[node_name] = myself
                _push_lineage(node_name, myself)
                log.debug(pulldom.START_ELEMENT, xml_node=xml_node)
            case [pulldom.END_ELEMENT, xml_node]:
                _pop_lineage()
                log.debug(pulldom.END_ELEMENT, xml_node=xml_node)
            case [pulldom.CHARACTERS, xml_node]:
                log.debug(pulldom.CHARACTERS, node=xml_node)
                text = xml_node.nodeValue.strip()
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
            case [pulldom.END_DOCUMENT, _]:
                break
    return root




if __name__ == "__main__":
    # This prototype is used for all SP elements to make the resulting objects have the same keys for both
    # String and SP elements.  Combined with the alias, this means that we get a single collection of String
    # / SP elements in the correct order rather than 2 sibling sub-collections of each TextLine
    prototype_sp = {
        "ID": None,
        "CONTENT": None,
        "WC": None,
        "HEIGHT": None,
    }
    native = xml_to_native(
        "sample/page-6.xml",
        force_list_elements=["String"],
        aliases={"SP": "String"},
        protos={"SP": prototype_sp},
    )
    json_data = json.dumps(native)
    log.info("eventual native", _is=native, json=json_data)
    print(json_data)