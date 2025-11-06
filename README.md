# LangGraph YAML Translator

A deterministic translator that converts Skill YAML files into executable LangGraph Python code.

## Features

* ✅ **Deterministic Code Generation** - Same YAML always produces identical code
* ✅ **Automatic Validation** - Validates workflow logic and variable dependencies
* ✅ **Mock Function Library** - Auto-generates deterministic mocks for all function calls
* ✅ **Topological Sorting** - Ensures correct execution order
* ✅ **CLI Interface** - Simple command-line tool for translation
* ✅ **Type Safety** - Full Pydantic validation of YAML structure

## Installation

```bash
# Clone the repository
git clone https://github.com/ASK029/langgraph-translator.git
cd langgraph-translator
```

## Quick Start

### 1. Validate a YAML file

```bash
python.exe src/cli.exe validate examples/workorder_similarity_search_r1.yaml
```

### 2. View YAML information

```bash
python.exe src/cli.exe info examples/workorder_similarity_search.yaml
```

### 3. Generate executable code

```bash
python.exe src/cli.exe translate examples/workorder_similarity_search.yaml
```

This creates a timestamped directory in `output/` with:

* `graph.py` - Executable workflow
* `mock_functions.py` - Mock implementations
* `manifest.json` - Generation metadata
* `README.md` - Usage documentation

### 4. Run the generated workflow

```bash
cd output/workorder_similarity_search_20251106_143022/
python graph.py
```

```## Variable References

Use `{{variable_name}}` to reference outputs from previous nodes or input parameters.

The validator ensures:

* All referenced variables exist
* Variables are available before use (respects workflow order)
* No circular dependencies

## CLI Commands

### `translate`

Generate executable code from YAML.

```bash
python.exe src/cli.exe translate <yaml_file> [OPTIONS]

Options:
  -o, --output PATH      Output directory (default: ./output/<skill_id>_<timestamp>)
  -v, --validate-only    Only validate, don't generate code
  -f, --force           Overwrite existing output directory
```
### `validate`

Validate YAML without generating code.

```bash
python.exe src/cli.exe validate <yaml_file>
```
### `info`

Display detailed information about a skill.

```bash
langgraph-translate info <yaml_file>
```
## Project Structure

```
langgraph-translator/
├── src/
│   ├── cli.py                    # CLI interface
│   ├── translator/
│   │   ├── parser.py            # YAML parsing
│   │   ├── validator.py         # Workflow validation
│   │   ├── generator.py         # Code generation
│   │   ├── models/
│   │   │   └── skill.py         # Pydantic models
│   │   └── templates/
│   │       ├── graph_template.py.jinja2
│   │       └── mock_lib_template.py.jinja2
│   └── mocks/
├── examples/
│   └── workorder_similarity_search.yaml
├── output/                       # Generated projects
├── tests/
├── pyproject.toml
└── README.md
```
```## How It Works

1. **Parse**: YAML is parsed and validated against Pydantic models
2. **Validate**: Workflow logic is checked for:
   * Valid node references
   * No circular dependencies
   * Correct variable usage
   * Required configurations
3. **Order**: Nodes are sorted topologically for deterministic execution
4. **Generate**: Jinja2 templates render:
   * `graph.py` with execution logic
   * `mock_functions.py` with deterministic mocks
   * Supporting files (manifest, README)

## Examples

See the `examples/` directory for sample YAML files.

## Future Enhancements

This is Version 0.0 focused on core translation. Future versions may include:

* FastAPI runtime server (SSE streaming)
* Save/restore execution state
* Multi-user session management
* Agent hub for skill composition
* User approval integration
* Real LLM/API integration
