# USDM Biomedical Concept Mapper

A Python tool for automatically mapping activities in USDM (Unified Study Data Model) files to CDISC biomedical concepts using AI-powered semantic search and LLM-based matching.

## What does this project do?

The [USDM Biomedical Concept Mapper](https://github.com/AI-LENS/usdm-bc-mapper) helps standardize clinical trial data by:

- **Automated Mapping**: Maps biomedical concepts from USDM files to standardized CDISC biomedical concepts
- **AI-Powered Search**: Uses Large Language Models (LLMs) to find the best matching CDISC concepts for given biomedical terms
- **CDISC Integration**: Works with the latest [CDISC biomedical concepts](https://github.com/cdisc-org/COSMoS/blob/main/export/cdisc_biomedical_concepts_latest.csv) and [SDTM dataset specializations](https://github.com/cdisc-org/COSMoS/blob/main/export/cdisc_sdtm_dataset_specializations_latest.csv)
- **Batch Processing**: Processes entire USDM study files and generates mapped outputs

### Key Features

- **CDISC Standards Compliance**: Uses official CDISC terminology including ADaM, CDASH, SDTM, SEND, and Protocol terminologies
- **Configurable AI Models**: Supports different [OpenAI-compatible models](https://github.com/AI-LENS/usdm-bc-mapper/blob/mapping/example.py)
- **Command Line Interface**: Easy-to-use CLI for batch processing and individual concept searches
- **Structured AI Output**: Structured output from LLMs using [OpenRouter](https://openrouter.ai/docs/features/structured-outputs) or [OpenAI](https://platform.openai.com/docs/guides/structured-outputs).

## Installation

### Prerequisites

- Python 3.13 or higher
- Access to [OpenRouter](https://openrouter.ai/models?q=openai)(recommended) or [OpenAI](https://platform.openai.com/docs/models)-compatible models .

### Install from source
```bash
pip install usdm-bc-mapper
```


### Install dependencies for development

## Run Locally

Clone the project

```bash
 git clone https://github.com/AI-LENS/usdm-bc-mapper.git
```

Go to the project directory

```bash
  cd usdm-bc-mapper
```

Install dependencies

```bash
  uv sync
```

Using pip:

```bash
pip install -e .
```

```bash
uv sync --group dev
```

## How to use the tools

### Configuration

Your Configuration folder structure should look like this:

```
usdm-bc-mapper/
└── dump/
    └── test/
        └──  config.yaml   # Configuration file

```

Before using the tool, you need to configure your settings. Create a YAML configuration file:
```yaml
# config.yaml
openrouter_api_key: "your-api-key"
openrouter_model: "openai/gpt-5" # or your preferred model
openrouter_base_url: "https://openrouter.ai/api/v1" 
openai_api_key: "your-api-key-here"
openai_model: "gpt-4"  # or your preferred model
openai_base_url: "https://api.openai.com/v1"  # or your custom endpoint


max_ai_lookup_attempts: "max retries for AI lookup"
data_search_cols:  # columns to search in CDISC data
  - "short_name"
  - "bc_categories" 
  - "synonyms"
  - "definition"
```

### Command Line Usage

The tool provides three main commands through the `bcm` CLI:

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

Find CDISC match for a specific biomedical concept using LLM:

```bash
bcm find-bc-cdisc "diabetes mellitus" --config config.yaml
```

#### 3. Search CDISC Biomedical Concepts

Search the local CDISC index for matching concepts:

```bash
bcm search-bc-cdisc "blood pressure" --config config.yaml
```

Search with custom number of results:
```bash
bcm search-bc-cdisc "blood pressure" --k 20 --config config.yaml
```

### Advanced Usage

#### Enable Debug Logging

Add the `--show-logs` flag to any command to see detailed processing information:

```bash
bcm usdm path/to/file.json --config config.yaml --show-logs
```

#### Configuration Options

Your Configuration folder structure should look like this:

```
usdm-bc-mapper/
└── dump/
    └── test/
        └──  config.yaml   # Configuration file

```


The following settings can be configured in your YAML config file:

```yaml
# AI Model Configuration
openrouter_api_key: "your-api-key"
openrouter_model: "openai/gpt-5" # or your preferred model
openrouter_base_url: "https://openrouter.ai/api/v1" 
openai_api_key: "your-api-key"
openai_model: "gpt-4"  # Model to use
openai_base_url: "https://api.openai.com/v1"  # API endpoint

# Search Configuration
max_ai_lookup_attempts: 7  # Max retries for AI lookup
data_search_cols:  # Columns to search in CDISC data
  - "short_name"
  - "bc_categories" 
  - "synonyms"
  - "definition"
```

### Example Workflow

* **Prepare your USDM file**: Ensure you have a valid USDM JSON file containing biomedical concepts
* **Configure API access**: Set up your config.yaml with API credentials
* **Run the mapper**: 
   ```bash
   bcm usdm my_study.json --config config.yaml --output mapped_study.json
   ```
* **Review results**: The output file will contain the original USDM data with mapped CDISC biomedical concepts

### Example Output

The tool outputs detailed mapping results including:
- Original biomedical concept information
- Matched CDISC concept details
- Confidence scores and reasoning
- Structured JSON format for further processing

## Development

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

## License

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg) 

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For questions or issues, please open an issue on the GitHub repository.
