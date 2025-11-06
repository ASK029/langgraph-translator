"""
Auto-generated LangGraph workflow from Skill YAML.

Skill: Find Similar Work Orders
Generated: 2025-11-06T19:07:41.570001
"""

from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from mock_functions import MockFunctionLibrary


class GraphState(TypedDict):
    """State for the workflow graph."""
    workorder_description: Any
    limit: Any
    embedding: Any
    similar_workorders: Any
    enriched_results: Any
    summarized_findings: Any
    display_results: Any


class WorkorderSimilaritySearchWorkflow:
    """
    Search for work orders with similar descriptions using vector embeddings
        
    LangGraph workflow implementation.
    """
        
    def __init__(self, mock_seed: str = "workorder_similarity_search"):
        self.mock_lib = MockFunctionLibrary(seed=mock_seed)
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build and compile the LangGraph workflow."""
        graph = StateGraph(GraphState)
        
        # Add all nodes
        graph.add_node("generate_embedding", self._node_generate_embedding)
        graph.add_node("vector_search", self._node_vector_search)
        graph.add_node("enrich_results", self._node_enrich_results)
        graph.add_node("summarize_findings", self._node_summarize_findings)
        graph.add_node("display_results", self._node_display_results)
        
        # Add edges
        graph.add_edge("generate_embedding", "vector_search")
        graph.add_edge("vector_search", "enrich_results")
        graph.add_edge("enrich_results", "summarize_findings")
        graph.add_edge("summarize_findings", "display_results")
        
        # Set entry point
        graph.add_edge(START, "generate_embedding")
        
        # Set exit point
        graph.add_edge("display_results", END)
        
        return graph.compile()
        
    def _node_generate_embedding(self, state: GraphState) -> GraphState:
        """Node: generate_embedding (function_call)"""
        print(f"[Executing] generate_embedding (function_call)")
        
        # Function call node
        # API call
        params = {}
        resolved_params = self._resolve_params(params, state)
        result = self.mock_lib.call_api("/api/embeddings/generate", resolved_params)
        
        # Store outputs - if no outputs, this is a void function that modifies state
        # Single output - store result directly
        state["embedding"] = result
        
        
        print(f"[Completed] generate_embedding")
        return state
        
    def _node_vector_search(self, state: GraphState) -> GraphState:
        """Node: vector_search (function_call)"""
        print(f"[Executing] vector_search (function_call)")
        
        # Function call node
        # Regular function call
        params = {"embedding": "{{embedding}}", "limit": "{{limit}}"}
        resolved_params = self._resolve_params(params, state)
        result = self.mock_lib.call_function("VectorSearchWorkOrders", resolved_params)
        
        # Store outputs - if no outputs, this is a void function that modifies state
        # Single output - store result directly
        state["similar_workorders"] = result
        
        
        print(f"[Completed] vector_search")
        return state
        
    def _node_enrich_results(self, state: GraphState) -> GraphState:
        """Node: enrich_results (function_call)"""
        print(f"[Executing] enrich_results (function_call)")
        
        # Function call node
        # Regular function call
        params = {"workorder_ids": "{{similar_workorders}}"}
        resolved_params = self._resolve_params(params, state)
        result = self.mock_lib.call_function("MxFetchWorkOrderDetails", resolved_params)
        
        # Store outputs - if no outputs, this is a void function that modifies state
        state["enriched_results"] = result
        
        
        print(f"[Completed] enrich_results")
        return state
        
    def _node_summarize_findings(self, state: GraphState) -> GraphState:
        """Node: summarize_findings (llm_call)"""
        print(f"[Executing] summarize_findings (llm_call)")
        
        # LLM call node
        prompt_template = """You found these similar work orders for: "{{workorder_description}}"

Similar Work Orders:
{{enriched_results}}

Provide:
1. Summary of common issues
2. Solutions that worked
3. Parts commonly needed
4. Estimated resolution time
"""
        prompt = self._resolve_template(prompt_template, state)
        
        config = {
            "model": "claude-sonnet-4-5",
            "temperature": 0.3
        }
        
        result = self.mock_lib.llm_call(prompt, config)
        
        state["summarized_findings"] = result
        
        
        print(f"[Completed] summarize_findings")
        return state
        
    def _node_display_results(self, state: GraphState) -> GraphState:
        """Node: display_results (visualizer)"""
        print(f"[Executing] display_results (visualizer)")
        
        # Visualizer node
        template = {'title': 'Similar Work Orders', 'sections': [{'type': 'summary', 'data': '{{summarized_findings}}'}, {'type': 'list', 'data': '{{enriched_results}}'}]}
        import json
        template_str = json.dumps(template)
        resolved_str = self._resolve_template(template_str, state)
        resolved_template = json.loads(resolved_str)
        
        visualization_data = {
            "component_type": "card",
            "template": template,
            "resolved_template": resolved_template
        }
        
        result = self.mock_lib.visualize(visualization_data)
        state["display_results_visualization"] = result
        
        
        print(f"[Completed] display_results")
        return state
        
        
    def _resolve_template(self, template: str, state: GraphState) -> str:
        """Resolve  placeholders safely inside JSON templates."""
        import re, json

        pattern = r'\{\{(\w+)\}\}'

        def replacer(match):
            var_name = match.group(1)
            value = state.get(var_name)
            if value is None:
                raise ValueError(
                    f"Variable '{var_name}' not found in state. Available: {list(state.keys())}"
                )
            
            # === START FIX: Robust JSON value escaping ===
            # 1. Convert value to its string representation
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (int, float, bool)):
                value_str = json.dumps(value) # Handles true/false/123
            else:
                value_str = str(value)

            # 2. Escape that string representation so it can be safely
            #   injected *inside* the template's JSON quotes
            safe_str = value_str.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
            return safe_str
            # === END FIX ===

        return re.sub(pattern, replacer, template)


        

    def _resolve_param_variable(self, template_str: str, state: Dict[str, Any]) -> Any:
        """
        Resolves a '{{var}}' string to its corresponding value in state.
        This returns the *actual object* (list, dict, str), not a string-escaped version.
        """
        import re
        # Simple match for '{{var_name}}'
        match = re.fullmatch(r'\{\{(\w+)\}\}', template_str)
        
        if not match:
            # Handle complex f-strings like "Error on {{asset}}"
            pattern = r'\{\{(\w+)\}\}'
            
            def replacer(match):
                var_name = match.group(1)
                value = state.get(var_name)
                if value is None:
                    raise ValueError(f"Variable '{var_name}' not found in state. Available: {list(state.keys())}")
                return str(value)
                
            return re.sub(pattern, replacer, template_str)

        # Pure '{{var_name}}' match, return the raw object
        var_name = match.group(1)
        if var_name not in state:
             raise ValueError(f"Variable '{var_name}' not found in state. Available: {list(state.keys())}")
        return state[var_name]

    def _resolve_params(self, params: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve all {{variable}} references in a params dict."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and '{{' in value:
                # === START FIX: Use the correct resolver ===
                # Use the new helper that returns the raw object, not the JSON-escaped string
                 resolved[key] = self._resolve_param_variable(value, state)
                # === END FIX ===
            elif isinstance(value, list):
                resolved[key] = [
                    # === START FIX: Use the correct resolver ===
                     self._resolve_param_variable(item, state) if isinstance(item, str) and '{{' in item else item
                    # === END FIX ===
                    for item in value
                ]
            else:
                resolved[key] = value
        return resolved
        
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow."""
        required_inputs = ['workorder_description']
        for req in required_inputs:
            if req not in inputs:
                raise ValueError(f"Missing required input: {req}")
        
        initial_state: GraphState = {}
        for param in inputs:
            initial_state[param] = inputs[param]
        
        final_state = self.graph.invoke(initial_state)
        return final_state


def main():
    """Example execution."""
    workflow = WorkorderSimilaritySearchWorkflow()
        
    inputs = {
        "workorder_description": "example_workorder_description",
        "limit": 10,
    }
        
    print("Starting workflow execution...")
    print(f"Inputs: {inputs}")
    print("-" * 60)
        
    result = workflow.execute(inputs)
        
    print("-" * 60)
    print("Workflow completed!")
    print(f"Final state: {result}")


if __name__ == "__main__":
    main()