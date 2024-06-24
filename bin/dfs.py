#!/usr/bin/env python

# グラフのデータ構造はcytoscape.jsと同様の形式であることを前提とする

#
# 標準ライブラリのインポート
#
import logging
import sys

from pathlib import Path

# このファイルへのPathオブジェクト
app_path = Path(__file__)

# このファイルの名前から拡張子を除いてプログラム名を得る
app_name = app_path.stem

# アプリケーションのホームディレクトリはこのファイルからみて一つ上
app_home = app_path.parent.joinpath('..').resolve()

# データ用ディレクトリ
data_dir = app_home.joinpath('data')

#
# ログ設定
#

# ログファイルの名前
log_file = app_path.with_suffix('.log').name

# ログファイルを置くディレクトリ
log_dir = app_home.joinpath('log')
log_dir.mkdir(exist_ok=True)

# ログファイルのパス
log_path = log_dir.joinpath(log_file)

# ロガーを取得する
logger = logging.getLogger(__name__)

# フォーマット
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 標準出力へのハンドラ
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

# ログファイルのハンドラ
#file_handler = logging.FileHandler(log_path, 'a+')
#file_handler.setFormatter(formatter)
#file_handler.setLevel(logging.INFO)
#logger.addHandler(file_handler)

#
# ここからスクリプト
#

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
# DFS 深さ優先探索
#

def dfs(elements: list, start_id: str, target_id='', is_directed=False) -> list:
    """
    深さ優先探索を行い、start_idからtarget_idまでの経路を返却する。
    pathsは [from, to] の形式で格納される。
    '_dfs'という名前の辞書をノードに追加してアップリンクノードを記録しているので
    別途、経路を遡って取得することもできる。
    """

    # target_idのエレメントを取得しておく
    target_node = get_element_by_id(elements, target_id)

    # たどった経路を格納するリスト
    # [from, to] の形式で格納する
    paths = []

    # これから探索していく予定のノードのidを格納するリスト
    todo_list = []

    # 探索の過程で発見したノードの一覧
    visited = set()

    #
    # 初期化
    #

    # すべてのノードに_dfsという名前の辞書を追加しておく（DATA_KEYは'_dfs'を指す）
    node_data = {}
    for node in get_nodes(elements):
        node.get('data')[DATA_KEY] = node_data

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

        if current_id == start_id:
            # ループの初回でスタートノードを処理している場合は記録すべき経路はまだ存在しない
            pass
        else:
            # このcurrent_idの上位ノードを取り出して、[from, to]の形式でpathsに追加
            current_node = get_element_by_id(elements, current_id)
            pointer_node_id = current_node.get('data').get(DATA_KEY).get('pointer_node')
            paths.append([pointer_node_id, current_id])

        # current_idの先にいる隣接ノードを取得する
        neighbor_node_ids = get_neighborhood_ids(elements, current_id, is_directed=is_directed)

        # ゴールになるノード target_id をその中に見つけたら探索途中でも処理を終了する
        if target_id in neighbor_node_ids:
            target_node.get('data').get(DATA_KEY)['pointer_node'] = current_id

            # 発見済みにしておくが、これで終了なので探索対象には追加しない
            visited.add(target_id)

            paths.append([current_id, target_id])
            break

        # current_idの隣接ノードに関して、
        for neighbor_node_id in neighbor_node_ids:
            # 発見済みのノードであれば（すでにtodo_listに入っているはずなので）ここでは何もしない
            if neighbor_node_id in visited:
                continue

            # どこからたどり着いたのかを、pointer_nodeに記録する
            neighbor_node = get_element_by_id(elements, neighbor_node_id)
            neighbor_node.get('data').get(DATA_KEY)['pointer_node'] = current_id

            # 発見済みにした上で、探索対象として追加
            visited.add(neighbor_node_id)
            todo_list.append(neighbor_node_id)

    logger.info(f"visited={visited}")
    logger.info(f"paths={paths}")

    return paths



if __name__ == '__main__':

    # ログレベル設定
    logger.setLevel(logging.INFO)

    import json

    # 図6.1
    fig_6_1_elements = [
        { 'group': 'nodes', 'data': { 'id': 's' } },
        { 'group': 'nodes', 'data': { 'id': 'A' } },
        { 'group': 'nodes', 'data': { 'id': 'B' } },
        { 'group': 'nodes', 'data': { 'id': 'C' } },
        { 'group': 'nodes', 'data': { 'id': 'D' } },
        { 'group': 'nodes', 'data': { 'id': 'E' } },
        { 'group': 'nodes', 'data': { 'id': 'F' } },
        { 'group': 'nodes', 'data': { 'id': 'G' } },
        { 'group': 'nodes', 'data': { 'id': 't' } },
        { 'group': 'edges', 'data': { 'id': 's_A', 'source': 's', 'target': 'A', 'weight': 5 } },
        { 'group': 'edges', 'data': { 'id': 's_B', 'source': 's', 'target': 'B', 'weight': 7 } },
        { 'group': 'edges', 'data': { 'id': 'A_C', 'source': 'A', 'target': 'C', 'weight': 8 } },
        { 'group': 'edges', 'data': { 'id': 'A_B', 'source': 'A', 'target': 'B', 'weight': 3 } },
        { 'group': 'edges', 'data': { 'id': 'B_D', 'source': 'B', 'target': 'D', 'weight': 3 } },
        { 'group': 'edges', 'data': { 'id': 'B_E', 'source': 'B', 'target': 'E', 'weight': 2 } },
        { 'group': 'edges', 'data': { 'id': 'C_D', 'source': 'C', 'target': 'D', 'weight': 4 } },
        { 'group': 'edges', 'data': { 'id': 'C_F', 'source': 'C', 'target': 'F', 'weight': 2 } },
        { 'group': 'edges', 'data': { 'id': 'D_F', 'source': 'D', 'target': 'F', 'weight': 1 } },
        { 'group': 'edges', 'data': { 'id': 'D_t', 'source': 'D', 'target': 't', 'weight': 4 } },
        { 'group': 'edges', 'data': { 'id': 'D_G', 'source': 'D', 'target': 'G', 'weight': 4 } },
        { 'group': 'edges', 'data': { 'id': 'E_D', 'source': 'E', 'target': 'D', 'weight': 3 } },
        { 'group': 'edges', 'data': { 'id': 'E_G', 'source': 'E', 'target': 'G', 'weight': 3 } },
        { 'group': 'edges', 'data': { 'id': 'F_t', 'source': 'F', 'target': 't', 'weight': 7 } },
        { 'group': 'edges', 'data': { 'id': 'G_t', 'source': 'G', 'target': 't', 'weight': 5 } }
    ]

    def test_dfs():
        print("--- Fig6.1 ---")
        elements = fig_6_1_elements
        print(json.dumps(elements, indent=2))
        print('')

        source_id = 's'
        paths = dfs(elements, source_id)
        print(f"dfs from {source_id}")
        print(paths)
        print('')

        target_id = 't'
        paths = dfs(elements, source_id, target_id)
        print(f"dfs from {source_id} to {target_id}")
        print(paths)
        print('')


    def main():
        test_dfs()
        return 0

    # 実行
    sys.exit(main())
