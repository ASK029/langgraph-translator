"""Code generator for LangGraph workflows."""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models.skill import SkillYAML, NodeModel
from .validator import WorkflowValidator


class CodeGenerator:
    """Generate executable Python code from Skill YAML."""
    
    def __init__(self, skill: SkillYAML, output_dir: Path):
        self.skill = skill
        self.output_dir = Path(output_dir)
        self.validator = WorkflowValidator(skill)

        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate(self) -> Dict[str, Path]:
        """
        Generate all files for the workflow.
        
        Returns:
            Dictionary mapping file types to their paths
        """
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🔨 Output directory: {self.output_dir}")
        # Generate files
        generated_files = {}
        generated_files['graph'] = self._generate_graph_py()
        print(f"\n🔨 Output directory: 111")
        generated_files['mocks'] = self._generate_mock_functions()
        generated_files['manifest'] = self._generate_manifest()
        generated_files['readme'] = self._generate_readme()
        
        
        print(f"\n✓ Generated project in: {self.output_dir}")
        print(f"  - graph.py: {generated_files['graph']}")
        print(f"  - mock_functions.py: {generated_files['mocks']}")
        print(f"  - manifest.json: {generated_files['manifest']}")
        print(f"  - README.md: {generated_files['readme']}")
        
        return generated_files
    
    def _generate_graph_py(self) -> Path:
        """Generate the main graph.py file."""
        template = self.jinja_env.get_template('graph_template.py.jinja2')
        # Get topological order
        node_order = self.validator.get_topological_order()
        ordered_nodes = [
            self._prepare_node_data(self.validator.nodes[nid]) 
            for nid in node_order
        ]

        # Find start and end nodes
        target_nodes = {e.target_node for e in self.skill.skill.workflow.edges}
        source_nodes = {e.source_node for e in self.skill.skill.workflow.edges}
        start_nodes = [n.id for n in self.skill.skill.workflow.nodes if n.id not in target_nodes]
        end_nodes = [n.id for n in self.skill.skill.workflow.nodes if n.id not in source_nodes]
        
        # Prepare template context
        context = {
            'skill_name': self.skill.skill.metadata.name,
            'skill_id': self.skill.skill.metadata.id,
            'description': self.skill.skill.metadata.description,
            'class_name': self._get_class_name(),
            'timestamp': datetime.now().isoformat(),
            'nodes': ordered_nodes,
            'edges': [{'source': e.source_node, 'target': e.target_node} for e in self.skill.skill.workflow.edges],
            'start_node': start_nodes[0] if start_nodes else (ordered_nodes[0]['id'] if ordered_nodes else None),
            'end_node': end_nodes[0] if end_nodes else (ordered_nodes[-1]['id'] if ordered_nodes else None),
            'required_inputs': [
                p.name for p in self.skill.skill.inputs.parameters if p.required
            ],
            'input_params': self._prepare_input_params()
        }
        
        print(f"\n🔨 Output directory:{(context)}")
        
        # Render template
        code = template.render(**context)
        
        # Write to file
        output_file = self.output_dir / "graph.py"
        output_file.write_text(code, encoding='utf-8')
        
        return output_file
    
    def _generate_mock_functions(self) -> Path:
        """Generate mock_functions.py with deterministic mocks."""
        template = self.jinja_env.get_template('mock_lib_template.py.jinja2')
        
        # Extract unique function names
        function_names = self._extract_function_names()
        
        context = {
            'skill_name': self.skill.skill.metadata.name,
            'timestamp': datetime.now().isoformat(),
            'function_names': sorted(function_names)
        }
        
        code = template.render(**context)
        
        output_file = self.output_dir / "mock_functions.py"
        output_file.write_text(code, encoding='utf-8')
        
        return output_file
    
    def _generate_manifest(self) -> Path:
        """Generate manifest.json with metadata and hashes."""
        # Calculate hash of input YAML
        yaml_hash = self._calculate_yaml_hash()
        
        manifest = {
            "skill_id": self.skill.skill.metadata.id,
            "skill_name": self.skill.skill.metadata.name,
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "generator_version": "0.1.0",
            "input_hash": yaml_hash,
            "metadata": {
                "description": self.skill.skill.metadata.description,
                "category": self.skill.skill.metadata.category,
                "tags": self.skill.skill.metadata.tags
            },
            "workflow": {
                "node_count": len(self.skill.skill.workflow.nodes),
                "edge_count": len(self.skill.skill.workflow.edges),
                "execution_order": self.validator.get_topological_order()
            }
        }
        
        output_file = self.output_dir / "manifest.json"
        output_file.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding='utf-8'
        )
        
        return output_file
    
    def _generate_readme(self) -> Path:
        """Generate README.md for the project."""
        readme_content = f"""# {self.skill.skill.metadata.name}

{self.skill.skill.metadata.description}

## Overview

**Skill ID**: `{self.skill.skill.metadata.id}`  
**Category**: {self.skill.skill.metadata.category}  
**Tags**: {', '.join(self.skill.skill.metadata.tags)}

## Generated Files

- `graph.py` - Main workflow execution logic
- `mock_functions.py` - Mock implementations for all function calls
- `manifest.json` - Project metadata and generation info

## Usage

```python
from graph import {self._get_class_name()}

# Initialize workflow
workflow = {self._get_class_name()}()

# Prepare inputs
inputs = {{
{self._format_input_example()}
}}

# Execute
result = workflow.execute(inputs)
print(result)
```

## Workflow Nodes

{self._format_node_list()}

## Execution Order

The nodes are executed in this topological order:

{self._format_execution_order()}

## Triggers

This skill can be triggered by the following keywords:
{self._format_triggers()}

---

*Auto-generated by langgraph-translator v0.1.0*
"""
        
        output_file = self.output_dir / "README.md"
        output_file.write_text(readme_content, encoding='utf-8')
        
        return output_file
    
    def _prepare_node_data(self, node: NodeModel) -> Dict:
        """Prepare node data for template rendering."""
        # Infer output name if no outputs declared
        inferred_output = None
        if not node.outputs:
            inferred_output = self.validator._infer_output_name(node.id)
        
        return {
            'id': node.id,
            'type': node.type,
            'config': node.config.model_dump(exclude_none=True),
            'outputs': [o.model_dump() for o in (node.outputs or [])],
            'inferred_output': inferred_output
        }
    
    def _prepare_input_params(self) -> List[Dict]:
        """Prepare input parameters with example values."""
        params = []
        for param in self.skill.skill.inputs.parameters:
            example_value = param.default
            if example_value is None:
                # Generate example based on type
                if param.type == 'string':
                    example_value = f"example_{param.name}"
                elif param.type == 'integer':
                    example_value = 10
                elif param.type == 'boolean':
                    example_value = True
                else:
                    example_value = None
            
            params.append({
                'name': param.name,
                'type': param.type,
                'required': param.required,
                'example_value': example_value
            })
        
        return params
    
    def _extract_function_names(self) -> Set[str]:
        """Extract all unique function names from workflow."""
        functions = set()
        
        for node in self.skill.skill.workflow.nodes:
            if node.type == 'function_call':
                func_name = node.config.function_name
                # Skip API endpoints
                if func_name and not func_name.startswith('/api/'):
                    functions.add(func_name)
        
        return functions
    
    def _get_class_name(self) -> str:
        """Generate class name from skill ID."""
        # Convert snake_case to PascalCase
        parts = self.skill.skill.metadata.id.split('_')
        return ''.join(word.capitalize() for word in parts) + 'Workflow'
    
    def _calculate_yaml_hash(self) -> str:
        """Calculate deterministic hash of skill definition."""
        # Convert to sorted JSON for consistent hashing
        skill_dict = self.skill.model_dump()
        skill_json = json.dumps(skill_dict, sort_keys=True)
        return hashlib.sha256(skill_json.encode()).hexdigest()[:16]
    
    def _format_input_example(self) -> str:
        """Format input parameters as example code."""
        lines = []
        for param in self.skill.skill.inputs.parameters:
            example = param.default or f'"example_{param.name}"'
            if isinstance(example, str) and not example.startswith('"'):
                example = f'"{example}"'
            lines.append(f'    "{param.name}": {example}')
        return ',\n'.join(lines)
    
    def _format_node_list(self) -> str:
        """Format node list for README."""
        lines = []
        for i, node in enumerate(self.skill.skill.workflow.nodes, 1):
            lines.append(f"{i}. **{node.id}** ({node.type})")
        return '\n'.join(lines)
    
    def _format_execution_order(self) -> str:
        """Format execution order for README."""
        order = self.validator.get_topological_order()
        return '\n'.join(f"{i}. {node_id}" for i, node_id in enumerate(order, 1))
    
    def _format_triggers(self) -> str:
        """Format trigger keywords for README."""
        keywords = self.skill.skill.triggers.keywords
        return '\n'.join(f"- {kw}" for kw in keywords)


def generate_code(skill: SkillYAML, output_dir: Path) -> Dict[str, Path]:
    """
    Convenience function to generate code from a skill.
    
    Args:
        skill: Validated SkillYAML object
        output_dir: Directory to write generated files
        
    Returns:
        Dictionary of generated file paths
    """
    generator = CodeGenerator(skill, output_dir)
    print(f"\n🔨 Output directory: ")
    return generator.generate()