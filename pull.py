import json
import logging
import argparse
from pathlib import Path

#from xml.dom import pulldom
from defusedxml import pulldom


def xml_to_native(from_file: Path, force_list_elements: list[str]=None, aliases: dict=None, proto_masks: dict=None):
    """Attempt a generic mapping of the given XML document to a native Python dict/list structure.

    Not all valid XML will work here, complex content is not supported.  Name clashes between attributes and child
    elements wil result in data loss - child element wins (TODO: Fix this?).

    - Elements are mapped to equivalently nested dicts, if there's more than one sub-element sharing a  name, the
    resulting dict member becomes a list.
    - Use ``force_list_elements`` to force named elements to be rendered as a list, even if there's just a single
    named sibling.
    - Use ``aliases`` to rename elements in the mapped dict
    - Use proto_masks to force a particular named element to always be mapped to a given dict structure, the default is
    an empty dict.  **the non-alises element name is used to detect when the prototype is applied**

    Args:
        from_file (str): XML data is in this file
        force_list_element (list[str], optional): Optional forced list map
        aliases (dict, optional): Optional aliases map
        proto_masks (dict, optional): Optional prototype objects map
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

    if from_file.stat().st_size == 0:
        return {}
    aliases = {} if aliases is None else aliases
    proto_masks = {} if proto_masks is None else proto_masks
    force_list_elements = [] if force_list_elements is None else force_list_elements
    xmldoc = pulldom.parse(str(from_file))
    root = curr_node = {}
    curr_key = None
    lineage = [(None, root)]
    while True:
        _event = xmldoc.getEvent()
        match _event:
            case ["START_ELEMENT", xml_node]:
                myself = proto_masks[xml_node.nodeName] if xml_node.nodeName in proto_masks else {}  # nodeName not aliased
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
            case ["END_ELEMENT", xml_node]:
                _pop_lineage()
            case ["CHARACTERS", xml_node]:
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
            case ["END_DOCUMENT", _]:
                break
    return root


def parse_command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src-xml-file", type=Path, required=True)
    parser.add_argument("--dest-json-file", type=Path, required=True)
    args = parser.parse_args()

    if args.src_xml_file.exists() is False:
        raise RuntimeError("file given in --src-xml-file cannot be found")
    return args


if __name__ == "__main__":
    # This prototype mask is used for all SP elements to make the resulting objects
    # have the same keys for both String and SP elements.  Combined with the alias,
    # this means that each TextLine maps to a collection of String/SP elements that
    # reflects the XML document order, rather than 2 sibling sub-collections of
    # SP / String.  e.g.

    # LIKE THIS
    # {"TextLine": {
    #       ...
    #       "String": [
    #           {}, {}, {}, {}
    #       ]
    #   }
    # }

    # THIS WOULD BE THE DEFAULT OTHERWISE
    # {"TextLine": {
    #       ...
    #       "String": [
    #           {}, {}
    #       ],
    #       "SP": [
    #           {}, {}
    #       ]
    #   }
    # }


    sp_mask = {
        "ID": None,
        "CONTENT": None,
        "WC": None,
        "HEIGHT": None,
    }
    cli_args = parse_command_line_args()
    native = xml_to_native(
        cli_args.src_xml_file,
        force_list_elements=["String"],
        aliases={"SP": "String"},
        proto_masks={"SP": sp_mask},
    )
    json.dump(native, cli_args.dest_json_file.open("w"))