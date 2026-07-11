import networkx as nx
from uuid import UUID
from switchboard.types.task import Task, TaskStatus

class Workflow:
    """
    Structural graph representation and dependency resolution for a DAG of Tasks.
    Focuses strictly on representation (not execution).
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._graph = nx.DiGraph()

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    def add_task(self, task: Task) -> None:
        """Add a Task node to the workflow DAG."""
        self._graph.add_node(task.task_id, task=task)

    def add_dependency(self, parent_id: UUID, child_id: UUID) -> None:
        """
        Record a dependency: child_id depends on parent_id.
        
        Args:
            parent_id: UUID of the prerequisite task.
            child_id: UUID of the dependent task.
        """
        if not self._graph.has_node(parent_id) or not self._graph.has_node(child_id):
            raise ValueError("Both parent and child tasks must exist in the Workflow before drawing dependencies.")
        
        # Link in graph: parent_id -> child_id
        self._graph.add_edge(parent_id, child_id)
        
        # Also update child Task's inline dependencies list
        child_task = self._graph.nodes[child_id]["task"]
        if parent_id not in child_task.dependencies:
            child_task.dependencies.append(parent_id)

    def get_ready_tasks(self) -> list[Task]:
        """
        Identify tasks whose prerequisites are completely satisfied (COMPLETED)
        and are ready for execution scheduling.
        
        Returns:
            List of Task objects in CREATED status ready to run.
        """
        ready: list[Task] = []
        
        for node_id, data in self._graph.nodes(data=True):
            task: Task = data["task"]
            if task.status not in (TaskStatus.CREATED, TaskStatus.QUEUED):
                continue
                
            # Find prerequisites (incoming edges)
            parents = list(self._graph.predecessors(node_id))
            
            # If all parent nodes are COMPLETED, this task is ready
            if all(self._graph.nodes[p]["task"].status == TaskStatus.COMPLETED for p in parents):
                ready.append(task)
                
        return ready

    def get_task(self, task_id: UUID) -> Task:
        """Retrieve a task from the workflow graph."""
        if not self._graph.has_node(task_id):
            raise ValueError(f"Task '{task_id}' not found in workflow '{self.name}'.")
        return self._graph.nodes[task_id]["task"]
