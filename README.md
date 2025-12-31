
# OmniJournal: A Multimodal Automated Personal Ethnography Agent

## Abstract
OmniJournal is a local-first, privacy-preserving personal analytics framework designed to automate the process of quantitative self-tracking and qualitative journaling. By leveraging Large Language Models (LLM) and Vision Language Models (VLM), the agent autonomously perceives user activity through a combination of screen context, system telemetry, and active visual "harvesting." It distinguishes between deep work (e.g., coding, academic reading) and passive consumption (e.g., video learning) using a context-aware state machine, compiling a structured, semantic narrative of the user's day without requiring manual input.

## Key Features

* **Multimodal Perception**: Utilizes `Llava` (VLM) to perform Optical Character Recognition (OCR) and semantic scene understanding. This allows the system to interpret *what* is being read, coded, or watched, rather than merely logging application names.
* **Context-Aware State Machine**: Implements a heuristic logic engine that differentiates between "Idle," "Active Work," and "Passive Consumption." It employs "sticky" states to maintain context during media playback even in the absence of HID (Human Interface Device) activity.
* **Privacy by Design**: All data processing—including screen capture analysis, log storage, and narrative generation—occurs locally on the device using `Ollama`. No user data is transmitted to external cloud servers.
* **Automated Ethnography**: At the end of a session, an LLM (`Llama3`) synthesizes raw JSONL telemetry into a structured Markdown journal, highlighting technical progress, knowledge acquisition, and temporal distribution.
* **System Telemetry**: integrated sensors track physical context (via Wi-Fi SSID), power states (AC/Battery), and user presence (HID idle time).

## System Architecture

The project is structured into four main modules:

1.  **Sensors (`src/utils.py`)**: Interfaces with macOS APIs (AppleScript, IOREG, PMSET) to retrieve window titles, idle time, and power assertions.
2.  **Perception (`src/analysis.py`)**: Manages interactions with local AI models. It includes a `WorkContextManager` for dynamic prompt engineering based on the active application.
3.  **Core Logic (`src/recorder.py`)**: The main event loop that orchestrates sampling frequencies and triggers the "Visual Harvester" based on context.
4.  **Logging (`src/utils.py`)**: Handles structured data persistence in JSON Lines format (`.jsonl`).

## Prerequisites

This framework is optimized for **macOS** (Apple Silicon recommended) due to specific dependencies on macOS automation APIs.

* **Operating System**: macOS 12.0+ (Monterey or newer).
* **Python**: Version 3.10 or higher.
* **Ollama**: A local LLM runner required for inference. [Download Ollama](https://ollama.com/).

## Installation

### 1. Environment Setup
It is recommended to use `Conda` to manage the environment and dependencies to avoid conflicts.

```bash
# Create a new conda environment
conda create -n omni_journal python=3.10
conda activate omni_journal

# Clone the repository
git clone [https://github.com/yourusername/OmniJournal.git](https://github.com/yourusername/OmniJournal.git)
cd OmniJournal

```

### 2. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt

```

### 3. Model Preparation

OmniJournal relies on specific local models. You must pull them via Ollama before running the agent.

* **Llama3 (8B)**: Used for daily summarization and narrative construction.
* **Llava (7B)**: Used for visual analysis. Note: `Llava` is preferred over lighter models like `moondream` for its superior OCR capabilities regarding academic text and code.

```bash
ollama pull llama3
ollama pull llava

```

### 4. Configuration

Open `config.py` to customize the agent's behavior:

* **MONITOR_PATH**: Set this to your primary working directory (e.g., your OneDrive, Research folder, or Code base) to enable file modification tracking.
* **VLM_MODEL**: Ensure this is set to `"llava"`.
* **Sampling Intervals**: Adjust `MEDIA_HARVEST_INTERVAL` and `WORK_PROGRESS_INTERVAL` based on your hardware capabilities.

## Usage

### Running the Agent

Ensure Ollama is running in the background, then execute the main script:

```bash
python main.py

```

### First-Run Permissions

Upon the first execution, macOS will request the following permissions for your terminal application (e.g., iTerm2, VS Code, or Terminal):

1. **Accessibility**: Required to read window titles.
2. **Screen Recording**: Required for the VLM to capture screen context.

*Note: You must grant these permissions and restart the terminal for the agent to function correctly.*

### Generating Summaries

The agent runs continuously in the background. To stop the recording and generate the daily report:

1. Press `Ctrl+C` in the terminal.
2. The agent will process the day's logs and generate a summary in `Downloads/OmniJournal_Data/`.

## Data Structure

The system generates two types of files in the configured log directory:

1. **Raw Logs (`YYYY-MM-DD.jsonl`)**:
Contains structured event data.
```json
{
  "timestamp": "2023-12-31 10:00:00",
  "type": "PROGRESS",
  "content": "Analyzed [VS Code] main.py: Implemented the VisualHarvester class...",
  "context": {"wifi": "Lab_Network", "category": "CODING"}
}

```


2. **Daily Summary (`Summary_YYYY-MM-DD.md`)**:
A human-readable, AI-synthesized report categorized into "Deep Work," "Knowledge Inputs," and "Timeline."

## Project Structure

```text
OmniJournal/
├── config.py           # User configuration and model settings
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
├── src/
│   ├── __init__.py
│   ├── analysis.py     # VLM/LLM interaction and context classification
│   ├── recorder.py     # Main event loop and state machine logic
│   └── utils.py        # System sensors, logging, and I/O handlers
└── README.md           # Project documentation
