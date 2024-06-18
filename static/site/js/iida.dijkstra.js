/* global iida */

// define function iida.dijkstra()

(function () {

  function get_minimum_weight_edges(edges) {
    let min_weight = Infinity
    let min_weight_edges = []
    edges.forEach(edge => {
      let weight = edge.data('weight')
      if (min_weight > weight) {
        min_weight = weight
        min_weight_edges = [edge]
      } else if (min_weight === weight) {
        min_weight_edges.push(edge)
      }
    });
    return min_weight_edges
  }

  // 未訪問のノードが存在するかどうかを返却する
  function exists_unvisited_node(nodes) {
    for (let node of nodes) {
      if (node.data('_dijkstra').visited === false) {
        return true
      }
    }
    return false;
  }

  // 指定されたエレメントのリストのうち、
  // 未訪問でかつ
  // 最小のdistanceを持つノードを取得する
  function get_minimum_distance_nodes_from_unvisited(nodes) {
    let min_distance = Infinity;
    let min_distance_nodes = []

    for (let node of nodes) {
      // 空間Lに格納済み、すなわち訪問済みのノードは無視する
      if (node.data('_dijkstra').visited) {
          continue;
      }

      // 始点からの距離を取り出す
      distance = node.data('_dijkstra').distance;

      // 最小値と同じ距離ならリストに追加
      if (distance === min_distance) {
          min_distance_nodes.push(node);
      } else if (distance < min_distance) {
          // より小さい距離が見つかればリストを初期化して追加
          min_distance = distance;
          min_distance_nodes = [node];
      }
    }

    return min_distance_nodes;
  }

  // 渡されたエッジのリストから最小の重みを持つエッジをすべて取得する
  function get_minimum_weight_edges(edges) {
    let min_weight = Infinity;
    let min_weight_edges = [];

    for (let edge of edges) {
      let weight = edge.data('weight') || 1;
      if (min_weight > weight) {
        min_weight = weight;
        min_weight_edges = [edge];
      } else if (min_weight === weight) {
        min_weight_edges.push(edge);
      }
    }
    return min_weight_edges;
  }

  iida.dijkstra = function (elements, source_id='s') {
    let nodes = elements.nodes();

    // 指定されたsource_idのオブジェクトを取り出しておく
    let source = elements.getElementById(source_id);
    if (!source) {
      throw new Error('source_id not found');
    }

    //
    // STEP1
    //

    // δ(v)はノードvの v['data']['_dijkstra']['distance'] を指すことにする

    // sourceの距離、すなわちδ(source)を0とし、その他ノードは無限大に初期化する
    nodes.forEach(node => {

      // このアルゴリズムの途中経過で用いるデータの保存先を初期化する
      let _dijkstra = {}
      node.data('_dijkstra', _dijkstra)

      // sourceから各ノードに至る距離distanceを初期化する
      if (node.id() === source_id) {
        _dijkstra['distance'] = 0
      } else {
        _dijkstra['distance'] = Infinity
      }

      // 探索済みのノードの集合 L は、visitedフラグで管理する
      // 全ノードを未探索の状態に初期化する
      _dijkstra['visited'] = false
    });

    //
    // STEP2
    //

    // 頂点sourceを集合 L に入れる、すなわちvisitedフラグを立てる
    let _dijkstra = source.data('_dijkstra')
    _dijkstra['visited'] = true

    // 次にsourceに隣接している各頂点 v について
    let source_neighbors = source.neighborhood().nodes();
    source_neighbors.forEach(v => {
      // 利便性のため、保存先オブジェクトを取り出しておく
      let _dijkstra = v.data('_dijkstra')

      // 2-1. δ(v)=w(source, v)に更新する

      // sourceとvの間にあるエッジをすべて取得する
      let edges = source.edgesWith(v);

      // その中から最小の重みを持つエッジだけを取得
      edges = get_minimum_weight_edges(edges)

      // それらエッジのidの一覧を取得する
      let edge_ids = [];
      edges.forEach(edge => {
        edge_ids.push(edge.id());
      });

      // そのエッジの重みを取得する
      let weight = edges[0].data('weight') || 1;

      // δ(v)をその重みに設定する
      _dijkstra['distance'] = weight

      // 2-2. vはポインタでsourceを指す
      // ポインタはノードだけでなくエッジも指すことにする
      _dijkstra['pointer_nodes'] = [source_id]
      _dijkstra['pointer_edges'] = edge_ids

    });

    //
    // 次のSTEP3の処理を、全ノードが集合Lに格納されるまで続ける
    //
    while(exists_unvisited_node(nodes)) {

      //
      // STEP3
      //

      // まだLに入っていない頂点、すなわちvisitedがFalseのノードの中で δ が最小のものを選びvとする
      let min_distance_nodes = get_minimum_distance_nodes_from_unvisited(nodes);

      // vの候補が複数ある場合は任意の一つを選ぶ（先頭の要素を選ぶ）
      let v = min_distance_nodes[0];
      let v_id = v.id();

      // vをLに入れる、すなわちvisitedフラグを立てる
      // どこにもつながってない孤立したノードであっても、この時点でvisitedになる
      v.data('_dijkstra')['visited'] = true;

      // 次にこのvに隣接している頂点のうち、
      for (let u of v.neighborhood().nodes()) {

        // まだLに入っていない頂点 u に対してのみ、すなわち訪問済みは無視して、
        if (u.data('_dijkstra').visited) {
          continue;
        }

        // 3-1. δ(u)の新しい値を
        // δ(u) = min(δ(u), δ(v) + w(v, u))
        // とする

        // vとuの間のエッジをすべて取得する
        let edges = u.edgesWith(v);

        // その中から最小の重みを持つエッジだけを取得
        edges = get_minimum_weight_edges(edges)

        // それらエッジのidの一覧を取得する
        edge_ids = [];
        edges.forEach(edge => {
          edge_ids.push(edge.id());
        });

        // エッジに付与されている重みを取得する
        weight = edges[0].data('weight');

        // 3-2. δ(u)の値と、v経由の距離で比較して、小さい経路が見つかれば更新する
        // δ(u)を更新した、すなわち新しい経路を見つけたなら、uはポインタでvを指す
        if (u.data('_dijkstra').distance < v.data('_dijkstra').distance + weight) {
          // 既存の値の方が小さい場合は更新しない
          //
        } else if (u.data('_dijkstra').distance > v.data('_dijkstra').distance + weight) {
          // 新しい値の方が小さい場合は更新する
          u.data('_dijkstra').distance = v.data('_dijkstra').distance + weight;

          // ポインタを更新する
          u.data('_dijkstra')['pointer_nodes'] = [v_id];
          u.data('_dijkstra')['pointer_edges'] = edge_ids;
        } else if (u.data('_dijkstra').distance == v.data('_dijkstra').distance + weight) {
          // 既存の値と同じ場合は、その経路も使える、ということなのでポインタを追加する
          u.data('_dijkstra')['pointer_nodes'].push(v_id);
          u.data('_dijkstra')['pointer_edges'].push(...edge_ids);
        }

      }

    }

  };


})();
