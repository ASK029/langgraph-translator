"""Command-line interface for LangGraph translator."""

import click
import sys
from pathlib import Path
from datetime import datetime

from translator.parser import parse_skill_yaml
from translator.validator import validate_skill
from translator.generator import generate_code


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """LangGraph YAML to Python translator."""
    pass


@cli.command()
@click.argument('yaml_file', type=click.Path(exists=True))
@click.option(
    '--output', '-o',
    type=click.Path(),
    help='Output directory for generated files (default: ./output/<skill_id>)'
)
@click.option(
    '--validate-only', '-v',
    is_flag=True,
    help='Only validate YAML without generating code'
)
@click.option(
    '--force', '-f',
    is_flag=True,
    help='Overwrite existing output directory'
)
def translate(yaml_file, output, validate_only, force):
    """
    Translate a Skill YAML file to executable LangGraph code.
    
    Example:
        langgraph-translate translate examples/workorder_similarity_search.yaml
    """
    try:
        click.echo(f"📄 Reading YAML file: {yaml_file}")
        
        # Step 1: Parse YAML
        skill = parse_skill_yaml(yaml_file)
        click.echo(f"✓ Parsed skill: {skill.skill.metadata.name}")
        
        # Step 2: Validate workflow
        click.echo("\n🔍 Validating workflow...")
        is_valid, errors = validate_skill(skill)
        
        if not is_valid:
            click.echo("❌ Validation failed:", err=True)
            for error in errors:
                click.echo(f"  • {error}", err=True)
            sys.exit(1)
        
        click.echo("✓ Workflow is valid")
        click.echo(f"  - {len(skill.skill.workflow.nodes)} nodes")
        click.echo(f"  - {len(skill.skill.workflow.edges)} edges")
        
        if validate_only:
            click.echo("\n✓ Validation complete (no code generated)")
            return
        
        # Step 3: Determine output directory
        if output:
            output_dir = Path(output)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output") / f"{skill.skill.metadata.id}_{timestamp}"
        
        click.echo(f"\n🔨 Output directory: {output_dir}")
        
        # Check if output exists
        if output_dir.exists() and not force:
            click.echo(f"\n❌ Output directory already exists: {output_dir}", err=True)
            click.echo("   Use --force to overwrite", err=True)
            sys.exit(1)
        
        # Step 4: Generate code
        click.echo(f"\n🔨 Generating code...")
        generated_files = generate_code(skill, output_dir)
        
        click.echo("\n✅ Translation complete!")
        click.echo(f"\n📦 Generated files in: {output_dir}")
        click.echo(f"   • graph.py - Main workflow")
        click.echo(f"   • mock_functions.py - Mock implementations")
        click.echo(f"   • manifest.json - Project metadata")
        click.echo(f"   • README.md - Documentation")
        
        click.echo(f"\n🚀 To run the workflow:")
        click.echo(f"   cd {output_dir}")
        click.echo(f"   python graph.py")
        
    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        import traceback
        if click.get_current_context().obj.get('debug', False):
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('yaml_file', type=click.Path(exists=True))
def validate(yaml_file):
    """
    Validate a Skill YAML file without generating code.
    
    Example:
        langgraph-translate validate examples/workorder_similarity_search.yaml
    """
    ctx = click.get_current_context()
    ctx.invoke(translate, yaml_file=yaml_file, validate_only=True)


@cli.command()
@click.argument('yaml_file', type=click.Path(exists=True))
def info(yaml_file):
    """
    Display information about a Skill YAML file.
    
    Example:
        langgraph-translate info examples/workorder_similarity_search.yaml
    """
    try:
        skill = parse_skill_yaml(yaml_file)
        
        click.echo(f"\n{'='*60}")
        click.echo(f"Skill: {skill.skill.metadata.name}")
        click.echo(f"{'='*60}")
        
        click.echo(f"\n📋 Metadata:")
        click.echo(f"  ID: {skill.skill.metadata.id}")
        click.echo(f"  Category: {skill.skill.metadata.category}")
        click.echo(f"  Tags: {', '.join(skill.skill.metadata.tags)}")
        click.echo(f"  Description: {skill.skill.metadata.description}")
        
        click.echo(f"\n🎯 Triggers:")
        for kw in skill.skill.triggers.keywords:
            click.echo(f"  • {kw}")
        
        click.echo(f"\n📥 Input Parameters:")
        for param in skill.skill.inputs.parameters:
            required = "required" if param.required else "optional"
            default = f" (default: {param.default})" if param.default else ""
            click.echo(f"  • {param.name}: {param.type} [{required}]{default}")
        
        click.echo(f"\n🔄 Workflow:")
        click.echo(f"  Nodes: {len(skill.skill.workflow.nodes)}")
        for node in skill.skill.workflow.nodes:
            click.echo(f"    • {node.id} ({node.type})")
        
        click.echo(f"\n  Edges: {len(skill.skill.workflow.edges)}")
        for edge in skill.skill.workflow.edges:
            click.echo(f"    • {edge.source_node} → {edge.target_node}")
        
        # Validate and show execution order
        is_valid, errors = validate_skill(skill)
        if is_valid:
            from translator.validator import WorkflowValidator
            validator = WorkflowValidator(skill)
            order = validator.get_topological_order()
            
            click.echo(f"\n⚡ Execution Order:")
            for i, node_id in enumerate(order, 1):
                click.echo(f"    {i}. {node_id}")
        else:
            click.echo(f"\n⚠️  Validation Issues:")
            for error in errors:
                click.echo(f"    • {error}")
        
        click.echo(f"\n{'='*60}\n")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()