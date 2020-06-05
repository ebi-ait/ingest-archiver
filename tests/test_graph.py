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
        self.assertEqual([4, 5, 0, 2, 3, 1], sorted_list)

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

        self.assertEqual([0, 2, 3, 1], context.exception.cycle)

    def test_indirect_cyclic_dependency_error_5_levels(self):
        g = Graph()
        g.add_edge(0, 1)
        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(3, 4)
        g.add_edge(4, 5)

        with self.assertRaises(CyclicDependencyError) as context:
            g.add_edge(5, 0)

        self.assertEqual([5, 0, 1, 2, 3, 4], context.exception.cycle)

    def test_topological_sort_for_strings(self):
        g = Graph()
        g.add_edge('donor', 'specimen')
        g.add_edge('specimen', 'cell_suspension')

        sorted_list = g.topological_sort()
        self.assertEqual(['donor', 'specimen', 'cell_suspension'], sorted_list)

    def test_topological_sort_5_levels_for_strings(self):
        g = Graph()
        g.add_edge('donor', 'specimen')
        g.add_edge('specimen', 'cell_suspension')
        g.add_edge('cell_suspension', 'cs2')
        g.add_edge('cs2', 'cs3')
        g.add_edge('cs3', 'cs4')

        sorted_list = g.topological_sort()
        self.assertEqual(['donor', 'specimen', 'cell_suspension', 'cs2', 'cs3', 'cs4'], sorted_list)

    def test_direct_cyclic_dependency_error_for_strings(self):
        g = Graph()
        g.add_edge('donor', 'specimen')

        with self.assertRaises(CyclicDependencyError) as context:
            g.add_edge('specimen', 'donor')

        self.assertEqual(['specimen', 'donor'], context.exception.cycle)

    def test_indirect_cyclic_dependency_error_5_levels_for_strings(self):
        g = Graph()
        g.add_edge('donor', 'specimen')
        g.add_edge('specimen', 'cs')
        g.add_edge('cs', 'cs2')
        g.add_edge('cs2', 'cs3')
        g.add_edge('cs3', 'cs4')

        with self.assertRaises(CyclicDependencyError) as context:
            g.add_edge('cs4', 'donor')

        self.assertEqual(['cs4', 'donor', 'specimen', 'cs', 'cs2', 'cs3'], context.exception.cycle)
