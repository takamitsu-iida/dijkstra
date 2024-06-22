#!/usr/bin/env python

# グラフのデータ構造はcytoscape.jsと同様の形式であることを前提とする
# dataフォルダに格納しているjsonデータを参照

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

    # 再帰処理による変更影響を避けるためにコピーしておく
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

    # from_idをアップリンクのノードに変更して再帰呼び出し
    for i, pointer_node_id in enumerate(pointer_nodes):
        logger.info(f"{i} pointer_node_id={pointer_node_id} current_paths={current_paths}")
        get_dijkstra_paths(all_paths, current_paths, elements, pointer_node_id)


#
# DFS 深さ優先探索
#

def dfs(elements: list, start_id: str, target_id='', is_directed=False) -> list:
    """
    深さ優先探索を行い、start_idからtarget_idまでの経路を取得する
    target_idが指定されなければ、start_idから到達可能なすべてのノードを取得する
    """
    paths = []

    todo_list = []
    seen = set()

    # 開始ノードを発見済みに初期化
    seen.add(start_id)

    # start_idに隣接しているノードを取得する
    neighbor_node_ids = get_neighborhood_ids(elements, start_id, is_directed=is_directed)

    # 見つけた隣接ノードを発見済みにした上で、探索対象として追加する
    for neighbor_id in neighbor_node_ids:
        seen.add(neighbor_id)
        todo_list.append([start_id, neighbor_id])

    # 探索対象がなくなるまで続ける
    while len(todo_list) > 0:

        # 探索対象に追加された最後のオブジェクトを取り出す
        todo = todo_list.pop(-1)

        # パスに追加
        paths.append(todo)

        # from_id = todo[0]
        to_id = todo[1]

        # 隣接ノードを取得して、順に探索する
        neighbor_node_ids = get_neighborhood_ids(elements, to_id, is_directed=is_directed)

        # ゴールノードが見つかったら、探索を終了
        if target_id in neighbor_node_ids:
            seen.add(target_id)
            paths.append([to_id, target_id])
            break

        for neighbor_id in neighbor_node_ids:
            if neighbor_id in seen:
                continue

            # 見つけた隣接ノードを発見済みにした上で、探索対象として追加
            seen.add(neighbor_id)
            todo_list.append([to_id, neighbor_id])

    return paths


#
# bfs 幅優先探索
#

def bfs(elements: list, start_id: str, target_id='', is_directed=False) -> list:
    """
    幅優先探索を行い、start_idからtarget_idまでの経路を取得する
    target_idが指定されなければ、start_idから到達可能なすべてのノードを取得する
    """
    paths = []

    todo_list = []
    seen = set()

    # 開始ノードを発見済みに初期化
    seen.add(start_id)

    # start_idに隣接しているノードを取得する
    neighbor_node_ids = get_neighborhood_ids(elements, start_id, is_directed=is_directed)

    # 見つけた隣接ノードを発見済みにした上で、探索対象として追加する
    for neighbor_id in neighbor_node_ids:
        seen.add(neighbor_id)
        todo_list.append([start_id, neighbor_id])

    # 探索対象がなくなるまで続ける
    while len(todo_list) > 0:

        # 探索対象に追加された最初のオブジェクトを取り出す
        todo = todo_list.pop(0)

        # パスに追加
        paths.append(todo)

        # from_id = todo[0]
        to_id = todo[1]

        # 隣接ノードを取得して、順に探索する
        neighbor_node_ids = get_neighborhood_ids(elements, to_id, is_directed=is_directed)

        # ゴールノードが見つかったら、探索を終了
        if target_id in neighbor_node_ids:
            seen.add(target_id)
            paths.append([to_id, target_id])
            break

        for neighbor_id in neighbor_node_ids:
            if neighbor_id in seen:
                continue

            # 見つけた隣接ノードを発見済みにした上で、探索対象として追加
            seen.add(neighbor_id)
            todo_list.append([to_id, neighbor_id])

    return paths


#
# max_flow 最大フロー
# Ford-Fulkerson法で最大流を求める
# 同一ノード間に複数のエッジはないものとする（事前に結合しておく）
#
def max_flow(elements: list, source_id: str, target_id: str) -> int:
    # 残余ネットワークを作成する
    residual_network = create_residual_network(elements)

    # 残余ネットワーク上でsource_idからtarget_idまでのパスを探す
    augmenting_paths = search_augmenting_flow(residual_network, source_id, target_id)
    print(f"augmenting_paths={augmenting_paths}")

    counter = 0
    while len(augmenting_paths) > 0:

        print("")
        counter += 1
        print(f"counter={counter}")

        # パス上のフローを更新する
        update_augmenting_network(residual_network, augmenting_paths)

        # 残余ネットワーク上でsource_idからtarget_idまでのパスを探す
        augmenting_paths = search_augmenting_flow(residual_network, source_id, target_id)
        print(f"augmenting_paths={augmenting_paths}")

        if counter == 20:
            break

    for edge in get_edges(residual_network):
        if edge.get('data').get('is_residual') == True:
            continue
        print(f"source={edge.get('data').get('source')}, target={edge.get('data').get('target')}, flow={edge.get('data').get('flow')}")



def create_residual_network(elements: list, flow=0) -> list:
    residual = []
    node_ids = set()

    for edge in get_edges(elements):
        edge_id = edge.get('data').get('id')
        residual_edge_id = f"_residual_{edge_id}"

        source = edge.get('data').get('source')
        target = edge.get('data').get('target')
        weight = edge.get('data').get('weight')

        # 残余ネットワークにこのエッジを追加する
        residual.append({
            'group': 'edges',
            'data': {
                'id': edge_id,
                'source': source,
                'target': target,
                'weight': weight,
                'flow': flow,
                'current_weight': weight - flow,
                'pointing': residual_edge_id,
                'is_residual': False
            }
        })

        # これとは逆向きのエッジを追加する
        # idは__を先頭につけて重複を避ける
        residual.append({
            'group': 'edges',
            'data': {
                'id': residual_edge_id,
                'source': target,
                'target': source,
                'current_weight': flow,
                'pointing': edge_id,
                'is_residual': True
            }
        })

        node_ids.add(source)
        node_ids.add(target)

    # ノードを追加する
    for node_id in node_ids:
        residual.append({
            'group': 'nodes',
            'data': {
                'id': node_id
            }
        })

    return residual



def search_augmenting_flow(residual: list, source_id: str, target_id: str) -> list:
    """
    DFSを使って残余ネットワーク上でsource_idからtarget_idまでのパスを探す
    """
    paths = []

    todo_list = []
    seen = set()

    # source_idを発見済みに初期化
    seen.add(source_id)

    # source_idに隣接しているノードを取得する
    neighbor_node_ids = []
    for edge in get_edges(residual):
        if edge.get('data').get('current_weight') > 0 and edge.get('data').get('source') == source_id:
            neighbor_node_ids.append(edge.get('data').get('target'))

    # 見つけた隣接ノードを発見済みにした上で、探索対象として追加する
    for neighbor_id in neighbor_node_ids:
        seen.add(neighbor_id)
        todo_list.append([source_id, neighbor_id])

    # 探索対象がなくなるまで続ける
    while len(todo_list) > 0:

        # 探索対象に追加された最後のオブジェクトを取り出す
        todo = todo_list.pop()

        # from_id = todo[0]
        to_id = todo[1]

        # パスに追加
        paths.append(todo)

        # 隣接ノードを取得して、順に探索する
        neighbor_node_ids = []
        for edge in get_edges(residual):
            if edge.get('data').get('current_weight') > 0 and edge.get('data').get('source') == to_id:
                neighbor_node_ids.append(edge.get('data').get('target'))

        # 隣接ノードの中にゴールを見つけたら終了
        if target_id in neighbor_node_ids:
            seen.add(target_id)
            paths.append([to_id, target_id])
            break

        # 未訪問の隣接ノードは次に探索する候補
        for neighbor_id in neighbor_node_ids:
            if neighbor_id in seen:
                continue

            # 見つけた隣接ノードを発見済みにした上で、探索対象として追加
            seen.add(neighbor_id)
            todo_list.append([to_id, neighbor_id])

    # ゴールノードに到達していない場合は空のパスを返す
    if target_id not in seen:
        return []

    # パスを最適化するために、ツリーの余分なところをカットする
    last_path = paths[-1]
    optimized_paths = []
    optimized_paths.append(last_path)
    while True:
        found = False
        for p in reversed(paths):
            if p[1] == last_path[0]:
                optimized_paths.append(p)
                last_path = p
                found = True
                break
        if not found:
            raise ValueError(f"last_path={last_path} is not found in paths.")

        if last_path[0] == source_id:
            break

    optimized_paths.reverse()
    return optimized_paths


def update_augmenting_network(augmenting_network: list, augmenting_paths: list):
    """
    残余ネットワーク上で、augmenting_paths上のエッジのフローを更新する
    """
    # パス上のエッジのcurrent_weightの最小値（＝キャパシティ）を取得する
    min_weight = sys.maxsize
    for [from_id, to_id] in augmenting_paths:
        edge = None
        for e in get_edges(augmenting_network):
            if e.get('data').get('source') == from_id and e.get('data').get('target') == to_id:
                edge = e
                break

        if edge is None:
            raise ValueError(f"edge between {from_id} and {to_id} is not found.")

        if edge.get('data').get('current_weight') <= 0:
            raise ValueError(f"edge between {from_id} and {to_id} has no capacity.")

        if edge.get('data').get('current_weight') < min_weight:
            min_weight = edge.get('data').get('current_weight')

    print(f"min_weight={min_weight}")

    for [from_id, to_id] in augmenting_paths:
        edge = None
        for e in get_edges(augmenting_network):
            if e.get('data').get('source') == from_id and e.get('data').get('target') == to_id:
                edge = e
                break

        if edge.get('data').get('is_residual') == True:
            # このエッジが逆向きの場合、正向きエッジを流れるフローを減少させる
            pointing_id = edge.get('data').get('pointing')
            pointing_edge = get_element_by_id(augmenting_network, pointing_id)
            pointing_edge.get('data')['flow'] -= min_weight
            pointing_edge.get('data')['current_weight'] = pointing_edge.get('data')['weight'] - pointing_edge.get('data')['flow']

            edge.get('data')['current_weight'] = pointing_edge.get('data')['flow']

        else:
            # このエッジが正向きの場合、このエッジのフローを増大させる
            edge.get('data')['flow'] += min_weight
            edge.get('data')['current_weight'] = edge.get('data')['weight'] - edge.get('data')['flow']

            pointing_id = edge.get('data').get('pointing')
            pointing_edge = get_element_by_id(augmenting_network, pointing_id)
            pointing_edge.get('data')['current_weight'] = edge.get('data')['flow']


#
# 隣接行列からエレメントに変換
#

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


    def test_dfs():
        for data_file_name in [p.name for p in data_dir.iterdir() if p.is_file() and p.suffix == '.json']:
            print(f"--- {data_file_name} ---")

            data_file_path = data_dir.joinpath(data_file_name)
            elements = get_elements_from_file(data_file_path)
            source_id = 's'
            paths = dfs(elements, source_id)
            print(f"dfs from {source_id}")
            print(paths)
            target_id = 't'
            paths = dfs(elements, source_id, target_id)
            print(f"dfs from {source_id} to {target_id}")
            print(paths)
            print('')


    def test_bfs():
        for data_file_name in [p.name for p in data_dir.iterdir() if p.is_file() and p.suffix == '.json']:
            print(f"--- {data_file_name} ---")
            data_file_path = data_dir.joinpath(data_file_name)
            elements = get_elements_from_file(data_file_path)
            source_id = 's'
            paths = bfs(elements, source_id)
            print(f"bfs from {source_id}")
            print(paths)
            target_id = 't'
            paths = bfs(elements, source_id, target_id)
            print(f"bfs from {source_id} to {target_id}")
            print(paths)
            print('')


    def test_max_flow():
        # 図6.1
        elements = [
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

        print("--- Fig6.1 ---")
        source_id = 's'
        target_id = 't'
        max_flow(elements, source_id, target_id)


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
        # test_dijkstra(is_directed=False)
        # test_dfs()
        # test_bfs()

        test_max_flow()

        return 0

    # 実行
    sys.exit(main())
