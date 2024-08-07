# Dijkstra

ダイクストラのアルゴリズムで最短経路を計算するPythonおよびJavaScriptの実装例です。

<br>

> [!NOTE]
>
> Pythonで実装したものをJavaScriptに移植してますので、実装メモは[Pythonスクリプト dijkstra.py](/bin/dijkstra.py)の方が豊富です。

<br>

> [!NOTE]
>
> Pythonではダイクストラ法以外にもA*や最大流(Ford-Fulkerson法)、ベルマンフォード法、クラスカル法、プリム法などを実装しています。

<br>

実装は効率や速度よりも分かりやすさを重視し、教科書（グラフ理論入門）に記載されている通りに忠実に実装しています。

教科書に記載されている **章末問題** をPython実装で解いた実行例はこの通りです（章末問題は下記に引用しています）。

```bash
$ bin/dijkstra.py
--- fig-3-6.json ---
[['s', 'A', 'E', 'C', 'F', 't']]

--- fig-3-7.json ---
[['s', 'A', 'C', 't'], ['s', 'B', 'D', 't'], ['s', 'A', 'B', 'D', 't']]
```

図3.6の場合は `s -> A -> E -> C -> F -> t` という経路が最短になります。

図3.7の場合は等コストの最短経路が3個存在します。

もちろん、教科書に記載されている解答（下記の解図）と同じです。

![解図3.1](https://takamitsu-iida.github.io/dijkstra/asset/answer-fig-3-1.JPG)

![解図3.2](https://takamitsu-iida.github.io/dijkstra/asset/answer-fig-3-2.JPG)

<br><br>

## ライブデモ

JavaScript実装ではcytoscape.jsの描画機能を使ってグラフを可視化していますので、結果をより分かりやすく把握できます。

こちらの[Live Demo](https://takamitsu-iida.github.io/dijkstra/index.html)を参照。

<br>
<br>

# Reference

グラフのデータ表現は隣接行列や隣接リスト等、様々な記述方法がありますが、ここではcytoscape.jsで用いられているJSON形式を利用しています。

<br>

> [!NOTE] cytoscape.jsのデータ形式
>
> https://js.cytoscape.org/#notation/elements-json

<br>

教科書に記載のグラフ（図3-6および図3-7）をJSONで定義したものは以下のファイルにあります。

> [data/fig3-6.json](https://github.com/takamitsu-iida/dijkstra/blob/master/data/fig-3-6.json)
>
> [data/fig3-7.json](https://github.com/takamitsu-iida/dijkstra/blob/master/data/fig-3-7.json)

ダイクストラアルゴリズムについては以下の書籍（教科書）を参考にしています。
いくつか手に取った本の中でこれが最も分かりやすかったと思います。

<br>

> [!NOTE] 参考文献
>
> グラフ理論入門　宮崎修一 著 森北出版株式会社
>
> [森北出版へのリンク](https://www.morikita.co.jp/books/mid/085281)

<br>

また、図をふんだんに使った以下の本も分かりやすいです。

<br>

> [!NOTE] 参考文献
>
> アルゴリズム図鑑 増補改訂版 石田保輝 宮崎修一著 翔泳社
>
> [翔泳社へのリンク](https://www.shoeisha.co.jp/book/detail/9784798172439)


<br><br><br><br><br>

以下に教科書（グラフ理論入門）に記載されているダイクストラアルゴリズムを引用します。無断引用です。

私が手に取った書籍の中では、この説明が一番分かりやすいと思いました。

<br>

# ３章　最短経路問題

今いる場所から目的地まで、どのようなグラフ経路をたどれば最短で行けるか。これをグラフを使って定式化したのが最短経路問題である。

3.1節で問題を定義し、3.2節でこの問題を効率よく解くダイクストラのアルゴリズムを紹介する。

<br>

## 3.1 最短経路問題

図3.1のグラフの各頂点は、配送業者の中継地点を表している。二つの頂点uとvを結ぶ枝 e=(u,v) の重み w(e) は、荷物を中継所 u から v へ移動させるのに w(e) に比例する時間がかかることを意味する（たとえば、v1からv4に送るのに8時間かかる）。間に枝のない中継所間は直接送ることができない。今 s にある荷物を t に送りたいとき、どの経路を通せば最短で運ぶことができるだろうか。

この問題は、以下の **最短経路問題 (shortest path problem)** として定式化できる。入力として、枝に非負重みの付いた無向グラフ G=(V,E) と2頂点 s, t が与えられる。出力として、 s と t を両端とする G の道の中で、使われる枝の重みの総和（これを道の「長さ」ということを思い出して欲しい）が最小になるもの（最短経路）を求める問題である。

![図3.1](https://takamitsu-iida.github.io/dijkstra/asset/fig-3-1.JPG)

**問題 3.1**

図3.1のグラフに対する最短経路を求めよ。

**解答 3.1**

s→v1→v2→v4→tという経路は、 s から t への長さ10の経路である。これが最短であることは、容易に確かめることができる。

この問題に対して、 s から t までの道をすべて列挙し、それぞれの長さを求め、最短の道を出力するアルゴリズムは、確実に正しい解を出力するが、道の数は頂点数の指数個存在し得るので、計算時間が膨大になる。したがって、より効率的な解法が望まれる。

<br>

## 3.2 ダイクストラのアルゴリズム

最短経路問題を効率よく解くアルゴリズムとして、ダイクストラ (Dijkstra) のアルゴリズムが知られている。このアルゴリズムでは、頂点を格納するための *L* という集合を使う。*L* は最初は空集合 (0) であり、計算が進むにつれてサイズが大きくなっていく。最初は δ(s)=0 であり、 s 以外の頂点 v に対しては δ(v)=∞ とする。すなわち、 s から s へは長さ 0 の道で到達できるが、現段階ではまだ何も調べていないので、 s から他の頂点へどれくらいの長さで到達できるかが（そもそも到達できるかすら）全く分かっていない。そこで、とりあえず無限大という値を付けている。たとえば、アルゴリズムが探索を進めていくうちに、 s から v へ長さ15の道で到達できることがわかったら、 δ(υ)=15 と値が更新される。これもまた暫定値で、将来さらに短い、たとえば長さ12の道が見つかったら、 δ(v)=12 と更新される。このように、 δ(v) の値は、アルゴリズムの計算が進むにつれて（そして、グラフをより広く調べるにつれて）より小さくなっていく。さらに、各頂点はアルゴリズムの実行中に、ポインタで他の頂点を指す。これは、 s から自分までの（暫定的な）最短経路をたどる際の、自分の直前の頂点である。

それでは、図3.1の例を用いて、アルゴリズムの流れを説明していく。

**ステップ１** 上述のように *L*=0、δ(s)=0, δ(v)=∞ (v≠s) と変数を初期化する（図3.2参照）。

![図3.2](https://takamitsu-iida.github.io/dijkstra/asset/fig-3-2.JPG)

**ステップ２** 頂点 s を *L* に入れる。つぎに、 s に隣接している各頂点 v について

(2-1) δ(v)=w(s,v) とする。

(2-2) v はポインタで s を指す（図3.3参照）

なお、図では集合 *L* を灰色で表している。また、枝 (s,v) の重みは、正確には w(s,v) ではなく、w((s,v))と書くべきであるが、ここでは見やすさのためにw(s,v)を使う。

![図3.3](https://takamitsu-iida.github.io/dijkstra/asset/fig-3-3.JPG)

**ステップ３** まだ *L* に入っていない頂点の中で δ の値が最小のものを v とし、 v を *L* に入れる。 v の候補が複数ある場合は任意に一つを選ぶ。つぎに、 v に隣接している頂点のうち、まだ *L* に入っていない頂点 u に対して

(3-1) δ(u) の新しい値を δ(u)=min{ δ(u), δ(v) + w(u, v) } とする

(3-2) δ(u) の値が更新された場合（すなわち δ(v)+w(v, u) < δ(u) の場合）は、uのポインタをvに向け直す。

ここで min{a, b} は a と b のうち小さい方を意味する。

ステップ３の動作を、例を用いて説明する。図3.3の状態において、 δ の値が最も小さい頂点は v1 なので、 v1 が v として選ばれ、 *L* に入れられる（図3.4参照）。v1 に隣接していて、 *L* に入っていない頂点は v2, v3, v4 なので、それぞれに対して (3-1) (3-2) の作業を行う。

v2に対して見てみよう。δ(v2)=10、δ(v1)+w(v1, v2)=2+2=4 なので、後者の方が小さい。よって、δ(v2)=4 と更新され、 v2 から s を指していたポインタは v1 を指し直す。

![図3.4](https://takamitsu-iida.github.io/dijkstra/asset/fig-3-4.JPG)

これは、以下のように解釈できる。 *L* の中に入っている（すなわち、これまでにチェックした）頂点を経由して v2 に至る最短経路の長さは10であった。そして、その経路 v2 から s までポインタをたどったものであり、今の例では s→v2 という経路である。探索が1ステップ進んで v1 が *L* に入り、 v1 を経由する経路も調べると、今度は s→v1→v2 という経路が見つかった。そして、この経路は、今まで知っていた経路よりも短い。そこで、暫定的な最短経路の長さを4に更新し、最短経路での v2 の直前の頂点を s から v1 に更新したのである。 v3 と v4 に対しても同様の操作を行った結果が図3.4である。

あとは、頂点 t が *L* に入るまでステップを繰り返す。 t が *L* に入った時点で t からポインタをたどり s まで進むと最短経路が得られ、その長さは δ(t) である（図3.5）。

![図3.5](https://takamitsu-iida.github.io/dijkstra/asset/fig-3-5.JPG)

各繰り返しごとに一つの頂点が *L* に入り、すべての頂点が *L* に入ればアルゴリズムは終了するので、頂点数を n とすると繰り返し回数は高々 n 回である。正しさの証明は省略するが、以下のような方針で行えばよい。示すべきことは、「アルゴリズムの任意の時点で、v∈*L* である任意の頂点について、 δ(v) は s から v への**暫定ではなく本当の**最短経路の長さである」という命題である。もしこれを示すことができたとすると、 t が *L* に入った時点での δ(t) を出力するわけだから、アルゴリズムの正しさが示せたことになる。

上記の命題は、 帰納法により証明する。アルゴリズムの最初の時点では、 s だけしか *L* に入っておらず、δ(s)=0 なので確かに成り立つ。帰納的に行う部分では、ある時点（k回目の繰り返しの直後）で成立していると仮定し、k+1回目の繰り返し直後（すなわち、δ値の最も小さい頂点 v* を *L* に入れ、v* が隣接している頂点について更新作業を行ったあと）でも成り立つことを示せばよい。ということは、結局 k 回目の繰り返しの直後において、δ(v*) が s から v* までの（暫定ではなく）真の最短経路の長さになっていることを示せばよいことになる。


<br><br>

## 章末問題１．

ダイクストラのアルゴリズムを使って、図3.6のグラフに対する最短経路を求めよ。

![図3.6](https://takamitsu-iida.github.io/dijkstra/asset/fig-3-6.JPG)

## 章末問題１．解答

以下の解図3.1のとおりである。

![解図3.1](https://takamitsu-iida.github.io/dijkstra/asset/answer-fig-3-1.JPG)

<br><br>

## 章末問題２．

ダイクストラのアルゴリズムは、 s から t への最短経路が複数あった場合、そのうちの一つを求める。すべての最短経路を求めるためには、ダイクストラのアルゴリズムをどのように修正すればよいか述べよ。

## 章末問題２．解答

ダイクストラのアルゴリズムでは、ステップ３の (3-2) において δ(u) の値が更新された場合に、 u のポインタを v に向け直していた。よって、 δ(u)=δ(v)+w(v,u)の場合には、ポインタの操作は何もしない。修正後のアルゴリズムでは、δ(u)=δ(v)+w(v,u) の場合、古いポインタは残したままで、新たに u から v へのポインタを張ることにする。これは、 v からくる経路も、現在見つかっている暫定の最短経路と同じ長さで u に到達できることを意味する。最後に t から s へポインタを逆にたどる経路はすべて最短経路である。

<br><br>

## 章末問題３．

図3.7のグラフに対して、上記の問題２のアルゴリズムを適用させ、 s から t への最短経路をすべて求めよ。

![図3.7](https://takamitsu-iida.github.io/dijkstra/asset/fig-3-7.JPG)

<br><br>

## 章末問題３．解答

以下の解図3.2のとおり。 s から t への最短経路の長さは6で、三つの最短経路が存在する。

![解図3.2](https://takamitsu-iida.github.io/dijkstra/asset/answer-fig-3-2.JPG)
