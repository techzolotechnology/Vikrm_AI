"""
Task Graph Builder & Topological DAG Engine.

Builds a Directed Acyclic Graph (DAG) of generation tasks from RequirementSpec and ProjectPlan.
Performs cycle detection (Kahn's / DFS algorithm) and topological batching.
"""

from typing import Dict, List, Set, Tuple
from pydantic import BaseModel, Field
from app.services.project.requirement_analysis_service import RequirementSpec
from app.services.project.architecture_planner import ProjectPlan
from app.core.logging import get_logger

logger = get_logger(__name__)


class CircularDependencyError(Exception):
    """Raised when a circular dependency cycle is detected in task graph."""
    pass


class TaskNode(BaseModel):
    id: str
    name: str
    dependencies: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)
    batch_tier: int = 1


class TaskGraph(BaseModel):
    nodes: Dict[str, TaskNode] = Field(default_factory=dict)

    def add_node(self, node: TaskNode) -> None:
        self.nodes[node.id] = node

    def add_dependency(self, node_id: str, depends_on_id: str) -> None:
        if node_id in self.nodes and depends_on_id in self.nodes:
            if depends_on_id not in self.nodes[node_id].dependencies:
                self.nodes[node_id].dependencies.append(depends_on_id)


class TaskGraphBuilder:
    @staticmethod
    def build_graph(spec: RequirementSpec, plan: ProjectPlan) -> TaskGraph:
        """
        Constructs a task dependency graph for project modules and files.
        """
        graph = TaskGraph()

        # 1. Base Configuration Node
        graph.add_node(TaskNode(id="config", name="Base Configuration", dependencies=[], files=["package.json", "tsconfig.json", "vite.config.ts", ".gitignore", ".env.example"], batch_tier=1))

        # 2. Database Schema Node
        graph.add_node(TaskNode(id="db", name="Database & Models", dependencies=["config"], files=["server/main.py", "server/requirements.txt"], batch_tier=2))

        # 3. Authentication Node
        graph.add_node(TaskNode(id="auth", name="Authentication & RBAC", dependencies=["config", "db"], files=["src/api/apiClient.ts", "src/context/AuthContext.tsx", "src/routes/ProtectedRoute.tsx", "src/pages/LoginPage.tsx"], batch_tier=3))

        # 4. Feature Modules Nodes
        deps = ["config", "db", "auth"]
        for idx, module_name in enumerate(plan.modules, start=1):
            mod_id = f"mod_{idx}_{module_name.lower().replace(' ', '_')}"
            f_list = [f"src/components/{module_name}/{module_name}Card.tsx", f"src/pages/{module_name}Page.tsx"]
            graph.add_node(TaskNode(id=mod_id, name=f"Module: {module_name}", dependencies=deps, files=f_list, batch_tier=4))

        # 5. App Root Node
        graph.add_node(TaskNode(id="root", name="App Assembly & Layout", dependencies=[n.id for n in graph.nodes.values() if n.id != "root"], files=["src/App.tsx", "src/main.tsx", "src/index.css"], batch_tier=5))

        # 6. Test Suite & Deployment
        graph.add_node(TaskNode(id="devops", name="Testing & DevOps", dependencies=["root"], files=["src/__tests__/App.test.tsx", "Dockerfile", "docker-compose.yml", "README.md"], batch_tier=6))

        return graph

    @staticmethod
    def detect_cycles(graph: TaskGraph) -> None:
        """
        DFS cycle detection. Raises CircularDependencyError if cycle exists.
        """
        visited: Dict[str, int] = {node_id: 0 for node_id in graph.nodes}  # 0: unvisited, 1: visiting, 2: visited
        path: List[str] = []

        def dfs(node_id: str):
            visited[node_id] = 1
            path.append(node_id)

            node = graph.nodes[node_id]
            for dep in node.dependencies:
                if dep not in graph.nodes:
                    continue
                if visited[dep] == 1:
                    cycle = " -> ".join(path[path.index(dep):] + [dep])
                    raise CircularDependencyError(f"Circular dependency cycle detected: {cycle}")
                if visited[dep] == 0:
                    dfs(dep)

            visited[node_id] = 2
            path.pop()

        for n_id in graph.nodes:
            if visited[n_id] == 0:
                dfs(n_id)

    @staticmethod
    def topological_sort(graph: TaskGraph) -> List[List[TaskNode]]:
        """
        Returns topologically sorted batches of TaskNodes ready for concurrent execution.
        """
        TaskGraphBuilder.detect_cycles(graph)

        in_degree: Dict[str, int] = {n_id: 0 for n_id in graph.nodes}
        dependent_map: Dict[str, List[str]] = {n_id: [] for n_id in graph.nodes}

        for n_id, node in graph.nodes.items():
            for dep in node.dependencies:
                if dep in graph.nodes:
                    in_degree[n_id] += 1
                    dependent_map[dep].append(n_id)

        batches: List[List[TaskNode]] = []
        zero_in_degree = [n_id for n_id, deg in in_degree.items() if deg == 0]

        while zero_in_degree:
            current_batch = [graph.nodes[n_id] for n_id in zero_in_degree]
            batches.append(current_batch)

            next_zero: List[str] = []
            for node in current_batch:
                for dep_id in dependent_map[node.id]:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        next_zero.append(dep_id)

            zero_in_degree = next_zero

        return batches
