# OmniJournal: A Multimodal Automated Personal Ethnography Agent

## Abstract
OmniJournal is a local-first, privacy-preserving personal analytics tool designed to automate the process of journaling and self-quantification. By leveraging Large Language Models (LLM) and Vision Language Models (VLM), the agent autonomously perceives user activity through screen context, system signals, and visual "harvesting." It differentiates between active work (coding, writing) and passive consumption (video learning), compiling a structured narrative of the user's day without manual input.

## Features

* **Multimodal Perception**: Uses `Llava` (VLM) to perform OCR and semantic analysis on screen content, allowing it to understand *what* is being read or coded, not just *which* app is open.
* **Context-Aware Logic**: Distinguishes between deep work (coding/writing) and passive learning (watching tutorials) using a heuristic state machine.
* **Privacy by Design**: All data processing (screen capture, log storage, AI inference) occurs locally on the device using `Ollama`. No data is sent to the cloud.
* **Automated Summarization**: At the end of the day, an LLM (`Llama3`) synthesizes raw logs into a structured markdown journal, highlighting technical progress and knowledge acquisition.
* **System Telemetry**: Tracks physical location (via Wi-Fi SSID), power state, and user presence (HID idle time).

## Prerequisites

* **Operating System**: macOS (Relies on AppleScript and IOREG for sensor data).
* **Python**: 3.8+.
* **Ollama**: Installed and running locally.

### Required Models
You must pull the following models via Ollama before running the agent:
```bash
ollama pull llama3   # For summarization
ollama pull llava    # For visual analysis (VLM)