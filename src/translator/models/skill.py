"""Pydantic models for Skill YAML validation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class MetadataModel(BaseModel):
    """Skill metadata."""
    id: str
    name: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)


class TriggerModel(BaseModel):
    """Skill trigger configuration."""
    keywords: List[str] = Field(default_factory=list)


class ParameterModel(BaseModel):
    """Input parameter definition."""
    name: str
    type: str
    required: bool = True
    default: Optional[Any] = None


class InputsModel(BaseModel):
    """Skill inputs configuration."""
    parameters: List[ParameterModel]


class NodeOutputModel(BaseModel):
    """Output definition for a node."""
    name: str
    type: str  # array, object, string, etc.


class NodeConfigModel(BaseModel):
    """Configuration for different node types."""
    # For function_call nodes
    function_name: Optional[str] = None
    function_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # For llm_call nodes
    model: Optional[str] = None
    prompt_template: Optional[str] = None
    temperature: Optional[float] = None
    
    # For visualizer nodes
    component_type: Optional[str] = None
    template: Optional[Dict[str, Any]] = None


class NodeModel(BaseModel):
    """Workflow node definition."""
    id: str
    type: str  # function_call, llm_call, visualizer, user_approval
    config: NodeConfigModel
    outputs: Optional[List[NodeOutputModel]] = Field(default_factory=list)
    
    @field_validator('type')
    @classmethod
    def validate_node_type(cls, v):
        valid_types = ['function_call', 'llm_call', 'visualizer', 'user_approval']
        if v not in valid_types:
            raise ValueError(f"Node type must be one of {valid_types}, got '{v}'")
        return v


class EdgeModel(BaseModel):
    """Workflow edge connecting nodes."""
    source_node: str
    target_node: str


class WorkflowModel(BaseModel):
    """Workflow definition with nodes and edges."""
    nodes: List[NodeModel]
    edges: List[EdgeModel]


class SkillModel(BaseModel):
    """Complete skill definition."""
    metadata: MetadataModel
    triggers: TriggerModel
    inputs: InputsModel
    workflow: WorkflowModel


class SkillYAML(BaseModel):
    """Root YAML structure."""
    skill: SkillModel