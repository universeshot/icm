import json
import itertools

def parse_tree(lines):
    stack = []
    nodes = {}
    counter = itertools.count()

    def new_id():
        return f"node:{next(counter)}"

    root_id = None

    for raw in lines:
        if not raw.strip():
            continue

        indent = len(raw) - len(raw.lstrip())
        label = raw.strip()

        node_id = new_id()
        node = {
            "type": "node",
            "value": parse_value(label),
            "children": []
        }
        nodes[node_id] = node

        while stack and stack[-1][0] >= indent:
            stack.pop()

        if stack:
            parent_id = stack[-1][1]
            nodes[parent_id]["children"].append(node_id)
        else:
            root_id = node_id

        stack.append((indent, node_id))

    return {
        "format": "treechain/v1",
        "root": root_id,
        "nodes": nodes
    }


def parse_value(text):
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


if __name__ == "__main__":
    with open("tree.dsl") as f:
        tree = parse_tree(f.readlines())

    with open("tree.json", "w") as f:
        json.dump(tree, f, indent=2)
