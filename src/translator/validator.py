"""Semantic validation for Skill workflows."""

import re
from typing import Dict, List, Set, Tuple
from .models.skill import SkillYAML, NodeModel


class ValidationError(Exception):
    """Raised when workflow validation fails."""
    pass


class WorkflowValidator:
    """Validate workflow logic and dependencies."""
    
    def __init__(self, skill: SkillYAML):
        self.skill = skill
        self.workflow = skill.skill.workflow
        self.nodes = {node.id: node for node in self.workflow.nodes}
        self.edges = self.workflow.edges
        self.graph = None
        self.available_outputs = {}  # node_id -> set of output names
        
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for duplicate node IDs
        node_ids = [node.id for node in self.workflow.nodes]
        duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
        if duplicates:
            errors.append(f"Duplicate node IDs found: {set(duplicates)}")
        
        # Check edges reference valid nodes
        for edge in self.edges:
            if edge.source_node not in self.nodes:
                errors.append(f"Edge references non-existent source node: {edge.source_node}")
            if edge.target_node not in self.nodes:
                errors.append(f"Edge references non-existent target node: {edge.target_node}")
        
        # Build graph for topology checks
        try:
            self.graph = self._build_graph()
        except Exception as e:
            errors.append(f"Failed to build graph: {str(e)}")
            return False, errors
        
        # Check for cycles - LangGraph doesn't have built-in cycle detection,
        # so we'll use a simple topological sort approach
        try:
            topo_order = self._get_topological_order()
        except ValueError as e:
            errors.append(f"Workflow contains cycles: {str(e)}")
        
        # Build available outputs map
        self._build_outputs_map()
        
        # Check variable references
        var_errors = self._validate_variable_references()
        errors.extend(var_errors)
        
        # Check node-specific configurations
        config_errors = self._validate_node_configs()
        errors.extend(config_errors)
        
        return len(errors) == 0, errors
    
    def _build_graph(self) -> Dict:
        """Build graph structure for validation (simplified - not actual StateGraph)."""
        # We don't need a full StateGraph for validation, just structure
        # Return a dict representation for compatibility
        return {
            'nodes': [node.id for node in self.workflow.nodes],
            'edges': [(e.source_node, e.target_node) for e in self.edges]
        }
    
    def _build_outputs_map(self):
        """Build map of available outputs from each node."""
        # Get topological order
        try:
            topo_order = self._get_topological_order()
        except:
            return  # If there's a cycle, we can't determine order
        
        # Track cumulative available variables
        available = set()
        
        # Add input parameters as available
        for param in self.skill.skill.inputs.parameters:
            available.add(param.name)
        
        # Process nodes in topological order
        for node_id in topo_order:
            node = self.nodes[node_id]
            self.available_outputs[node_id] = available.copy()
            
            # Add this node's outputs to available set
            # If no outputs declared, infer from node ID (e.g., enrich_results -> enriched_results)
            if node.outputs:
                for output in node.outputs:
                    available.add(output.name)
            else:
                # Infer output name from node ID (convert snake_case to match common patterns)
                # For nodes like "enrich_results", the output might be "enriched_results"
                inferred_name = self._infer_output_name(node_id)
                available.add(inferred_name)
    
    def _validate_variable_references(self) -> List[str]:
        """Check that all {{variable}} references are valid."""
        errors = []
        
        # Get topological order to process dependencies
        try:
            topo_order = self._get_topological_order()
        except ValueError as e:
            return [f"Cannot validate variables due to cyclic workflow: {str(e)}"]
        
        for node_id in topo_order:
            node = self.nodes[node_id]
            available = self.available_outputs.get(node_id, set())
            
            # Extract all {{variable}} references from node config
            variables = self._extract_variables(node)
            
            # Check each variable is available
            for var in variables:
                if var not in available:
                    errors.append(
                        f"Node '{node_id}' references undefined variable '{var}'. "
                        f"Available: {sorted(available)}"
                    )
        
        return errors
    
    def _extract_variables(self, node: NodeModel) -> Set[str]:
        """Extract all {{variable}} references from a node."""
        variables = set()
        pattern = r'\{\{(\w+)\}\}'
        
        # Search in config
        config_dict = node.config.model_dump()
        self._search_dict_for_variables(config_dict, pattern, variables)
        
        return variables
    
    def _search_dict_for_variables(self, obj, pattern: str, variables: Set[str]):
        """Recursively search dictionary/list for variable patterns."""
        if isinstance(obj, dict):
            for value in obj.values():
                self._search_dict_for_variables(value, pattern, variables)
        elif isinstance(obj, list):
            for item in obj:
                self._search_dict_for_variables(item, pattern, variables)
        elif isinstance(obj, str):
            matches = re.findall(pattern, obj)
            variables.update(matches)
    
    def _validate_node_configs(self) -> List[str]:
        """Validate node-specific configuration requirements."""
        errors = []
        
        for node in self.workflow.nodes:
            if node.type == 'function_call':
                if not node.config.function_name:
                    errors.append(f"Node '{node.id}' (function_call) missing function_name")
                # Nodes without outputs are allowed - they're void functions that modify state
            
            elif node.type == 'llm_call':
                if not node.config.prompt_template:
                    errors.append(f"Node '{node.id}' (llm_call) missing prompt_template")
                # LLM calls implicitly output with node_id as variable name
            
            elif node.type == 'visualizer':
                if not node.config.component_type:
                    errors.append(f"Node '{node.id}' (visualizer) missing component_type")
        
        return errors
    
    def _get_topological_order(self) -> List[str]:
        """
        Get topological ordering of nodes using Kahn's algorithm.
        
        Returns:
            List of node IDs in execution order
            
        Raises:
            ValueError: If cycle is detected
        """
        # Build adjacency list and in-degree map
        in_degree = {node.id: 0 for node in self.workflow.nodes}
        adj_list = {node.id: [] for node in self.workflow.nodes}
        
        for edge in self.edges:
            adj_list[edge.source_node].append(edge.target_node)
            in_degree[edge.target_node] += 1
        
        # Kahn's algorithm
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort for determinism
            queue.sort()
            node_id = queue.pop(0)
            result.append(node_id)
            
            for neighbor in adj_list[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(self.workflow.nodes):
            raise ValueError("Cycle detected in workflow graph")
        
        return result
    
    def get_topological_order(self) -> List[str]:
        """
        Get deterministic topological ordering of nodes.
        
        Returns:
            List of node IDs in execution order
        """
        if self.graph is None:
            self.graph = self._build_graph()
        
        return self._get_topological_order()
    
    def _infer_output_name(self, node_id: str) -> str:
        """
        Infer output variable name from node ID.
        
        Common patterns:
        - enrich_results -> enriched_results
        - summarize_findings -> summarized_findings
        - generate_embedding -> embedding (already handled)
        """
        # Common transformations
        transforms = {
            'enrich': 'enriched',
            'summarize': 'summarized',
            'process': 'processed',
            'transform': 'transformed',
        }
        
        parts = node_id.split('_')
        if len(parts) > 1:
            verb = parts[0]
            if verb in transforms:
                return f"{transforms[verb]}_{'_'.join(parts[1:])}"
        
        # Default: use node_id as-is
        return node_id


def validate_skill(skill: SkillYAML) -> Tuple[bool, List[str]]:
    """
    Validate a skill workflow.
    
    Args:
        skill: Parsed SkillYAML object
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    validator = WorkflowValidator(skill)
    return validator.validate()