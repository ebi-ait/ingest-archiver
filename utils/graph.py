# Python program to print topological sorting of a Directed Acyclic Graph (DAG)
# https://www.geeksforgeeks.org/python-program-for-topological-sorting/
from collections import defaultdict


class Graph:
    def __init__(self):
        self.adjacency_list = defaultdict(list)
        self.visited = {}  # tracks vertices visited during sorting

    def add_edge(self, u, v):
        self.check_cycle(u, v)
        self.adjacency_list[u].append(v)
        self.visited[u] = False
        self.visited[v] = False

    def check_cycle(self, u, v, cycle=None):
        if not cycle:
            cycle = [u, v]
        else:
            cycle.append(v)

        if u in self.adjacency_list[v]:
            raise CyclicDependencyError(f'Cycle found! {cycle} ', cycle)
        for adjacent_vertex in self.adjacency_list[v]:
            self.check_cycle(u, adjacent_vertex, cycle)

    def _topological_sort(self, vertex, stack):
        self.visited[vertex] = True

        for adjacent_vertex in self.adjacency_list[vertex]:
            if not self.visited[adjacent_vertex]:
                self._topological_sort(adjacent_vertex, stack)
        stack.insert(0, vertex)

    def topological_sort(self):
        stack = []

        for vertex in self.visited.keys():
            if not self.visited[vertex]:
                self._topological_sort(vertex, stack)

        return stack


class CyclicDependencyError(Exception):
    def __init__(self, message, cycle):
        self.cycle = cycle
        super(CyclicDependencyError, self).__init__(message)

