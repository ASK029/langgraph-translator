"""YAML parser for Skill files."""

import yaml
from pathlib import Path
from typing import Union
from .models.skill import SkillYAML


class SkillParser:
    """Parse and validate Skill YAML files."""
    
    def __init__(self):
        self.parsed_skill = None
    
    def parse_file(self, filepath: Union[str, Path]) -> SkillYAML:
        """
        Parse a YAML file and validate against Skill schema.
        
        Args:
            filepath: Path to YAML file
            
        Returns:
            Validated SkillYAML object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is malformed
            ValidationError: If YAML doesn't match schema
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)
        
        return self.parse_dict(raw_data)
    
    def parse_dict(self, data: dict) -> SkillYAML:
        """
        Parse a dictionary and validate against Skill schema.
        
        Args:
            data: Dictionary containing skill definition
            
        Returns:
            Validated SkillYAML object
            
        Raises:
            ValidationError: If data doesn't match schema
        """
        self.parsed_skill = SkillYAML(**data)
        return self.parsed_skill
    
    def parse_string(self, yaml_string: str) -> SkillYAML:
        """
        Parse a YAML string and validate against Skill schema.
        
        Args:
            yaml_string: YAML content as string
            
        Returns:
            Validated SkillYAML object
            
        Raises:
            yaml.YAMLError: If YAML is malformed
            ValidationError: If YAML doesn't match schema
        """
        raw_data = yaml.safe_load(yaml_string)
        return self.parse_dict(raw_data)


def parse_skill_yaml(filepath: Union[str, Path]) -> SkillYAML:
    """
    Convenience function to parse a Skill YAML file.
    
    Args:
        filepath: Path to YAML file
        
    Returns:
        Validated SkillYAML object
    """
    parser = SkillParser()
    return parser.parse_file(filepath)