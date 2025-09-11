# USDM Biomedical Concept Mapper

![License: MIT](https://img.shields.io/github/license/AI-LENS/usdm-bc-mapper)
![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)

A Python tool for automatically mapping activities in USDM (Unified Study Data Model) files to CDISC biomedical concepts using AI-powered semantic search and LLM-based matching.

## Table of Contents

- [What does this project do?](#what-does-this-project-do)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Command Line Usage](#command-line-usage)
- [Advanced Usage](#advanced-usage)
- [Output Examples](#output-examples)
- [Development](#development)
- [License](#license)
- [Contributing](#contributing)
- [Support](#support)

## What does this project do?

The [USDM Biomedical Concept Mapper](https://github.com/AI-LENS/usdm-bc-mapper) helps identify biomedical concepts for activities in USDM files:

- **Automated Mapping**: Maps activities from USDM files to standardized biomedical concepts
- **AI-Powered Search**: Uses Large Language Models (LLMs) to find the best matching CDISC concepts for given activities
- **CDISC Integration**: Utilizes the latest [CDISC biomedical concepts](https://github.com/cdisc-org/COSMoS/blob/main/export/cdisc_biomedical_concepts_latest.csv) and [SDTM dataset specializations](https://github.com/cdisc-org/COSMoS/blob/main/export/cdisc_sdtm_dataset_specializations_latest.csv)
- **Batch Processing**: Processes entire USDM study files and generates mapped outputs

### Key Features

- **Multiple Search Methods**: Supports both LLM-powered exact matching and local index searching
- **Configurable AI Models**: Supports different commercial or open-source LLMs
- **Command Line Interface**: Easy-to-use CLI for batch processing and individual concept searches

## Installation

### Prerequisites

- Python 3.13 or higher
- Access to LLM (commercial or open-source)

### Install from PyPI

```bash
pip install usdm-bc-mapper
```

## Quick Start

1. **Install the package**:

   ```bash
   pip install usdm-bc-mapper
   ```

2. **Create a config file** (`config.yaml`) in your working directory:

   ```yaml
   llm_api_key: "your-api-key-here"
   llm_model: "gpt-5-mini"
   ```

3. **Run the mapper** on your USDM file:

   ```bash
   bcm usdm your_study.json
   ```

4. **Get help** with any command:
   ```bash
   bcm --help
   bcm usdm --help
   ```

## How to use the tools

### Configuration

Before using the tool, you need to configure your settings. Create a `config.yaml` file in your working directory (the same directory where your USDM JSON file is located):

```yaml
# config.yaml
llm_api_key: "your-api-key-here"
llm_model: "gpt-5-mini" # or your preferred model

# Optional Configurations
llm_base_url: "https://api.openai.com/v1" # or your custom endpoint
max_ai_lookup_attempts: 7 # max retries for AI lookup
data_path: "path/to/cdisc/data" # path to CDISC data files and system prompt for LLMs
data_search_cols: # columns to search in CDISC data
  - "short_name"
  - "bc_categories"
  - "synonyms"
  - "definition"
```

### Command Line Usage

The tool provides three main commands through the `bcm` CLI. Use `bcm --help` or `bcm <command> --help` to see detailed documentation for each command.

#### 1. Map USDM File Biomedical Concepts

Map all biomedical concepts in a USDM file to CDISC standards:

```bash
bcm usdm path/to/your/usdm_file.json --config config.yaml
```

With custom output file:

```bash
bcm usdm path/to/your/usdm_file.json --output mapped_results.json --config config.yaml
```

#### 2. Find Individual Biomedical Concept

Find CDISC match for a specific biomedical concept using LLM (provides exact matching):

```bash
bcm find-bc-cdisc "diabetes mellitus" --config config.yaml
```

#### 3. Search CDISC Biomedical Concepts

Search the local CDISC index for matching concepts (searches local index without LLM):

```bash
bcm search-bc-cdisc "blood pressure" --config config.yaml
```

Search with custom number of results:

```bash
bcm search-bc-cdisc "blood pressure" --k 20 --config config.yaml
```

**Note**: The main difference between `find-bc-cdisc` and `search-bc-cdisc` is that `find-bc-cdisc` uses an LLM to find exact matches, while `search-bc-cdisc` looks for matches in the local index.

### Advanced Usage

#### Enable Debug Logging

Add the `--show-logs` flag to any command to see detailed processing information:

```bash
bcm usdm path/to/file.json --config config.yaml --show-logs
```

### Output Examples

#### USDM Mapping Output

When using `bcm usdm`, the tool outputs the original USDM data with mapped CDISC biomedical concepts, including confidence scores and reasoning in structured JSON format.

#### Individual Concept Search Output

When using `bcm find-bc-cdisc` or `bcm search-bc-cdisc`, the tool returns matched CDISC concept details with relevance scores.

## Development

### Development Setup

Clone the project:

```bash
git clone https://github.com/AI-LENS/usdm-bc-mapper.git
```

Go to the project directory:

```bash
cd usdm-bc-mapper
```

Install dependencies:

```bash
uv sync --group dev
```

### Running Tests

```bash
pytest
```

### Pre-commit Hooks

Install pre-commit hooks for code quality:

```bash
pre-commit install
pre-commit run --all-files
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For questions or issues, please open an issue on the GitHub repository.
