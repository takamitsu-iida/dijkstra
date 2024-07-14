#!/usr/bin/env python

# グラフのデータ構造はcytoscape.jsと同様の形式を想定しています。

# kruskal法は重み付き無向グラフの最小全域木を求めるアルゴリズムです。
# 最小全域木は、ノード数-1のエッジを持ち、全てのノードが連結されている木です。

# 一般的には計算量を削減できる素集合データ構造（Union-Findデータ構造）を用いて閉路を確認します。
# Union-Findについては別のスクリプトで実装します。

# ここではDFS深さ優先探索を用いて閉路を検知することにします。
# 辺を選ぶたびに深さ優先探索を走らせますので計算量が多く、大規模なグラフではUnion-Findを使うべきです。

# dfs_cycle_detect.pyからcycle_detect関数をインポートして利用します。
from dfs_cycle_detect import cycle_detect

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


def get_elements_from_edge_list(all_elements, edge_list: list) -> list:
    """
    edge_listで構成されるサブグラフのエレメントリストを返却する
    """
    sub_elements = []
    for edge in edge_list:
        source_id = edge.get('data').get('source')
        target_id = edge.get('data').get('target')
        source = get_element_by_id(all_elements, source_id)
        target = get_element_by_id(all_elements, target_id)
        if source is not None and target is not None:
            sub_elements.append(source)
            sub_elements.append(target)
            sub_elements.append(edge)
    return sub_elements


#
# Kruskal法による最小全域木の構築
#

def kruskal(elements: list, is_directed=False) -> list:

    # 最小全域木を構成するエッジのリスト
    minimum_spanning_tree_edges = []

    # エッジのリストを取得
    edges = get_edges(elements)

    # エッジをweightが小さい順にソートする
    edges.sort(key=lambda x: x.get('data').get('weight'))

    # グラフのノードがすべて結合しているなら、ノードの数-1だけエッジが選ばれた時点でMSTは完成する
    # 孤立したノードがいる場合もあるので、ここでは全エッジを検査することにする
    while len(edges) > 0:
        # コストが一番小さいエッジ、edgesリストの先頭を取り出す
        edge = edges.pop(0)
        logger.info(f"selected edge: {edge}")

        # いったんこのエッジを解に加えて
        minimum_spanning_tree_edges.append(edge)

        # そのグラフが閉路を持つかどうかをチェックする
        eles = get_elements_from_edge_list(elements, minimum_spanning_tree_edges)
        if cycle_detect(elements=eles, is_directed=is_directed):
            # 閉路ができるなら、このエッジを解に含めてはいけないので取り除く
            logger.info(f"Cycle detected. Removing edge: {edge}")
            minimum_spanning_tree_edges.pop(-1)

    return minimum_spanning_tree_edges


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

    def test_kruscal():
        print("--- Fig6.1 ---")
        elements = fig_6_1_elements
        #print(json.dumps(elements, indent=2))
        #print('')

        edges = kruskal(elements)
        print("--- Minimum Spanning Tree ---")
        print(f"number of nodes: {len(get_nodes(elements))}")
        print(f"number of MST edges: {len(edges)}")
        print(json.dumps(edges, indent=2))

    def main():
        test_kruscal()
        return 0

    # 実行
    sys.exit(main())
