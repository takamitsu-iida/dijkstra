#!/usr/bin/env python

# グラフのデータ構造はcytoscape.jsと同様の形式を想定しています。
# テストで用いているグラフはdataフォルダにjson形式で格納してあります。

# ダイクストラ法は、始点から各ノードへの最短経路を求めるアルゴリズムです。
# ルーティングプロトコルのOSPFやISISにも使われています。

# このスクリプトではsourceからtargetに至る最短経路をリストで返します。
# イコールコストマルチパスに対応していますので、複数の最短経路が返ることがあります。
# 以下の実行例では、fig-3-7.jsonの解が3つ返ってきています。
#
# --- fig-3-6.json ---
# [['s', 'A', 'E', 'C', 'F', 't']]
#
# --- fig-3-7.json ---
# [['s', 'A', 'C', 't'], ['s', 'B', 'D', 't'], ['s', 'A', 'B', 'D', 't']]


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

# 隣接行列からcytoscape.jsのエレメント形式に変換
def convert_adj_matrix_to_elements(adj_matrix: list)->list:
    # ノードのidは1始まりの数値
    nodes = []
    for i in range(len(adj_matrix)):
        node_id = i + 1
        node = {
            'group': "nodes",
            'data': {
                'id': f"{node_id}",
            }
        }
        nodes.append(node)

    edges = []
    for i, row in enumerate(adj_matrix):
        source_node_id = i + 1
        for j in range(i+1, len(row)):
            if (row[j] == 0):
                continue
            target_node_id = j + 1
            edge = {
                'group': "edges",
                'data': {
                    'id': f"{source_node_id}_{target_node_id}",
                    'source': f"{source_node_id}",
                    'target': f"{target_node_id}",
                    'weight': row[j]
                }
            }
            edges.append(edge)

    elements = []
    elements.extend(nodes)
    elements.extend(edges)

    return elements


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


def get_edges_between(elements: list, source: str, target: str, is_directed=False) -> list:
    """
    sourceとtargetの間にあるエッジをすべて取得する
    """
    between_edges = []
    # エレメントリスト内のエッジに関して
    for edge in get_edges(elements):

        # weightに0が設定されているものは通らないものとして扱う
        if edge.get('data').get('weight', 1) == 0:
            continue

        # source側がnode_a、target側がnode_bの場合、もしくはその逆の場合
        if edge.get('data').get('source') == source and edge.get('data').get('target') == target:
            between_edges.append(edge)
        elif is_directed == False and edge.get('data').get('source') == target and edge.get('data').get('target') == source:
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


#
# Dijkstraアルゴリズム
#

def calc_dijkstra(elements: list, source_id: str, is_directed=False):

    # ノードのdataに_dijkstraという名前の辞書を追加し、そこに計算結果を保存する
    # この辞書には以下のキーが含まれる
    #   - distance: 始点からの距離
    #   - visited: 訪問済みかどうか（確定済みの集合Lに含まれるかどうか）
    #   - pointer_nodes: このノードに至る最短経路の直前のノードのidのリスト（等コストの場合は複数）
    #   - pointer_edges: このノードに至る最短経路のエッジのidのリスト（等コストの場合は複数）
    #
    # この関数ではsource_idを頂点とした最短経路の計算を行う
    # 特定の場所にたどり着くための経路を知りたければget_dijkstra_paths()を利用する

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

    # このステップはSTEP3の処理の中で行うこともできる
    # ここでは本に記載の通り、分けて記述している

    # 頂点sourceを集合 L に入れる、すなわちvisitedフラグを立てる
    source.get('data').get('_dijkstra')['visited'] = True

    # 次にsourceに隣接している各頂点 v について
    for v_id in get_neighborhood_ids(elements, source_id, is_directed=is_directed):

        # v_idのオブジェクトを取得しておく
        v = get_element_by_id(elements, v_id)

        # 利便性のため、保存先オブジェクトを取り出しておく
        _dijkstra = v.get('data').get('_dijkstra')

        # 2-1. δ(v)=w(source, v)に更新する

        # source_idとv_idの間にあるエッジをすべて取得する
        edges = get_edges_between(elements, source_id, v_id, is_directed=is_directed)

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
        _dijkstra['pointer_nodes'] = [source_id] # 配列として保存
        _dijkstra['pointer_edges'] = edge_ids  # edge_idsはもともと配列

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
        for u_id in get_neighborhood_ids(elements, v_id, is_directed=is_directed):

            u = get_element_by_id(elements, u_id)

            # まだLに入っていない頂点 u に対してのみ、すなわち訪問済みは無視して、
            if u.get('data').get('_dijkstra').get('visited') == True:
                continue

            # 3-1. δ(u)の新しい値を
            # δ(u) = min(δ(u), δ(v) + w(v, u))
            # とする

            # vとuの間のエッジをすべて取得する
            edges = get_edges_between(elements, v_id, u_id, is_directed=is_directed)

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


def get_dijkstra_paths(all_paths: list, current_paths: list, elements: list, from_id: str):
    """
    from_idからアップリンク方向に遡る最短経路をすべて取得する
    """

    # all_paths: 最短経路のリストを格納するリスト
    # current_paths: 現在の経路を格納するリスト
    # elements: グラフデータ
    # from_id: 終点のノードid

    # ノードエレメントには、_dijkstraという名前の辞書が追加されている
    # distance: 始点からそのノードまでの距離
    # pointer_nodes: そのノードに至る最短経路の上位ノードのidのリスト（等コストの場合は複数）
    # pointer_edges: そのノードに至る最短経路のエッジのidのリスト（等コストの場合は複数）
    # これらの情報を使って最短経路を取得する

    # current_pathsは再帰呼び出しのたびに変更されるので、
    # この関数内で変更を加えると、呼び出し元に影響が出る
    # そのため、current_pathsを変更する前にコピーしておく
    current_paths = current_paths.copy()

    # ターゲットノードを取得する
    target = get_element_by_id(elements, from_id)
    if target is None:
        raise ValueError(f"target_id={from_id} is not found.")

    # current_pathsに自分を保存
    current_paths.append(from_id)

    # アップリンクのノードを取得する
    pointer_nodes = target.get('data').get('_dijkstra').get('pointer_nodes', [])

    if len(pointer_nodes) == 0:
        # アップリンクがない場合は、current_pathsを逆順にしてall_pathsに追加して終了
        all_paths.append(current_paths[::-1])
        return

    # 複数のアップリンクがある場合は、それぞれに対して再帰処理を行う
    # from_idをアップリンクのノードに変更して再帰呼び出し
    for i, pointer_node_id in enumerate(pointer_nodes):
        logger.info(f"{i} pointer_node_id={pointer_node_id} current_paths={current_paths}")
        get_dijkstra_paths(all_paths, current_paths, elements, pointer_node_id)


if __name__ == '__main__':

    import json

    # ログレベル設定
    # logger.setLevel(logging.INFO)

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


    def test_dijkstra(is_directed=False):

        # 隣接行列が与えられてるなら、それをconvert_adj_matrix_to_elements()でエレメントに変換する

        # ここではdataディレクトリにあるJSONファイルを読み取ってエレメントを取得する

        for data_file_name in [p.name for p in data_dir.iterdir() if p.is_file() and p.suffix == '.json']:

            print(f"--- {data_file_name} ---")

            data_file_path = data_dir.joinpath(data_file_name)

            # オブジェクトの配列に変換
            elements = get_elements_from_file(data_file_path)

            # 始点ノードのid
            source_id = 's'

            # 終点ノードのid
            target_id = 't'

            # ダイクストラ法で最短経路を計算する
            calc_dijkstra(elements, source_id, is_directed=is_directed)

            # target_idから遡るパスをすべて取得する
            all_paths = []
            get_dijkstra_paths(all_paths, [], elements, target_id)

            print(all_paths)
            print('')

        return 0


    def main():
        test_dijkstra(is_directed=False)
        return 0

    # 実行
    sys.exit(main())
