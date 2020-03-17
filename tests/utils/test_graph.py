from unittest import TestCase

from utils.graph import Graph, CyclicDependencyError


class TestGraph(TestCase):
    def test_topological_sort(self):
        g = Graph()
        g.add_edge(5, 2)
        g.add_edge(5, 0)
        g.add_edge(4, 0)
        g.add_edge(4, 1)
        g.add_edge(2, 3)
        g.add_edge(3, 1)
        sorted_list = g.topological_sort()
        self.assertEqual(sorted_list, [5, 4, 2, 3, 1, 0])

    def test_direct_cyclic_dependency_error(self):
        g = Graph()
        g.add_edge(5, 2)

        with self.assertRaises(CyclicDependencyError):
            g.add_edge(2, 5)

    def test_indirect_cyclic_dependency_error(self):
        g = Graph()
        g.add_edge(5, 2)
        g.add_edge(5, 0)
        g.add_edge(4, 0)
        g.add_edge(4, 1)
        g.add_edge(2, 3)
        g.add_edge(3, 1)

        with self.assertRaises(CyclicDependencyError):
            g.add_edge(1, 2)

    def test_indirect_cyclic_dependency_error_3_levels(self):
        g = Graph()
        g.add_edge(5, 2)
        g.add_edge(5, 0)
        g.add_edge(4, 0)
        g.add_edge(4, 1)
        g.add_edge(2, 3)
        g.add_edge(3, 1)
        g.add_edge(1, 0)

        with self.assertRaises(CyclicDependencyError) as context:
            g.add_edge(0, 2)

        self.assertEqual(context.exception.cycle, [0, 2, 3, 1])

    def test_indirect_cyclic_dependency_error_5_levels(self):
        g = Graph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(3, 4)
        g.add_edge(4, 5)

        with self.assertRaises(CyclicDependencyError) as context:
            g.add_edge(5, 0)

        self.assertEqual(context.exception.cycle, [5, 0, 1, 2, 3, 4])
