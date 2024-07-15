#!/usr/bin/env python

# グラフのデータ構造はcytoscape.jsと同様の形式を想定しています。
# テストで用いているグラフはdataフォルダにjson形式で格納してあります。

# プリム法(Prim's algorithm)は、クラスカル法と同様、グラフの最小全域木を求めるアルゴリズムです。

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

# 計算に用いるデータを保存する辞書のキー
DATA_KEY = '_prim'


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


def get_connected_edges(elements: list, node_id: str, is_directed: bool=False) -> list:
    """
    指定されたノードに接続しているエッジを取得する
    """
    connected_edges = []
    for edge in get_edges(elements):
        if edge.get('data').get('source') == node_id:
            connected_edges.append(edge)
        if is_directed == False and edge.get('data').get('target') == node_id:
            connected_edges.append(edge)
    return connected_edges


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


def exists_unvisited_node(elements: list) -> bool:
    """
    未訪問のノードが存在するかどうかを返却する
    """
    for node in get_nodes(elements):
        if node.get('data').get(DATA_KEY).get('visited') == False:
            return True
    return False


def get_unvisited_edges(elements: list, is_directed=False) -> list:
    """
    集合Lに隣接する未訪問のエッジを取得する
    """
    unvisited_edges = []

    # 集合Lに含まれるノード（すなわち、訪問済みのノード）を取得する
    visited_nodes = [node for node in get_nodes(elements) if node.get('data').get(DATA_KEY).get('visited') == True]
    for node in visited_nodes:
        # そのノードに接続しているエッジを取得する
        edges = get_connected_edges(elements, node.get('data').get('id'), is_directed=is_directed)
        for edge in edges:
            # そのエッジの両端のノードがそれぞれ訪問済みかどうかを確認する
            source_id = edge.get('data').get('source')
            source = get_element_by_id(elements, source_id)
            target_id = edge.get('data').get('target')
            target = get_element_by_id(elements, target_id)
            if source.get('data').get(DATA_KEY).get('visited') == True and target.get('data').get(DATA_KEY).get('visited') == False:
                # sourceが訪問済みで、targetが未訪問の場合は、そのエッジを未訪問エッジとして追加する
                unvisited_edges.append(edge)
            elif is_directed == False and target.get('data').get(DATA_KEY).get('visited') == True and source.get('data').get(DATA_KEY).get('visited') == False:
                # 無向グラフの場合は逆の場合、すなわちsourceが未訪問で、targetが訪問済みの場合も同様に追加する
                unvisited_edges.append(edge)
    return unvisited_edges


#
# プリム法
#

def calc_prim(elements: list, source_id: str, is_directed=False):

    # ノードおよびエッジのdataに_primという名前の辞書を追加し、そこに計算結果を保存する
    # この辞書には以下のキーが含まれる
    #   - distance: 始点からの距離
    #   - visited: 訪問済みかどうか（確定済みの集合Lに含まれるかどうか）
    #   - pointer_nodes: このノードに至る最短経路の直前のノードのidのリスト（等コストの場合は複数）
    #   - pointer_edges: このノードに至る最短経路のエッジのidのリスト（等コストの場合は複数）
    #
    # この関数ではsource_idを頂点とした最小全域木の計算を行う

    # 指定されたsource_idのオブジェクトを取り出しておく
    source = get_element_by_id(elements, source_id)
    if source is None:
        raise ValueError(f"source_id={source_id} is not found.")

    #
    # STEP1. 初期化
    #
    for node in get_nodes(elements):
        # このアルゴリズムの途中経過で用いるデータの保存先を初期化する
        node.get('data')[DATA_KEY] = {}

        # sourceから各ノードに至る距離distanceを初期化する
        if node.get('data')['id'] == source_id:
            node.get('data').get(DATA_KEY)['distance'] = 0
        else:
            node.get('data').get(DATA_KEY)['distance'] = sys.maxsize

        # 探索済みのノードの集合 L は、visitedフラグで管理する
        # 全ノードを未探索の状態に初期化する
        node.get('data').get(DATA_KEY)['visited'] = False

    for edge in get_edges(elements):
        # このアルゴリズムの途中経過で用いるデータの保存先を初期化する
        edge.get('data')[DATA_KEY] = {}

        # 各エッジの重みを初期化する
        edge.get('data').get(DATA_KEY)['visited'] = False

    #
    # STEP2. 頂点sourceを集合 L に入れる
    #

    # 頂点sourceを集合 L に入れる、すなわちsourceのvisitedフラグを立てる
    source.get('data').get(DATA_KEY)['visited'] = True

    #
    # STEP3. 全てのノードが集合 L に入るまで、以下を繰り返す
    #

    while exists_unvisited_node(elements):

        #
        # STEP4. 集合 L に隣接する未訪問のノードを取得する
        #

        unvisited_edges = get_unvisited_edges(elements, is_directed=is_directed)
        logger.info(f"unvisited edges: {[edge.get('data').get('id') for edge in unvisited_edges]}")

        if not unvisited_edges:
            logger.info(f"finished by no unvisited edges")
            break

        # その中から最小の重みを持つエッジだけを取得（等コストの場合に複数）
        min_weight_edges = get_minimum_weight_edges(unvisited_edges)

        # その中から最小の重みを持つエッジを選択する
        min_weight_edge = min_weight_edges[0]

        # そのエッジを集合 L に入れる、すなわちvisitedフラグを立てる
        min_weight_edge.get('data').get(DATA_KEY)['visited'] = True
        logger.info(f"edge {min_weight_edge.get('data').get('id')} visited")

        # エッジの両端のノードのうち、一方はまだ集合 L に入ってないので集合 L に加える（すなわちvisitedフラグを立てる）
        target_id = min_weight_edge.get('data').get('target')
        target = get_element_by_id(elements, target_id)
        source_id = min_weight_edge.get('data').get('source')
        source = get_element_by_id(elements, source_id)

        if target.get('data').get(DATA_KEY).get('visited') == False:
            target.get('data').get(DATA_KEY)['visited'] = True
            logger.info(f"target {target_id} visited")

            # targetに至る最短経路の直前のノードをsource_idに設定する
            target.get('data').get(DATA_KEY)['pointer_nodes'] = [source_id]

            # targetに至る最短経路のエッジをmin_weight_edgeのidに設定する
            target.get('data').get(DATA_KEY)['pointer_edges'] = [min_weight_edge.get('data').get('id')]

            # sourceに至る最短経路の距離に、targetまでのエッジの距離を加算する
            target.get('data').get(DATA_KEY)['distance'] = source.get('data').get(DATA_KEY).get('distance') + min_weight_edge.get('data').get('weight')

        # 無向グラフの場合はsourceも考慮する
        if is_directed == False:
            if source.get('data').get(DATA_KEY).get('visited') == False:
                source.get('data').get(DATA_KEY)['visited'] = True
                logger.info(f"source {source_id} visited")

                source.get('data').get(DATA_KEY)['pointer_nodes'] = [target_id]
                source.get('data').get(DATA_KEY)['pointer_edges'] = [min_weight_edge.get('data').get('id')]
                source.get('data').get(DATA_KEY)['distance'] = target.get('data').get(DATA_KEY).get('distance') + min_weight_edge.get('data').get('weight')


def get_mst_paths(all_paths: list, current_paths: list, elements: list, from_id: str):
    """
    from_idからアップリンク方向に遡る最短経路をすべて取得する
    """

    # all_paths: 最短経路のリストを格納するリスト
    # current_paths: 現在の経路を格納するリスト
    # elements: グラフデータ
    # from_id: 終点のノードid

    # ノードエレメントには、_primという名前の辞書が追加されている
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
    pointer_nodes = target.get('data').get(DATA_KEY).get('pointer_nodes', [])

    if len(pointer_nodes) == 0:
        # アップリンクがない場合は、current_pathsを逆順にしてall_pathsに追加して終了
        all_paths.append(current_paths[::-1])
        return

    # 複数のアップリンクがある場合は、それぞれに対して再帰処理を行う
    # from_idをアップリンクのノードに変更して再帰呼び出し
    for i, pointer_node_id in enumerate(pointer_nodes):
        logger.info(f"{i} pointer_node_id={pointer_node_id} current_paths={current_paths}")
        get_mst_paths(all_paths, current_paths, elements, pointer_node_id)



if __name__ == '__main__':

    # ログレベル設定
    logger.setLevel(logging.INFO)

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

    def test_prim(is_directed:bool=False):
        print("--- Fig6.1 ---")
        elements = fig_6_1_elements
        #print(json.dumps(elements, indent=2))
        #print('')

        calc_prim(elements, 's', is_directed=is_directed)

        # 結果を表示
        print(f"number of nodes: {len(get_nodes(elements))}")

        mst_edges = [edge.get('data').get('id') for edge in get_edges(elements) if edge.get('data').get(DATA_KEY).get('visited') == True]
        print(f"number of MST edges: {len(mst_edges)}")
        print(f"MST edges: {mst_edges}")
        unvisited_edges = [edge.get('data').get('id') for edge in get_edges(elements) if edge.get('data').get(DATA_KEY).get('visited') == False]
        print(f"other edges: {unvisited_edges}")

        # tからsにたどり着く経路を取得する
        from_id = 't'
        all_paths = []
        get_mst_paths(all_paths, [], elements, from_id)
        print(all_paths)

    def main():
        test_prim(is_directed=False)
        return 0

    # 実行
    sys.exit(main())
