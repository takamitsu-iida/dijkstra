#!/usr/bin/env python

# グラフのデータ構造はcytoscape.jsと同様の形式を想定しています。
# テストで用いているグラフはdataフォルダにjson形式で格納してあります。

# Bellman-Fordアルゴリズムは、ダイクストラ法と同様に単一始点最短経路を求めるアルゴリズムです。
# 辺の重みが負の場合でも解くことができます。

# ルーティングプロトコルのRIPはBellman-Fordの応用です。

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

#
# Bellman-Fordアルゴリズム
#
# ディスタンスベクター型のルーティングアルゴリズムに使われている。
# メリット
#   - 実装が容易
#   - 有向グラフ、無向グラフの両方に適用可能
#   - 負の重みを持つエッジがあっても適用可能
#   - ネットワークのループがあっても適用可能
#   - (ノード数 -1) 以内の繰り返しで最短経路を求めることができる
# デメリット
#   - ノード数が多いと収束に時間がかかる。
#

def calc_bellman_ford(elements: list, source_id: str, is_directed=False):

    # ノードのdataに_bellman_fordという名前の辞書を追加し、そこに計算結果を保存する
    # distance: 始点からそのノードまでの距離
    # pointer_nodes: そのノードに至る最短経路の上位ノードのidのリスト（等コストの場合は複数）
    # pointer_edges: そのノードに至る最短経路のエッジのidのリスト（等コストの場合は複数）

    # 指定されたsource_idのオブジェクトを取り出しておく
    source_node = get_element_by_id(elements, source_id)
    if source_node is None:
        raise ValueError(f"source_id={source_id} is not found.")

    #
    # STEP1
    #

    # δ(v)はノードvの v['data']['_bellman_ford']['distance'] を指すことにする
    # sourceノードの距離、すなわちδ(source)は0とし、
    # その他のノードは無限大に初期化する

    for node in get_nodes(elements):

        # このアルゴリズムの途中経過で用いるデータの保存先を初期化する
        _bellman_ford = {}
        node.get('data')['_bellman_ford'] = _bellman_ford

        # sourceからノードに至る距離distanceを初期化する
        if node.get('data')['id'] == source_id:
            # sourceノードの距離は0
            _bellman_ford['distance'] = 0
        else:
            # それ以外は無限大
            _bellman_ford['distance'] = sys.maxsize

    #
    # STEP2
    #

    # たかだか|V| - 1 回の繰り返しで最短経路を求めることができる

    logger.info("start Bellman-Ford algorithm.")
    logger.info(f"node count={len(get_nodes(elements))}, edge count={len(get_edges(elements))}")
    logger.info(f"iteration will occur {len(get_nodes(elements)) - 1} times.")

    for i in range(len(get_nodes(elements)) - 1):

        # 更新があったかどうかを示すフラグ、更新がなければ早期に終了する
        updated = False

        # すべてのエッジについて、
        for edge in get_edges(elements):

            # このエッジのid
            edge_id = edge.get('data').get('id')

            # 両端のノードのidを取得する
            source_node_id = edge.get('data').get('source')
            target_node_id = edge.get('data').get('target')

            # このエッジのsourceとtargetのノードを取得する
            source_node = get_element_by_id(elements, source_node_id)
            target_node = get_element_by_id(elements, target_node_id)

            # このエッジの重みを取得する
            edge_weight = edge.get('data').get('weight')

            # 各ノードのdistanceを取り出す
            source_distance = source_node.get('data').get('_bellman_ford').get('distance')
            target_distance = target_node.get('data').get('_bellman_ford').get('distance')

            # targetノードに関して、
            # source --> このエッジ --> target という経路の方が距離が短くなるなら更新する
            if source_distance + edge_weight < target_distance:
                # distanceを小さい値に更新して、
                target_node.get('data').get('_bellman_ford')['distance'] = source_distance + edge_weight
                # 上位ノードを指すポインタとして source_node_id を指す
                target_node.get('data').get('_bellman_ford')['pointer_nodes'] = [source_node_id]
                target_node.get('data').get('_bellman_ford')['pointer_edges'] = [edge_id]
                updated = True
            elif source_distance + edge_weight == target_distance:
                # 同じ距離の場合は、ポインタに追加する
                if source_node_id not in target_node.get('data').get('_bellman_ford').get('pointer_nodes'):
                    target_node.get('data').get('_bellman_ford')['pointer_nodes'].append(source_node_id)
                if edge_id not in target_node.get('data').get('_bellman_ford').get('pointer_edges'):
                    target_node.get('data').get('_bellman_ford')['pointer_edges'].append(edge_id)
                updated = True

            # 有向グラフの場合は処理はここまで
            # 無向グラフの場合は逆方向、すなわち target --> このエッジ --> source という経路も考慮する
            if is_directed == False:
                if target_distance + edge_weight < source_distance:
                    # distanceを小さい値に更新して、
                    source_node.get('data').get('_bellman_ford')['distance'] = target_distance + edge_weight
                    # ポインタとして上位ノード target を指す
                    source_node.get('data').get('_bellman_ford')['pointer_nodes'] = [target_node_id]
                    source_node.get('data').get('_bellman_ford')['pointer_edges'] = [edge_id]
                    updated = True
                elif target_distance + edge_weight == source_distance:
                    # 同じ距離の場合は、ポインタに追加する
                    if target_node_id not in source_node.get('data').get('_bellman_ford').get('pointer_nodes'):
                        source_node.get('data').get('_bellman_ford')['pointer_nodes'].append(target_node_id)
                    if edge_id not in source_node.get('data').get('_bellman_ford').get('pointer_edges'):
                        source_node.get('data').get('_bellman_ford')['pointer_edges'].append(edge_id)
                    updated = True

        if updated:
            logger.info(f"iteration {i + 1} completed with updated.")
        else:
            # 何も更新がなければ早期に終了
            logger.info(f"converged at {i + 1} iteration.")
            break


def get_bellman_ford_paths(all_paths: list, current_paths: list, elements: list, from_id: str):
    """
    from_idからアップリンク方向に遡る最短経路をすべて取得する
    """

    # all_paths: 最短経路のリストを格納するリスト
    # current_paths: 現在の経路を格納するリスト
    # elements: グラフデータ
    # from_id: 終点のノードid

    # ノードエレメントには、_bellman_fordという名前の辞書が追加されている
    # distance: 始点からそのノードまでの距離
    # pointer_nodes: そのノードに至る最短経路の上位ノードのidのリスト（等コストの場合は複数）
    # pointer_edges: そのノードに至る最短経路のエッジのidのリスト（等コストの場合は複数）
    # これらの情報を使って最短経路を取得する

    # 再帰処理による変更影響を避けるためにコピーしておく
    current_paths = current_paths.copy()

    # ターゲットノードを取得する
    target = get_element_by_id(elements, from_id)
    if target is None:
        raise ValueError(f"target_id={from_id} is not found.")

    # current_pathsに自分を保存
    current_paths.append(from_id)

    # アップリンクのノードを取得する
    pointer_nodes = target.get('data').get('_bellman_ford').get('pointer_nodes', [])

    if len(pointer_nodes) == 0:
        # アップリンクがない場合は、current_pathsを逆順にしてall_pathsに追加して終了
        all_paths.append(current_paths[::-1])
        return

    # 複数のアップリンクがある場合は、それぞれに対して再帰処理を行う
    # from_idをアップリンクのノードに変更して再帰呼び出し
    for pointer_node_id in pointer_nodes:
        get_bellman_ford_paths(all_paths, current_paths, elements, pointer_node_id)


if __name__ == '__main__':

    import json

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


    def test_bellman_ford(is_directed=False):

        # ここではdataディレクトリにあるJSONファイルを読み取ってエレメントを取得する

        for data_file_name in [p.name for p in data_dir.iterdir() if p.is_file() and p.suffix == '.json']:

            print(f"--- {data_file_name} ---")

            data_file_path = data_dir.joinpath(data_file_name)

            # オブジェクトの配列に変換
            elements = get_elements_from_file(data_file_path)

            # 始点ノードのid
            source_id = 's'

            # 最短経路を計算する
            calc_bellman_ford(elements, source_id, is_directed=is_directed)

            # 終点ノードのid
            target_id = 't'

            # target_idから遡るパスをすべて取得する
            all_paths = []
            get_bellman_ford_paths(all_paths, [], elements, target_id)

            print(all_paths)
            print('')

        return 0


    def main():

        # ログレベル設定
        # logger.setLevel(logging.INFO)

        test_bellman_ford(is_directed=False)
        return 0

    # 実行
    sys.exit(main())
