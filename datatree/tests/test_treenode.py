import pytest
from anytree.resolver import ChildResolverError

from datatree.treenode import TreeError, TreeNode
from datatree.iterators import PreOrderIter, LevelOrderIter


class TestFamilyTree:
    def test_lonely(self):
        root = TreeNode()
        assert root.parent is None
        assert root.children == {}

    def test_parenting(self):
        john = TreeNode()
        mary = TreeNode()
        mary._set_parent(john, "Mary")

        assert mary.parent == john
        assert john.children["Mary"] is mary

    def test_parent_swap(self):
        john = TreeNode()
        mary = TreeNode()
        mary._set_parent(john, "Mary")

        steve = TreeNode()
        mary._set_parent(steve, "Mary")

        assert mary.parent == steve
        assert steve.children["Mary"] is mary
        assert "Mary" not in john.children

    def test_multi_child_family(self):
        mary = TreeNode()
        kate = TreeNode()
        john = TreeNode(children={"Mary": mary, "Kate": kate})
        assert john.children["Mary"] is mary
        assert john.children["Kate"] is kate
        assert mary.parent is john
        assert kate.parent is john

    def test_disown_child(self):
        mary = TreeNode()
        john = TreeNode(children={"Mary": mary})
        mary.orphan()
        assert mary.parent is None
        assert "Mary" not in john.children

    def test_doppelganger_child(self):
        kate = TreeNode()
        john = TreeNode()

        with pytest.raises(TypeError):
            john.children = {"Kate": 666}

        with pytest.raises(TreeError, match="Cannot add same node"):
            john.children = {"Kate": kate, "Evil_Kate": kate}

        john = TreeNode(children={"Kate": kate})
        evil_kate = TreeNode()
        evil_kate._set_parent(john, "Kate")
        assert john.children["Kate"] is evil_kate

    # TODO test setting children via __setitem__ syntax

    def test_sibling_relationships(self):
        mary = TreeNode()
        kate = TreeNode()
        ashley = TreeNode()
        TreeNode(children={"Mary": mary, "Kate": kate, "Ashley": ashley})
        assert kate.siblings["Mary"] is mary
        assert kate.siblings["Ashley"] is ashley
        assert "Kate" not in kate.siblings

    def test_ancestors(self):
        tony = TreeNode()
        michael = TreeNode(children={"Tony": tony})
        vito = TreeNode(children={"Michael": michael})
        assert tony.root is vito
        assert tony.lineage == (tony, michael, vito)
        assert tony.ancestors == (vito, michael, tony)


def create_test_tree():
    f = TreeNode()
    b = TreeNode()
    a = TreeNode()
    d = TreeNode()
    c = TreeNode()
    e = TreeNode()
    g = TreeNode()
    i = TreeNode()
    h = TreeNode()

    f.children = {"b": b, "g": g}
    b.children = {"a": a, "d": d}
    d.children = {"c": c, "e": e}
    g.children = {"i": i}
    i.children = {"h": h}

    return f


class TestIterators:
    def test_preorderiter(self):
        tree = create_test_tree()
        result = list(PreOrderIter(tree))
        expected = [f, b, g, a, d, i, c, e, h]
        assert result == expected


class TestGetNodes:
    def test_get_child(self):
        john = TreeNode("john")
        mary = TreeNode("mary", parent=john)
        assert john.get_node("mary") is mary
        assert john.get_node(("mary",)) is mary

    def test_get_nonexistent_child(self):
        john = TreeNode("john")
        TreeNode("jill", parent=john)
        with pytest.raises(ChildResolverError):
            john.get_node("mary")

    def test_get_grandchild(self):
        john = TreeNode("john")
        mary = TreeNode("mary", parent=john)
        sue = TreeNode("sue", parent=mary)
        assert john.get_node("mary/sue") is sue
        assert john.get_node(("mary", "sue")) is sue

    def test_get_great_grandchild(self):
        john = TreeNode("john")
        mary = TreeNode("mary", parent=john)
        sue = TreeNode("sue", parent=mary)
        steven = TreeNode("steven", parent=sue)
        assert john.get_node("mary/sue/steven") is steven
        assert john.get_node(("mary", "sue", "steven")) is steven

    def test_get_from_middle_of_tree(self):
        john = TreeNode("john")
        mary = TreeNode("mary", parent=john)
        sue = TreeNode("sue", parent=mary)
        steven = TreeNode("steven", parent=sue)
        assert mary.get_node("sue/steven") is steven
        assert mary.get_node(("sue", "steven")) is steven


class TestSetNodes:
    def test_set_child_node(self):
        john = TreeNode("john")
        mary = TreeNode("mary")
        john.set_node("/", mary)

        mary = john.children[0]
        assert mary.name == "mary"
        assert isinstance(mary, TreeNode)
        assert mary.children == ()

    def test_child_already_exists(self):
        john = TreeNode("john")
        TreeNode("mary", parent=john)
        marys_replacement = TreeNode("mary")

        with pytest.raises(KeyError):
            john.set_node("/", marys_replacement, allow_overwrite=False)

    def test_set_grandchild(self):
        john = TreeNode("john")
        mary = TreeNode("mary")
        rose = TreeNode("rose")
        john.set_node("/", mary)
        john.set_node("/mary/", rose)

        mary = john.children[0]
        assert mary.name == "mary"
        assert isinstance(mary, TreeNode)
        assert rose in mary.children

        rose = mary.children[0]
        assert rose.name == "rose"
        assert isinstance(rose, TreeNode)
        assert rose.children == ()

    def test_set_grandchild_and_create_intermediate_child(self):
        john = TreeNode("john")
        rose = TreeNode("rose")
        john.set_node("/mary/", rose)

        mary = john.children[0]
        assert mary.name == "mary"
        assert isinstance(mary, TreeNode)
        assert mary.children[0] is rose

        rose = mary.children[0]
        assert rose.name == "rose"
        assert isinstance(rose, TreeNode)
        assert rose.children == ()

    def test_no_intermediate_children_allowed(self):
        john = TreeNode("john")
        rose = TreeNode("rose")
        with pytest.raises(KeyError, match="Cannot reach"):
            john.set_node(
                path="mary", node=rose, new_nodes_along_path=False, allow_overwrite=True
            )

    def test_set_great_grandchild(self):
        john = TreeNode("john")
        mary = TreeNode("mary", parent=john)
        rose = TreeNode("rose", parent=mary)
        sue = TreeNode("sue")
        john.set_node("mary/rose", sue)
        assert sue.parent is rose

    def test_overwrite_child(self):
        john = TreeNode("john")
        mary = TreeNode("mary")
        john.set_node("/", mary)
        assert mary in john.children

        marys_evil_twin = TreeNode("mary")
        john.set_node("/", marys_evil_twin)
        assert marys_evil_twin in john.children
        assert mary not in john.children

    def test_dont_overwrite_child(self):
        john = TreeNode("john")
        mary = TreeNode("mary")
        john.set_node("/", mary)
        assert mary in john.children

        marys_evil_twin = TreeNode("mary")
        with pytest.raises(KeyError, match="path already points"):
            john.set_node(
                "", marys_evil_twin, new_nodes_along_path=True, allow_overwrite=False
            )
        assert mary in john.children
        assert marys_evil_twin not in john.children


class TestPruning:
    ...


class TestPaths:
    def test_pathstr(self):
        john = TreeNode("john")
        mary = TreeNode("mary", parent=john)
        rose = TreeNode("rose", parent=mary)
        sue = TreeNode("sue", parent=rose)
        assert sue.pathstr == "john/mary/rose/sue"

    def test_relative_path(self):
        ...


class TestTags:
    ...


class TestRenderTree:
    def test_render_nodetree(self):
        mary = TreeNode("mary")
        kate = TreeNode("kate")
        john = TreeNode("john", children=[mary, kate])
        TreeNode("Sam", parent=mary)
        TreeNode("Ben", parent=mary)

        printout = john.__str__()
        expected_nodes = [
            "TreeNode('john')",
            "TreeNode('mary')",
            "TreeNode('Sam')",
            "TreeNode('Ben')",
            "TreeNode('kate')",
        ]
        for expected_node, printed_node in zip(expected_nodes, printout.splitlines()):
            assert expected_node in printed_node
