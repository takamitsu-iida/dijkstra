#!/usr/bin/env python

# 疎集合データ構造（Union-Find）がどんなものかを理解するためのサンプルコードです。
# 以下のコードは、AtCoderのライブラリを参考にしています。

# 疎集合データ構造（Union-Find）については、この資料が分かりやすいです。
# https://www.slideshare.net/slideshow/union-find-49066733/49066733


#
# Union-Find
#

from collections import defaultdict

class UnionFind:

    def __init__(self, n):
        # 要素の数を最初に与える
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
            # 自分の親を、自分の親の親（の親・・・）に更新することで木を平準化する
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
            # ルートの要素数を加算する
            self.parents[root_y] += self.parents[root_x]

            # xの親をyに変更する
            self.parents[root_x] = root_y
        else:
            # xの方が要素が多いので、yをxにくっつける
            # ルートの要素数を加算する
            self.parents[root_x] += self.parents[root_y]
            # yの親をxに変更する
            self.parents[root_y] = root_x

    def size(self, x):
        return -self.parents[self.find(x)]

    def is_same(self, x, y):
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



class UnionFindDict:

    def __init__(self):

        # 要素と親の対応を格納する辞書
        self.parent_map = {}

        # 親がどれだけの要素を持っているかを格納する辞書
        self.size_map = {}

    def insert(self, element):
        # 登録されていない要素を渡されたら、自分自身を親として登録する
        if element not in self.parent_map:
            self.parent_map[element] = element
            self.size_map[element] = 1


    def insert_group(self, elements):
        for element in elements:
            self.insert(element)
            root = self.find(element)

            for other_element in elements:
                if other_element == element:
                    continue
                self.insert(other_element)
                if self.find(other_element) != root:
                    self.union(root, other_element)


    def find(self, element):
        if element not in self.parent_map:
            return None

        if self.parent_map[element] == element:
            return element

        # 経路圧縮する
        parent = self.parent_map[element]
        while parent != self.parent_map[parent]:
            grandparent = self.parent_map[parent]
            self.parent_map[parent] = grandparent
            parent = grandparent

        return self.find(self.parent_map[element])


    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return

        size_x = self.size_map[root_x]
        size_y = self.size_map[root_y]

        if size_x >= size_y:
            self.parent_map[root_y] = root_x
            self.size_map[root_x] += size_y
        else:
            self.parent_map[root_x] = root_y
            self.size_map[root_y] += size_x

    def is_same(self, x, y):
        return self.find(x) == self.find(y)

    def members(self, x):
        root = self.find(x)
        return [k for k, v in self.parent_map.items() if self.find(k) == root]

    def roots(self):
        return [k for k, v in self.parent_map.items() if k == v]

    def group_count(self):
        return len(self.roots())

    def all_group_members(self):
        group_members = defaultdict(list)
        for k, v in self.parent_map.items():
            group_members[self.find(k)].append(k)
        return group_members

    def __str__(self):
        return '\n'.join(f'{r}: {m}' for r, m in self.all_group_members().items())


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

    def test_union_find_dict():
        # Union-Find Dictを作成
        uf = UnionFindDict()

        print("insert A")
        uf.insert("A")
        assert uf.find("A") == "A", f"Error: {uf.find('A')} should be A"

        print("insert B, C, D")
        uf.insert("B")
        uf.insert("C")
        uf.insert("D")
        print(uf)
        print(f"uf.roots() = {uf.roots()}")
        print(f"uf.all_group_members() = {uf.all_group_members()}")
        print(f"uf.parents = {uf.parent_map}")
        print('')
        # A B C D

        print("union('B', 'C')")
        uf.union("B", "C")
        assert uf.find("C") == "B", f"Error: {uf.find('C')} should be B"

        print(uf)
        print(f"uf.roots() = {uf.roots()}")
        print(f"uf.all_group_members() = {uf.all_group_members()}")
        print(f"uf.parents = {uf.parent_map}")
        print('')
        # A B D
        #   |
        #   C

        # 各要素の親要素と、要素同士が同じグループかどうかを確認
        assert uf.is_same("A", "B") == False, f"Error: A and B should be different group"
        assert uf.is_same("B", "C") == True, f"Error: B and C should be same group"
        assert uf.is_same("C", "D") == False, f"Error: C and D should be different group"

        print("union('A', 'D')")
        uf.union("A", "D")
        assert uf.find("D") == "A", f"Error: {uf.find('D')} should be A"

        print(uf)
        print(f"uf.roots() = {uf.roots()}")
        print(f"uf.all_group_members() = {uf.all_group_members()}")
        print(f"uf.parents = {uf.parent_map}")
        print('')
        # A B
        # | |
        # D C

        print("union('B', 'A')")
        uf.union("A", "B")
        assert uf.find("C") == "A", f"Error: {uf.find('C')} should be A"
        assert uf.find("B") == "A", f"Error: {uf.find('B')} should be A"
        assert uf.find("D") == "A", f"Error: {uf.find('D')} should be A"
        assert uf.find("A") == "A", f"Error: {uf.find('A')} should be A"

        print(uf)
        print(f"uf.roots() = {uf.roots()}")
        print(f"uf.all_group_members() = {uf.all_group_members()}")
        print(f"uf.parents = {uf.parent_map}")
        print('')
        # A
        # |
        # D
        # |
        # B
        # |
        # C

        uf = UnionFindDict()
        uf.insert_group(["A", "B", "C", "D"])
        print("insert_group(['A', 'B', 'C', 'D'])")
        print(uf)
        print(f"uf.roots() = {uf.roots()}")
        print(f"uf.all_group_members() = {uf.all_group_members()}")
        print(f"uf.parents = {uf.parent_map}")
        print('')

    def main():
        # test_union_find()
        test_union_find_dict()

        return 0

    # 実行
    sys.exit(main())
