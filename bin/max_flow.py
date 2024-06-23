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
    深さ優先探索を行い、start_idからtarget_idまでの経路を返却する
    pathsは [from, to] の形式で格納される
    _dfsという名前の辞書をノードに追加してアップリンクノードを記録するので、別途、経路を遡ることもできる
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

    # すべてのノードに_dfsという名前の辞書を追加しておく
    for node in get_nodes(elements):
        node.get('data')['_dfs'] = {}

    # start_idに関して、
    # 発見済みにしてから、探索予定のリストに追加する
    visited.add(start_id)
    todo_list.append(start_id)

    #
    # 探索開始
    #

    while len(todo_list) > 0:

        # pop(0)で先頭から取り出すとBFS 幅優先探索になる
        # pop(-1)で最後のノードを取り出すとDFS 深さ優先探索になる
        current_id = todo_list.pop(-1)

        if current_id == start_id:
            # スタートノードの場合、記録すべき経路はまだ存在しない
            pass
        else:
            # このcurrent_idの上位ノードを取り出して、[from, to]の形式でpathsに追加
            current_node = get_element_by_id(elements, current_id)
            pointer_node_id = current_node.get('data').get('_dfs').get('pointer_node')
            paths.append([pointer_node_id, current_id])

        # current_idの先にいる隣接ノードを取得する
        neighbor_node_ids = get_neighborhood_ids(elements, current_id, is_directed=is_directed)

        # ゴールになるノード target_id をその中に見つけたら探索途中でも処理を終了する
        if target_id in neighbor_node_ids:
            target_node.get('data').get('_dfs')['pointer_node'] = current_id

            visited.add(target_id)
            paths.append([current_id, target_id])
            break

        # current_idの隣接ノードに関して、
        for neighbor_node_id in neighbor_node_ids:
            # 発見済みのノードであれば（すでにtodo_listに入っているはずなので）ここでは何もしない
            if neighbor_node_id in visited:
                continue

            # どこからたどり着いたか、pointer_nodeとして記録する
            neighbor_node = get_element_by_id(elements, neighbor_node_id)
            neighbor_node.get('data').get('_dfs')['pointer_node'] = current_id

            # 発見済みにした上で、探索対象として追加
            visited.add(neighbor_node_id)
            todo_list.append(neighbor_node_id)

    logger.info(f"visited={visited}")
    logger.info(f"paths={paths}")

    return paths

#
# max_flow 最大フロー
# Ford-Fulkerson法で最大流を求める
# 同一ノード間に複数のエッジはないものとする（事前に結合しておく）
#
def max_flow(elements: list, source_id: str, target_id: str) -> int:

    # 残余ネットワークを作成する
    residual_network = create_residual_network(elements)

    # 試行回数
    iter = 0

    # 最大試行回数
    max_iter = 200

    # 残余ネットワーク上でsource_idからtarget_idまでのパスを探す
    augmenting_paths = search_augmenting_flow(residual_network, source_id, target_id)

    print(f"iteration={iter}, augmenting_paths={augmenting_paths}")

    while len(augmenting_paths) > 0:

        iter += 1
        if iter > max_iter:
            raise ValueError(f"max_iter={max_iter} is exceeded.")

        # パス上のフローを更新する
        update_augmenting_network(residual_network, augmenting_paths)

        # 残余ネットワーク上でsource_idからtarget_idまでのパスを探す
        augmenting_paths = search_augmenting_flow(residual_network, source_id, target_id)

        print(f"iteration={iter}, augmenting_paths={augmenting_paths}")

    print("\n--- flow ---")

    for edge in get_edges(residual_network):
        if edge.get('data').get('is_residual') == True:
            continue
        print(f"[{edge.get('data').get('source')}, {edge.get('data').get('target')}], flow={edge.get('data').get('flow')} / {edge.get('data').get('weight')}")

    flow = 0
    for edge in get_edges(residual_network):
        if edge.get('data').get('source') == source_id:
            flow += edge.get('data').get('flow')

    return flow






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

    # target_idのエレメントを取得しておく
    target_node = get_element_by_id(residual, target_id)

    # これから探索していく予定のノードのidを格納するリスト
    todo_list = []

    # 探索の過程で発見したノードの一覧
    visited = set()

    #
    # 初期化
    #

    # すべてのノードに_dfsという名前の辞書を追加しておく
    # 後ほど、pointer_nodeを記録し、経路を遡れるようにする
    for node in get_nodes(residual):
        node.get('data')['_dfs'] = {}

    # source_idに関して、
    # 発見済みにしてから、探索予定のリストに追加する
    visited.add(source_id)
    todo_list.append(source_id)

    #
    # 探索開始
    #

    while len(todo_list) > 0:

        # DFSの場合は pop(-1) で最後のノードを取り出す
        current_id = todo_list.pop(-1)

        # current_idの先にいる隣接ノードを取得する
        # ただし、current_weight が 0 になったエッジは通れないものとして扱う
        neighbor_node_ids = []
        for edge in get_edges(residual):
            if edge.get('data').get('current_weight') > 0 and edge.get('data').get('source') == current_id:
                neighbor_node_ids.append(edge.get('data').get('target'))

        # ゴールになるノード target_id をその中に見つけたら探索途中でも処理を終了する
        if target_id in neighbor_node_ids:
            target_node.get('data').get('_dfs')['pointer_node'] = current_id
            visited.add(target_id)
            break

        # current_idに隣接するノードに関して、
        for neighbor_node_id in neighbor_node_ids:
            # 発見済みのノードであれば（すでにtodo_listに入っているはずなので）ここでは何もしない
            if neighbor_node_id in visited:
                continue

            # どこからたどり着いたか、pointer_nodeとして記録する
            neighbor_node = get_element_by_id(residual, neighbor_node_id)
            neighbor_node.get('data').get('_dfs')['pointer_node'] = current_id

            # 見つけた隣接ノードを発見済みにした上で、探索対象として追加
            visited.add(neighbor_node_id)
            todo_list.append(neighbor_node_id)

    # ゴールノードに到達していない場合は空のパスを返す
    if target_id not in visited:
        return []

    # ゴールノードに到達した場合、ゴールノードからスタートノードまでのパスを取得する
    paths = []

    # ゴールノードから開始して、
    current_node_id = target_id
    current_node = get_element_by_id(residual, current_node_id)
    # スタートノードに到達するまで、pointer_nodeをたどっていく
    while current_node_id != source_id:
        pointer_node_id = current_node.get('data').get('_dfs').get('pointer_node')
        pointer_node = get_element_by_id(residual, pointer_node_id)
        # どこから、どこに向かうか、[from, to]の形式で記録する
        paths.append([pointer_node_id, current_node_id])
        # 次のノードに移動する
        current_node_id = pointer_node_id
        current_node = pointer_node

    # 順番を逆にして返却する
    paths.reverse()

    return paths


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


if __name__ == '__main__':

    # ログレベル設定
    # logger.setLevel(logging.INFO)

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

    def test_max_flow():
        print("--- Fig6.1 ---")
        elements = fig_6_1_elements
        print(json.dumps(elements, indent=2))
        print('')

        source_id = 's'
        target_id = 't'
        flow = max_flow(elements, source_id, target_id)
        print(f"--- max flow from {source_id} to {target_id} ---")
        print(f"{flow}")


    def main():
        #test_dfs()
        test_max_flow()

        return 0

    # 実行
    sys.exit(main())
