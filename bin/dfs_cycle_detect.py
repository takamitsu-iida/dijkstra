#!/usr/bin/env python

# グラフのデータ構造はcytoscape.jsと同様の形式を想定しています。

# DFS深さ優先探索を用いて閉路検出を行うスクリプトです。

DATA_KEY = '_dfs'

def is_valid_element(element: dict) -> bool:
    if 'data' not in element:
        return False
    if 'id' not in element.get('data'):
        return False
    return True


def is_edge(element: dict) -> bool:
    if not is_valid_element(element):
        return False
    if element.get('group') == 'edges':
        return True
    if 'source' in element.get('data') and 'target' in element.get('data'):
        return True
    return False


def is_node(element) -> bool:
    if not is_valid_element(element=element):
        return False
    if element.get('group') == 'nodes':
        return True
    if 'source' in element.get('data') and 'target' in element.get('data'):
        return False
    return True


def get_edges(elements: list) -> list:
    return [ele for ele in elements if is_valid_element(ele) and is_edge(ele)]


def get_nodes(elements: list) -> list:
    return [ele for ele in elements if is_valid_element(ele) and is_node(ele)]


def get_neighborhood_ids(elements: list, node_id: str, is_directed=False) -> list:
    """
    node_idのノードと隣接するすべてのノードのidをリストで返却する
    """
    neighbor_ids = []

    # エレメントリスト内のエッジに関して
    for edge in get_edges(elements):

        # weightに0が設定されているものは通らないものとして扱う
        if edge.get('data').get('weight', 1) == 0 or edge.get('data').get('current_weight', 1) == 0:
            continue

        # edgeのsource側がnode_idと一致したなら、targetが隣接ノードになる
        if edge.get('data').get('source') == node_id:
            neighbor_ids.append(edge.get('data').get('target'))

        # 有向グラフでないの場合は、逆向きも追加する
        if is_directed == False and edge.get('data').get('target') == node_id:
            neighbor_ids.append(edge.get('data').get('source'))

    # 同一ノードペアに複数のエッジがあると中身が重複するので、重複を排除して返す
    return list(set(neighbor_ids))


def get_element_by_id(elements: list, id: str):
    """
    指定されたidのエレメントを取得する
    """
    for ele in elements:
        if ele.get('data', {}).get('id') == id:
            return ele
    return None

#
# 深さ優先探索(DFS)で閉域路を検出する
#

def cycle_detect(elements: list, start_id: str='', is_directed=False) -> bool:
    """
    深さ優先で探索しながら閉路の有無を確認する
    """

    # start_idのエレメントを取得
    if not start_id:
        start_node = get_nodes(elements)[0]
        start_id = start_node.get('data').get('id')
    else:
        start_node = get_element_by_id(elements, start_id)
        if not start_node:
            raise ValueError(f"start_id={start_id} not found in elements")

    # これから探索していく予定のノードのidを格納するリスト
    todo_list = []

    # 探索の過程で発見したノードの一覧
    visited = set()

    #
    # 初期化
    #

    # すべてのノードに_dfsという名前の辞書を追加しておく（DATA_KEYは'_dfs'を指す）
    for node in get_nodes(elements):
        node.get('data')[DATA_KEY] = {}

    # start_nodeのcycleをFalseにしておく
    start_node.get('data').get(DATA_KEY)['cycle'] = False

    # start_idを発見済みにしてから
    visited.add(start_id)

    # 探索予定のリストに追加する
    todo_list.append(start_id)

    #
    # 探索開始
    #

    while len(todo_list) > 0:

        # pop(-1)で最後のノードを取り出すとDFS 深さ優先探索になる
        # pop(0)で先頭から取り出すとBFS 幅優先探索になる
        current_id = todo_list.pop(-1)
        current_node = get_element_by_id(elements, current_id)

        # pointer_node_idは、current_idのノードにたどり着く一つ前のノードのidを指す
        pointer_node_id = current_node.get('data').get(DATA_KEY).get('pointer_node')

        # current_idの先にいる隣接ノードを取得する
        neighbor_node_ids = get_neighborhood_ids(elements, current_id, is_directed=is_directed)

        # current_idの隣接ノードに関して、
        for neighbor_node_id in neighbor_node_ids:
            # 隣接ノードのうち一つは必ずpointer_node_idになるので、それはスキップする
            if neighbor_node_id == pointer_node_id:
                continue

            # 隣接ノードがすでに発見済みのノード、ということはサイクル（閉路）を検出した、ということなので、それ以上の探索を中止する
            if neighbor_node_id in visited:
                start_node.get('data').get(DATA_KEY)['cycle'] = True
                break

            # 未発見のノードであれば、
            # どこからたどり着いたのかを、pointer_nodeに記録する
            neighbor_node = get_element_by_id(elements, neighbor_node_id)
            neighbor_node.get('data').get(DATA_KEY)['pointer_node'] = current_id

            # 発見済みに変更した上で、探索対象として追加
            visited.add(neighbor_node_id)
            todo_list.append(neighbor_node_id)

        # サイクルが検出されたら、それ以降の探索を中止する
        if start_node.get('data').get(DATA_KEY).get('cycle') == True:
            break

    return start_node.get('data').get(DATA_KEY).get('cycle')


if __name__ == '__main__':

    import sys

    def test_cycle_detection():

        loop_1 = [
            { 'group': 'nodes', 'data': { 'id': 's' } },
            { 'group': 'nodes', 'data': { 'id': 'A' } },
            { 'group': 'nodes', 'data': { 'id': 'B' } },
            { 'group': 'nodes', 'data': { 'id': 'C' } },
            { 'group': 'nodes', 'data': { 'id': 'D' } },
            { 'group': 'nodes', 'data': { 'id': 't' } },
            { 'group': 'edges', 'data': { 'id': 's_A', 'source': 's', 'target': 'A' } },
            { 'group': 'edges', 'data': { 'id': 's_B', 'source': 's', 'target': 'B' } },
            { 'group': 'edges', 'data': { 'id': 'A_C', 'source': 'A', 'target': 'C' } },
            { 'group': 'edges', 'data': { 'id': 'B_D', 'source': 'B', 'target': 'D' } },
            { 'group': 'edges', 'data': { 'id': 'C_t', 'source': 'C', 'target': 't' } },
            { 'group': 'edges', 'data': { 'id': 'D_t', 'source': 'D', 'target': 't' } },
        ]

        loop_2 = [
            { 'group': 'nodes', 'data': { 'id': 's' } },
            { 'group': 'nodes', 'data': { 'id': 'A' } },
            { 'group': 'nodes', 'data': { 'id': 'B' } },
            { 'group': 'nodes', 'data': { 'id': 'C' } },
            { 'group': 'nodes', 'data': { 'id': 't' } },
            { 'group': 'edges', 'data': { 'id': 's_A', 'source': 's', 'target': 'A' } },
            { 'group': 'edges', 'data': { 'id': 'A_C', 'source': 'A', 'target': 'C' } },
            { 'group': 'edges', 'data': { 'id': 'A_B', 'source': 'A', 'target': 'B' } },
            { 'group': 'edges', 'data': { 'id': 'B_C', 'source': 'B', 'target': 'C' } },
            { 'group': 'edges', 'data': { 'id': 'C_t', 'source': 'C', 'target': 't' } },
        ]

        print("--- Loop1 ---")
        # print(json.dumps(loop_1, indent=2) + "\n")
        cycle = cycle_detect(loop_1)
        print(f"cycle={cycle} \n")

        print("--- Loop2 ---")
        cycle = cycle_detect(loop_2)
        print(f"cycle={cycle} \n")
        print('')

    def main():
        test_cycle_detection()
        return 0

    # 実行
    sys.exit(main())
