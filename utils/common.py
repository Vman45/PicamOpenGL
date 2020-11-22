class BaseNode:
    def __init__(self):
        self.next_node = None

    def set_next(self, node):
        self.next_node = node

    def run(self, input_obj):
        raise NotImplementedError

def set_nodes(node_list):
    max_len = len(node_list)
    for index, node in enumerate(node_list):
        next_index = index + 1
        # Last node will have default next_node as None
        if next_index < max_len:
            node.set_next(node_list[next_index])
            print("Current Node: {}, next: {}".format(node, node_list[next_index]))