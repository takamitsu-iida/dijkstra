#!/usr/bin/env python

# グラフのデータ構造はcytoscape.jsと同様の形式を想定しています。
# ダイクストラ法で用いたテストグラフと異なり、同一ノード間に複数のエッジはないものとします（事前に排除する必要があります）。

# このスクリプトでは、Ford-Fulkerson法を用いて最大フローを求めます。
# Ford-Fulkerson法は、教科書（グラフ理論入門）に詳しく記載されています。

# 最大フローを求めるアルゴリズムには、Ford-Fulkerson法のほかに、Dinic法というアルゴリズムがあるようです。
# Dinic法はFord-Fulkerson法の改良版で、最悪計算量がO(V^2 * E)となるFord-Fulkerson法に対して、O(V^2 * E)となることが知られています。

# 最大フローはマッチング問題にも応用できます。

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

# 各ノードに付与するデータのキー
DATA_KEY = '_max_flow'

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
# max_flow 最大フロー
# Ford-Fulkerson法で最大流を求める
# 同一ノード間に複数のエッジはないものとする（事前に結合しておく）
#
def calc_max_flow(elements: list, source_id: str, target_id: str) -> list:

    # 残余ネットワークを作成する
    residual_network = create_residual_network(elements)

    # 試行回数
    iter = 0

    # 最大試行回数
    max_iter = 200

    # 残余ネットワーク上でsource_idからtarget_idまでのパスを探す
    augmenting_paths = search_augmenting_flow(residual_network, source_id, target_id)

    logger.info(f"iteration={iter}, augmenting_paths={augmenting_paths}")

    while len(augmenting_paths) > 0:

        iter += 1
        if iter > max_iter:
            raise ValueError(f"max_iter={max_iter} is exceeded.")

        # パス上のフローを更新する
        update_augmenting_network(residual_network, augmenting_paths)

        # 残余ネットワーク上でsource_idからtarget_idまでのパスを探す
        augmenting_paths = search_augmenting_flow(residual_network, source_id, target_id)

        logger.info(f"iteration={iter}, augmenting_paths={augmenting_paths}")

    return residual_network


def show_flow(elements: list, source_id: str):
    # 各エッジを流れるフローを表示
    print("\n--- flow on each edge---")
    for edge in get_edges(elements):
        if edge.get('data').get('is_residual') == True:
            continue
        print(f"[{edge.get('data').get('source')}, {edge.get('data').get('target')}] flow / weight = {edge.get('data').get('flow')} / {edge.get('data').get('weight')}")

    flow = 0
    for edge in get_edges(elements):
        if edge.get('data').get('source') == source_id:
            flow += edge.get('data').get('flow')

    print(f"\n--- total flow from {source_id} ---")
    print(f"{flow}")



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
    残余ネットワーク上でsource_idからtarget_idまでのパスを探す
    到達できるパスがあるかどうか、が重要なのであって、最短パスである必要はない
    ここではDFS 深さ優先探索を用いる
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

    # すべてのノードに'_max_flow'という名前の辞書を追加しておく(DATA_KEYは'_max_flow'を指す)
    # 後ほどpointer_nodeを記録し、経路をたどれるようにする
    for node in get_nodes(residual):
        node.get('data')[DATA_KEY] = {}

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
            target_node.get('data').get(DATA_KEY)['pointer_node'] = current_id
            visited.add(target_id)
            break

        # current_idに隣接するノードに関して、
        for neighbor_node_id in neighbor_node_ids:
            # 発見済みのノードであれば（すでにtodo_listに入っているはずなので）ここでは何もしない
            if neighbor_node_id in visited:
                continue

            # どこから到達するのか、pointer_nodeとして記録する
            neighbor_node = get_element_by_id(residual, neighbor_node_id)
            neighbor_node.get('data').get(DATA_KEY)['pointer_node'] = current_id

            # 見つけた隣接ノードを
            # 発見済みにした上で、探索対象として追加
            visited.add(neighbor_node_id)
            todo_list.append(neighbor_node_id)

    # target_idに到達していない場合は空のパスを返す
    if target_id not in visited:
        return []

    # 到達できた場合は、source_idからtarget_idまでのパスを取得して返却する
    paths = []

    # target_idから開始して、
    current_node_id = target_id
    current_node = get_element_by_id(residual, current_node_id)
    # source_idに到達するまで、pointer_nodeをたどっていく
    while current_node_id != source_id:
        pointer_node_id = current_node.get('data').get(DATA_KEY).get('pointer_node')
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
    augmenting_pathsは [[from, to], [from, to]...] の形式で格納されている
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

    # 求まった最小値をパス上のエッジに適用してフローを増減させ、残余ネットワークを更新する
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
    import json

    # ログレベル設定
    logger.setLevel(logging.INFO)

    def matching_test_1():

        # 以下の表は、10人の男女が、
        #   - お互いにカップルになってもよい、と思っている場合はo
        #   - そうでない場合はx
        # を表しています。最大で何組のカップルができるでしょうか、
        # という問題を解いてみます。

        matching_text = """
            o   x   x   o   x   x   x   x   o   x
            x   x   x   o   x   x   o   x   x   x
            x   o   x   x   x   o   x   x   x   o
            x   x   x   o   x   x   x   x   x   x
            x   x   o   x   x   o   x   x   x   o
            o   x   x   x   o   x   x   o   x   x
            x   x   x   o   x   x   o   x   x   x
            o   x   o   x   x   x   x   x   o   x
            x   o   x   x   o   x   x   x   x   x
            x   x   x   o   x   x   x   x   x   x
        """

        # グラフの要素を格納するリスト
        elements = []

        # 始点ノード's'を追加
        elements.append({'group': 'nodes', 'data': { 'id': 's' } })

        # 終点ノード't'を追加
        elements.append({'group': 'nodes', 'data': { 'id': 't' } })

        # 行は男を、列は女を表すものとして、
        row_index = 0
        for row in matching_text.split('\n'):
            if len(row.strip()) == 0:
                # 空行はスキップ
                continue

            # 男ノードを追加
            male_node_id = f"male_{row_index}"
            elements.append({'group': 'nodes', 'data': { 'id': male_node_id } })

            # 's'から男ノードへのエッジを追加
            elements.append({'group': 'edges', 'data': { 'id': f"s-{male_node_id}", 'source': 's', 'target': male_node_id, 'weight': 1 } })

            # 行番号をインクリメント
            row_index += 1

            # 行を空白で分割して、各列を処理
            for column_index, column in enumerate(row.split()):
                if column == 'o':
                    # まだ女ノードを作っていなければ追加
                    female_node_id = f"female_{column_index}"
                    if next((ele for ele in elements if ele.get('data').get('id') == f"female_{column_index}"), None) is None:
                        elements.append({'group': 'nodes', 'data': { 'id': female_node_id } })

                        # 女ノードから't'へのエッジを追加
                        elements.append({'group': 'edges', 'data': { 'id': f"{female_node_id}-t", 'source': female_node_id, 'target': 't', 'weight': 1 } })

                    # エッジを追加
                    edge_id = f"{male_node_id}-{female_node_id}"
                    elements.append({'group': 'edges', 'data': { 'id': edge_id, 'source': male_node_id, 'target': female_node_id, 'weight': 1 } })

        # 最大フローを求める
        source_id = 's'
        target_id = 't'
        residual_network = calc_max_flow(elements, source_id, target_id)

        # エッジの重みは1なので、エッジのフローが1のものがカップル、0はカップル不成立、ということになる
        couples = []
        max_flow = 0
        for edge in get_edges(residual_network):
            if edge.get('data').get('is_residual') == True:
                continue
            if edge.get('data').get('source') == source_id:
                continue
            if edge.get('data').get('target') == target_id:
                continue

            if edge.get('data').get('flow') != 1:
                continue
            max_flow += 1

            male_node_index = int(edge.get('data').get('source').replace('male_', ''))
            female_node_index = int(edge.get('data').get('target').replace('female_', ''))
            couples.append((male_node_index, female_node_index))

            print(f"  (男{male_node_index}, 女{female_node_index}) がカップルになりました。")
        print(f"以上、全部で{max_flow}組のカップルができました。")

        # 行は男を、列は女を表す
        result_text = ""
        row_index = 0
        for row in matching_text.split('\n'):
            if len(row.strip()) == 0:
                continue
            for column_index, column in enumerate(row.split()):
                if column == 'o':
                    if (row_index, column_index) in couples:
                        result_text += " *"
                    else:
                        result_text += " o"
                else:
                    result_text += " x"
            result_text += "\n"
            row_index += 1

        print(result_text)

        """実行結果

        (男0, 女8) がカップルになりました。
        (男2, 女1) がカップルになりました。
        (男4, 女9) がカップルになりました。
        (男5, 女7) がカップルになりました。
        (男6, 女6) がカップルになりました。
        (男7, 女2) がカップルになりました。
        (男8, 女4) がカップルになりました。
        (男9, 女3) がカップルになりました。

        以上、全部で8組のカップルができました。

        x * x x x o x x x o
        x x x o x x x x x x
        x x o x x o x x x *
        o x x x o x x * x x
        x x x o x x * x x x
        o x * x x x x x o x
        x o x x * x x x x x
        x x x * x x x x x x

        """

    def test_max_flow():

        # 教科書の図6.1
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

        elements = fig_6_1_elements
        source_id = 's'
        target_id = 't'
        residual_network = calc_max_flow(elements, source_id, target_id)

        print("--- Fig6.1 residual network ---")
        print(json.dumps(residual_network, indent=2))
        print('')

        show_flow(residual_network, source_id)
        print('')

    def main():
        test_max_flow()
        # matching_test_1()
        return 0

    # 実行
    sys.exit(main())
