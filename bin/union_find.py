#!/usr/bin/env python

# 疎集合データ構造（Union-Find）を用いてクラスタリングを行うスクリプトです。

# 疎集合データ構造（Union-Find）については、この資料が分かりやすいです。
# https://www.slideshare.net/slideshow/union-find-49066733/49066733

#
# Union-Find
#

from collections import defaultdict

class UnionFind:

    def __init__(self, n):
        # 要素の数
        self.n = n

        # 各要素の親要素の番号を格納するリスト
        # 要素がルートの場合には、そのグループに属している要素の数*(-1)を格納する
        # 初期状態では各要素が独立したグループに属するものとして、[-1, -1, -1, ...] で初期化する
        self.parents = [-1] * n

    def find(self, x):
        # 要素xが属するグループのルートを返す
        # 同時に親を差し替えてツリーを平準化する
        #     o         o
        #    / \       /|\
        #   o   o     * o o
        #   |
        #   *
        if self.parents[x] < 0:
            return x
        else:
            # 自分の親を、自分の親の親（の親・・・）に更新する
            self.parents[x] = self.find(self.parents[x])

            # 一番上まで行かないとここには来ない
            return self.parents[x]

    def union(self, x, y):
        # xが属しているグループと、yが属しているグループを併合する
        root_x = self.find(x)
        root_y = self.find(y)

        # xの親とyの親が同じであれば、最初から併合されている
        if root_x == root_y:
            return

        # 要素が多いグループにくっつける
        # ルートの親は負の値で、値が要素数を表すため、値が小さい方が要素数が多い
        if self.parents[root_x] > self.parents[root_y]:
            # yの方が要素が多いので、xをyにくっつける
            self.parents[root_y] += self.parents[root_x]
            self.parents[root_x] = root_y
        else:
            # xの方が要素が多いので、yをxにくっつける
            self.parents[root_x] += self.parents[root_y]
            self.parents[root_y] = root_x

    def size(self, x):
        return -self.parents[self.find(x)]

    def same(self, x, y):
        return self.find(x) == self.find(y)

    def members(self, x):
        root = self.find(x)
        return [i for i in range(self.n) if self.find(i) == root]

    def roots(self):
        return [i for i, x in enumerate(self.parents) if x < 0]

    def group_count(self):
        return len(self.roots())

    def all_group_members(self):
        group_members = defaultdict(list)
        for member in range(self.n):
            group_members[self.find(member)].append(member)
        return group_members

    def __str__(self):
        return '\n'.join(f'{r}: {m}' for r, m in self.all_group_members().items())


class UnionFindLabel(UnionFind):
    def __init__(self, labels):
        assert len(labels) == len(set(labels))

        self.n = len(labels)
        self.parents = [-1] * self.n
        self.d = {x: i for i, x in enumerate(labels)}
        self.d_inv = {i: x for i, x in enumerate(labels)}

    def find_label(self, x):
        return self.d_inv[super().find(self.d[x])]

    def union(self, x, y):
        super().union(self.d[x], self.d[y])

    def size(self, x):
        return super().size(self.d[x])

    def same(self, x, y):
        return super().same(self.d[x], self.d[y])

    def members(self, x):
        root = self.find(self.d[x])
        return [self.d_inv[i] for i in range(self.n) if self.find(i) == root]

    def roots(self):
        return [self.d_inv[i] for i, x in enumerate(self.parents) if x < 0]

    def all_group_members(self):
        group_members = defaultdict(list)
        for member in range(self.n):
            group_members[self.d_inv[self.find(member)]].append(self.d_inv[member])
        return group_members




if __name__ == '__main__':

    import sys

    def test_union_find():
        # 6要素のUnion-Findを作成
        uf = UnionFind(6)
        print('uf = UnionFind(6)')
        print(uf)
        print('')

        # 0と2を併合
        uf.union(0, 2)
        print('uf.union(0, 2)')
        print(uf)
        print('')

        # 1と3を併合
        uf.union(1, 3)
        print('uf.union(1, 3)')
        print(uf)
        print('')

        # 4と5を併合
        uf.union(4, 5)
        print('uf.union(4, 5)')
        print(uf)
        print('')

        # 1と4を併合
        uf.union(1, 4)
        print('uf.union(1, 4)')
        print(uf)
        print('')

        print('parents')
        print(uf.parents)


    def main():
        test_union_find()


        return 0

    # 実行
    sys.exit(main())
