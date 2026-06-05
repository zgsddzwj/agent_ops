# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🚀 Added

- **Project Structure**: Comprehensive directory reorganization with clear separation of concerns
- **Documentation**: Enhanced README with badges, better structure, and comprehensive guides
- **Contributing Guide**: Detailed CONTRIBUTING.md with development setup and contribution guidelines
- **Changelog**: This CHANGELOG.md file for tracking project evolution
- **Issue Templates**: Standardized templates for bug reports and feature requests
- **Pull Request Template**: Standardized template for better PR descriptions

### 🔄 Changed

- **README.md**: Completely redesigned with modern layout, badges, and improved readability
- **Project Description**: More concise and focused value proposition
- **Documentation Structure**: Organized into logical sections with better navigation
- **Code Organization**: Better separation between SDK, CLI, backend, and frontend

### ⚡ Improved

- **Documentation Quality**: More comprehensive installation and usage instructions
- **Project Navigation**: Better structured directories and file organization
- **Onboarding Experience**: Clearer getting started guide for new contributors
- **Code Discoverability**: Better organized codebase structure

## [0.1.0] - 2026-06-05

### 🚀 Added

#### Core Platform
- **AgentOps Platform**: Complete MLOps platform for LangChain/LangGraph agents
- **Multi-project Management**: Support for registering and managing multiple AI projects
- **Unified Dashboard**: Next.js-based web interface for monitoring and management

#### SDK & Instrumentation
- **Python SDK** (`packages/agent-ops-sdk`): LangChain callback handlers for tracing
- **LangChain Integration**: Automatic collection of LLM/Tool/Chain traces
- **Security Pipeline**: Runtime security checks and PII protection
- **Cost Tracking**: Token usage and cost estimation for various LLM providers

#### CLI Tools
- **Command-line Interface** (`packages/agent-ops-cli`): Comprehensive CLI tools
- **Project Management**: `init`, `link`, `check` commands for project lifecycle
- **Evaluation Framework**: `eval run` for running smoke and regression tests
- **Security Scanning**: `security scan` for prompt injection and jailbreak detection
- **Benchmarking**: `benchmark run` for multi-model performance comparison

#### Backend Services
- **FastAPI Backend** (`backend/`): High-performance async API server
- **Database Models**: Complete SQLAlchemy ORM with PostgreSQL support
- **API Endpoints**: RESTful API for traces, metrics, evaluations, and security
- **Authentication**: API key-based project authentication
- **Data Ingestion**: High-throughput trace collection and processing

#### Task Processing
- **ARQ Worker** (`worker/`): Async task processing with Redis queue
- **Background Jobs**: Offline processing for evaluations and benchmarks
- **Data Aggregation**: Metric computation and time-series aggregation

#### Frontend Dashboard
- **Next.js 14 Web App** (`web/`): Modern React-based dashboard
- **Visualization**: Charts and graphs for metrics and performance data
- **Real-time Monitoring**: Live updates of agent performance
- **Multi-view Interface**: Dedicated pages for traces, evals, benchmarks, security

#### Data Management
- **PostgreSQL Schema**: Complete database schema for all entities
- **Alembic Migrations**: Database migration management
- **Model Pricing**: Comprehensive LLM provider cost database
- **Metric Aggregation**: Efficient time-series data storage

#### Security & Safety
- **Security Scanning**: Automated security testing capabilities
- **Vulnerability Detection**: Prompt injection and jailbreak detection
- **Safety Policies**: Configurable security rules and thresholds
- **Event Logging**: Security incident tracking and alerting

#### Testing & Quality
- **Test Suite**: Basic test structure and example tests
- **Security Tests**: Security scanner tests and validation
- **SDK Tests**: Client integration tests

#### Infrastructure
- **Docker Configuration**: Complete Docker setup for all services
- **Docker Compose**: Easy development and deployment setup
- **Environment Config**: Comprehensive environment variable management

#### Evaluation Framework
- **Built-in Datasets**: Example evaluation datasets for common use cases
- **Suite Configuration**: Predefined test suites (smoke, regression)
- **Result Analysis**: Comprehensive evaluation result processing

#### Benchmarking System
- **Model Comparison**: Multi-LLM performance benchmarking
- **Preset Configurations**: Various model preset combinations
- **Performance Metrics**: TTFT, latency, cost, quality measurements

#### Alerting System
- **Alert Rules**: Configurable alert conditions and thresholds
- **Webhook Integration**: External notification system
- **Event Management**: Alert event tracking and acknowledgment

### 🔄 Changed

- **Project Structure**: Organized as a Python workspace with uv package management
- **Architecture**: Microservices-style architecture with clear separation of concerns
- **Database Design**: Normalized database schema with proper relationships
- **API Design**: RESTful API with consistent naming and pagination

### ⚡ Improved

- **Performance**: Asynchronous backend architecture for high throughput
- **Scalability**: Docker-based deployment for easy scaling
- **Developer Experience**: Comprehensive tooling and CLI support
- **User Experience**: Intuitive web dashboard with real-time updates
- **Security**: Built-in security scanning and runtime protection

### 📝 Documentation

- **README.md**: Comprehensive project documentation with quick start guide
- **API Documentation**: Complete API endpoint reference
- **Integration Guides**: Step-by-step SDK integration instructions
- **CLI Reference**: Complete command-line interface documentation
- **Architecture Overview**: System design and component descriptions

### 🛠️ Technical Details

#### Suported Models
- OpenAI (GPT-4o, GPT-4o-mini)
- Qwen (Qwen-plus, Qwen-turbo, Qwen-max)
- DeepSeek (DeepSeek-chat, DeepSeek-reasoner)
- Anthropic (Claude Sonnet)

#### Preset Benchmarks
- `domestic`: Qwen family models
- `international`: Western LLM providers  
- `sota`: State-of-the-art models
- `cost_efficient`: Budget-friendly options

#### Security Scanning
- Prompt injection detection
- Jailbreak attempt prevention
- Data exfiltration protection
- PII detection and masking

#### Performance Metrics
- Time-to-first-token (TTFT)
- End-to-end latency
- Token consumption and cost
- Error rates and success rates
- P50/P95 latency distributions

---

## Types of Changes

- `🚀 Added` for new features
- `🔄 Changed` for changes in existing functionality
- `🗑️ Deprecated` for soon-to-be removed features
- `❌ Removed` for now removed features
- `🐛 Fixed` for any bug fixes
- `🛡️ Security` in case of vulnerabilities
- `⚡ Improved` for performance or quality improvements
- `📝 Documentation` for documentation updates
- `🚧 Work in Progress` for ongoing development

## Versioning Rules

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes