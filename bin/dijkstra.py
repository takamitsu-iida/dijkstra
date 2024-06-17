#!/usr/bin/env python

import sys

# グラフのデータ構造はcytoscape.jsと同様の形式であることを前提とする
# see data/elements.json

#
# 標準ライブラリのインポート
#
import json
import logging

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

# ログレベル設定
logger.setLevel(logging.INFO)

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


def get_neighborhood_ids(elements: list, node_id: str) -> list:
    """
    node_idのノードと隣接するすべてのノードのidをリストで返却する
    """
    neighbor_ids = []

    # エレメントリスト内のエッジに関して
    for edge in get_edges(elements):

        # edgeのsource側がnode_idと一致したなら、targetが隣接ノードになる
        if edge.get('data').get('source') == node_id:
            neighbor_ids.append(edge.get('data').get('target'))

        # target側が一致したなら、sourceが隣接ノードになる
        elif edge.get('data').get('target') == node_id:
            neighbor_ids.append(edge.get('data').get('source'))

    # 同一ノードペアに複数のエッジがあると中身が重複するので、重複を排除して返す
    return list(set(neighbor_ids))


def get_edges_between(elements: list, node_a: str, node_b: str) -> list:
    """
    node_aとnode_bの間にあるエッジをすべて取得する
    """
    between_edges = []
    # エレメントリスト内のエッジに関して
    for edge in get_edges(elements):

        # source側がnode_a、target側がnode_bの場合、もしくはその逆の場合
        if edge.get('data').get('source') == node_a and edge.get('data').get('target') == node_b:
            between_edges.append(edge)
        elif edge.get('data').get('source') == node_b and edge.get('data').get('target') == node_a:
            between_edges.append(edge)

    return between_edges


def get_minimum_weight_edges(edges: list) -> list:
    """
    渡されたエッジのリストから最小の重みを持つエッジをすべて取得する
    """
    min_weight = sys.maxsize
    min_weight_edges = []
    for edge in edges:
        w = edge.get('data').get('weight', 1)
        if w == min_weight:
            min_weight_edges.append(edge)
        elif w < min_weight:
            min_weight = w
            min_weight_edges = [edge]

    return min_weight_edges


def get_ids(elements: list) -> list:
    """
    渡されたエレメントリストにあるエレメントのidの一覧を返却する
    """
    ids = []
    for ele in elements:
        if is_valid_element(ele) == False:
            continue
        ids.append(ele.get('data').get('id'))
    return ids


def get_element_by_id(elements: list, id: str):
    """
    指定されたidのエレメントを取得する
    """
    for ele in elements:
        if ele.get('data', {}).get('id') == id:
            return ele
    return None


def get_minimum_distance_nodes_from_unvisited(elements: list) -> list:
    """
    指定されたエレメントのリストのうち、
    未訪問でかつ
    最小のdistanceを持つノードを取得する
    """
    min_distance = sys.maxsize
    min_distance_nodes = []
    for node in get_nodes(elements):
        # 空間Lに格納済み、すなわち訪問済みのノードは無視する
        if node.get('data').get('_dijkstra').get('visited') == True:
            continue

        # 始点からの距離を取り出す
        distance = node.get('data').get('_dijkstra').get('distance')
        # 最小値と同じ距離ならリストに追加
        if distance == min_distance:
            min_distance_nodes.append(node)
        # より小さい距離が見つかればリストを初期化して追加
        elif distance < min_distance:
            min_distance = distance
            min_distance_nodes = [node]

    return min_distance_nodes


def exists_unvisited_node(elements: list) -> bool:
    """
    未訪問のノードが存在するかどうかを返却する
    """
    for node in get_nodes(elements):
        if node.get('data').get('_dijkstra').get('visited') == False:
            return True
    return False


def calc_dijkstra(elements: list, source_id: str):

    # 指定されたsource_idのオブジェクトを取り出しておく
    source = get_element_by_id(elements, source_id)
    if source is None:
        raise ValueError(f"source_id={source_id} is not found.")

    #
    # STEP1
    #

    # δ(v)はノードvの v['data']['_dijkstra']['distance'] を指すことにする

    # sourceの距離、すなわちδ(source)を0とし、その他ノードは無限大に初期化する
    for node in get_nodes(elements):

        # このアルゴリズムの途中経過で用いるデータの保存先を初期化する
        _dijkstra = {}
        node.get('data')['_dijkstra'] = _dijkstra

        # sourceから各ノードに至る距離distanceを初期化する
        if node.get('data')['id'] == source_id:
            _dijkstra['distance'] = 0
        else:
            _dijkstra['distance'] = sys.maxsize

        # 探索済みのノードの集合 L は、visitedフラグで管理する
        # 全ノードを未探索の状態に初期化する
        _dijkstra['visited'] = False

    #
    # STEP2
    #

    # 頂点sourceを集合 L に入れる、すなわちvisitedフラグを立てる
    source.get('data').get('_dijkstra')['visited'] = True

    # 次にsourceに隣接している各頂点 v について
    for v_id in get_neighborhood_ids(elements, source_id):

        # v_idのオブジェクトを取得しておく
        v = get_element_by_id(elements, v_id)

        # 利便性のため、保存先オブジェクトを取り出しておく
        _dijkstra = v.get('data').get('_dijkstra')

        # 2-1. δ(v)=w(source, v)に更新する

        # source_idとv_idの間にあるエッジをすべて取得する
        edges = get_edges_between(elements, source_id, v_id)

        # その中から最小の重みを持つエッジだけを取得
        edges = get_minimum_weight_edges(edges)

        # それらエッジのidの一覧を取得する
        edge_ids = get_ids(edges)

        # 重みを取得する、なければ1とする
        weight = edges[0].get('data').get('weight', 1)

        # δ(v)をその重みに設定する
        _dijkstra['distance'] = weight

        # 2-2. vはポインタでsourceを指す
        # ポインタはノードだけでなくエッジも指すことにする
        _dijkstra['pointer_nodes'] = [source_id]
        _dijkstra['pointer_edges'] = edge_ids

    #
    # 次のSTEP3の処理を、全ノードが集合Lに格納されるまで続ける
    #

    while exists_unvisited_node(elements):

        #
        # STEP3
        #

        # まだLに入っていない頂点、すなわちvisitedがFalseのノードの中で δ が最小のものを選びvとする
        min_distance_nodes = get_minimum_distance_nodes_from_unvisited(elements)

        # vの候補が複数ある場合は任意の一つを選ぶ（先頭の要素を選ぶ）
        v = min_distance_nodes[0]
        v_id = v.get('data').get('id')

        # vをLに入れる、すなわちvisitedフラグを立てる
        # どこにもつながってない孤立したノードであっても、この時点でvisitedになる
        v.get('data').get('_dijkstra')['visited'] = True

        # 次にこのvに隣接している頂点のうち、
        for u_id in get_neighborhood_ids(elements, v_id):

            u = get_element_by_id(elements, u_id)

            # まだLに入っていない頂点 u に対して、すなわち訪問済みは無視して、
            if u.get('data').get('_dijkstra').get('visited') == True:
                continue

            # 3-1. δ(u)の新しい値を
            # δ(u) = min(δ(u), δ(v) + w(v, u))
            # とする

            # vとuの間のエッジをすべて取得する
            edges = get_edges_between(elements, v_id, u_id)

            # その中から最小の重みを持つエッジだけを取得
            edges = get_minimum_weight_edges(edges)

            # それらエッジのidの一覧を取得する
            edge_ids = get_ids(edges)

            # エッジに付与されている重みを取得する
            weight = edges[0].get('data').get('weight')

            # 3-2. δ(u)の値と、v経由の距離で比較して、小さい経路が見つかれば更新する
            # δ(u)を更新した、すなわち新しい経路を見つけたなら、uはポインタでvを指す
            if u.get('data').get('_dijkstra').get('distance') < v.get('data').get('_dijkstra').get('distance') + weight:
                # 既存の値の方が小さい場合は更新しない
                logger.info(f"skip: v={v_id}, u={u_id}, u-distance={u.get('data').get('_dijkstra').get('distance')}, new={v.get('data').get('_dijkstra').get('distance') + weight}")
                continue
            elif u.get('data').get('_dijkstra').get('distance') == v.get('data').get('_dijkstra').get('distance') + weight:
                # 既存の値と同じ場合は、その経路も使える、ということなのでポインタを追加する
                logger.info(f"add: v={v_id}, u={u_id}, u-distance={u.get('data').get('_dijkstra').get('distance')}, new={v.get('data').get('_dijkstra').get('distance') + weight}")
                u.get('data').get('_dijkstra')['pointer_nodes'].append(v_id)
                u.get('data').get('_dijkstra')['pointer_edges'].extend(edge_ids)
            else:
                # 既存の値より小さい場合は更新する
                logger.info(f"update: v={v_id}, u={u_id}, u-distance={u.get('data').get('_dijkstra').get('distance')}, new={v.get('data').get('_dijkstra').get('distance') + weight}")
                u.get('data').get('_dijkstra')['distance'] = v.get('data').get('_dijkstra').get('distance') + weight
                u.get('data').get('_dijkstra')['pointer_nodes'] = [v_id]
                u.get('data').get('_dijkstra')['pointer_edges'] = edge_ids


if __name__ == '__main__':


    def get_elements_from_file(file_path: Path) -> list:
        elements = []
        with open(file_path) as f:
            elements = json.load(f)

        nodes = get_nodes(elements)
        node_ids = get_ids(nodes)
        for edge in get_edges(elements):
            source = edge.get('data').get('source')
            target = edge.get('data').get('target')
            if source not in node_ids or target not in node_ids:
                raise ValueError(f"edge={edge.get('data').get('id')} has invalid source={source} or target={target}")

        return elements

    def dump_nodes(elements: list):
        nodes = get_nodes(elements)
        nodes = sorted(nodes, key=lambda x: x.get('data').get('_dijkstra').get('distance'))
        for node in nodes:
            print(f"{node.get('data').get('id')}, parent={node.get('data').get('_dijkstra').get('pointer_nodes')}, distance={node.get('data').get('_dijkstra').get('distance')}")

    def main():

        # dataディレクトリにあるJSONファイルからエレメントを取得する
        #data_file_name = 'fig-3-6.json'
        data_file_name = 'fig-3-7.json'

        data_file_path = data_dir.joinpath(data_file_name)
        elements = get_elements_from_file(data_file_path)

        # 始点ノードのid
        source_id = 's'

        # ダイクストラ法で最短経路を計算する
        calc_dijkstra(elements, source_id)

        # 結果を表示する
        dump_nodes(elements)

        return 0

    # 実行
    sys.exit(main())
