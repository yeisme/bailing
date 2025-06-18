# Bailing (百聆)

[ [中文](README.md) | English ]

**Bailing** is an open-source voice dialogue assistant designed to engage in natural conversations with users through voice interaction. This project combines Automatic Speech Recognition (ASR), Voice Activity Detection (VAD), Large Language Model (LLM), and Text-to-Speech (TTS) technologies. It's a voice dialogue robot similar to GPT-4o, implemented through ASR+LLM+TTS, providing high-quality voice conversation experience with end-to-end latency of 800ms. Bailing aims to achieve GPT-4o-like conversation effects without requiring GPU, making it suitable for various edge devices and low-resource environments.

![logo](assets/logo.png)

## Key Features

- 🚀 **Smooth Conversation Experience**: Low latency, no stuttering, almost as natural as human conversation. Bailing uses multiple open-source models to ensure efficient and reliable voice dialogue experience.
- 🖥 **Lightweight Deployment**: No need for high-end hardware or even GPU. Through optimization, it can be deployed locally while still providing GPT-4-like performance.
- 🔧 **Modular Design**: ASR, VAD, LLM, and TTS modules are independent of each other and can be replaced and upgraded according to needs.
- 🧠 **Intelligent Memory Function**: With continuous learning capability, it can remember user preferences and conversation history, providing personalized interactive experience.
- 🛠 **Tool Calling Capability**: Flexible integration of external tools, users can directly request information or execute operations through voice, enhancing the assistant's practicality.
- 📅 **Task Management**: Efficiently manage user tasks, track progress, set reminders, and provide dynamic updates to ensure users don't miss any important matters.

## Thanks to the Open Source Community

The birth of Bailing is inseparable from the selfless contributions of the open source community.

Thanks to excellent open source projects like DeepSeek, FunASR, Silero-VAD, ChatTTS, OpenManus, etc.,  
which give us the opportunity to create a truly open, powerful, and low-threshold voice AI assistant!

If you also agree with the concept of "making AI accessible to everyone", welcome to contribute code, optimize models,
and make Bailing stronger and smarter, becoming a true JARVIS!

📢 Welcome Star & PR

## Project Overview

Bailing implements voice dialogue functionality through the following technical components:

- 🎙 **ASR**: Uses [FunASR](https://github.com/modelscope/FunASR) for automatic speech recognition, converting user voice to text.
- 🎚 **VAD**: Uses [silero-vad](https://github.com/snakers4/silero-vad) for voice activity detection to ensure only valid voice segments are processed.
- 🧠 **LLM**: Uses [deepseek](https://github.com/deepseek-ai/DeepSeek-LLM) as the large language model to process user input and generate responses, extremely cost-effective.
- 🔊 **TTS**: Uses [edge-tts](https://github.com/rany2/edge-tts), [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), [ChatTTS](https://github.com/2noise/ChatTTS), MacOS say for text-to-speech conversion, converting generated text responses into natural and fluent speech.

## Framework Description

![Bailing Flowchart](assets/bailing_flowchart_a.png)

Robot is responsible for efficient task management and memory management, intelligently handling user interruption requests while achieving seamless coordination and connection between various modules to ensure smooth interactive experience.

| Player Status | Speaking | Description |
|---------------|----------|-------------|
| Playing | Not Speaking | Normal |
| Playing | Speaking | Interruption Scenario |
| Not Playing | Not Speaking | Normal |
| Not Playing | Speaking | VAD Detection, ASR Recognition |

## Demo

![Demo](assets/example.png)

[bailing audio dialogue](https://www.zhihu.com/zvideo/1818998325594177537)

[bailing audio dialogue](https://www.zhihu.com/zvideo/1818994917940260865)

## Features

- **Voice Input**: Accurate speech recognition through FunASR.
- **Voice Activity Detection**: Uses silero-vad to filter invalid audio and improve recognition efficiency.
- **Intelligent Dialogue Generation**: Relies on DeepSeek's powerful language understanding capability to generate natural text replies, extremely cost-effective.
- **Voice Output**: Converts text to speech through edge-tts and Kokoro-82M, providing users with realistic auditory feedback.
- **Interruption Support**: Flexible interruption strategy configuration, capable of recognizing keywords and voice interruptions, ensuring immediate feedback and control for users during conversations, improving interaction fluency.
- **Memory Function Support**: With continuous learning capability, can remember user preferences and conversation history, providing personalized interactive experience.
- **Tool Calling Support**: Flexible integration of external tools, users can directly request information or execute operations through voice, enhancing assistant practicality.
- **Task Management Support**: Efficiently manage user tasks, track progress, set reminders, and provide dynamic updates to ensure users don't miss any important matters.

## Project Advantages

- **High-Quality Voice Dialogue**: Integrates excellent ASR, LLM, and TTS technologies to ensure fluency and accuracy of voice dialogue.
- **Lightweight Design**: Can run without high-performance hardware, suitable for resource-constrained environments.
- **Completely Open Source**: Bailing is completely open source, encouraging community contributions and secondary development.

## Installation and Running

### Dependencies

Please ensure the following tools and libraries are installed in your development environment:

- Python 3.11-3.12 version
- `uv` package manager (recommended) or `pip` package manager
- Dependencies required by FunASR, silero-vad, deepseek, edge-tts, Kokoro-82M

### Installation Steps

1. Clone the project repository:

    ```bash
    git clone https://github.com/wwbin2017/bailing.git
    cd bailing
    ```

2. Install required dependencies:

    **Using uv (recommended):**

    ```bash
    # First install uv (if not installed)
    pip install uv
    
    # Install project dependencies
    uv sync
    ```

    ```powershell
    # Configure variables
    # Windows configure FFMPEG_DLL_PATH
    $env:FFMPEG_DLL_PATH = "C:\path\to\ffmpeg\bin"

    # Optional configuration: huggingface mirror
    $env:HF_ENDPOINT = "https://hf-mirror.com"
    ```

3. Configure environment variables:

     - Open config/config.yaml to configure ASR, LLM and other related configurations
     - RAG functionality will automatically download the `BAAI/bge-small-zh-v1.5` embedding model, requiring network connection on first run

4. Run the project:

    ```bash
    cd server
    uv run server.py # Start backend service, this step is optional
    ```

    **Using uv to run:**

    ```bash
    uv run python main.py
    ```

    **Or run directly:**

    ```bash
    python main.py
    ```

## Usage Instructions

1. After starting the application, the system will wait for voice input.
2. User voice is converted to text through FunASR.
3. silero-vad performs voice activity detection to ensure only valid voice is processed.
4. deepseek processes text input and generates intelligent replies.
5. edge-tts, Kokoro-82M, ChatTTS, MacOS say convert generated text to speech and play it to the user.

## Roadmap

- [x] Basic voice dialogue functionality
- [x] Support plugin calls
- [x] Task management
- [x] RAG & Agent
- [x] Memory
- [ ] Support voice wake-up
- [ ] Enhance WebSearch
- [ ] Support WebRTC

In the future, Bailing will evolve into a JARVIS-like personal assistant, like a caring think tank with unparalleled memory and forward-looking task management capabilities. Based on cutting-edge RAG and Agent technologies, it will precisely control your affairs and knowledge, simplifying complexity. With just a gentle word, such as "help me find recent news" or "summarize the latest developments in large models", Bailing will respond quickly, analyze intelligently, track in real-time, and present results elegantly to you. Imagine having not just an assistant, but a wise partner who understands your needs deeply, accompanying you through every important moment in the future, helping you gain insights and achieve success.

## Supported Tools

| Function Name             | Description                                | Functionality                                                                                | Example                                                                                                         |
| ------------------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `get_weather`             | Get weather information for a location     | Provides weather conditions for a specified location                                         | User says: "What's the weather in Hangzhou?" → `zhejiang/hangzhou`                                              |
| `ielts_speaking_practice` | IELTS speaking practice                    | Generates IELTS speaking practice topics and dialogues to help users practice IELTS speaking | -                                                                                                               |
| `get_day_of_week`         | Get current day of week or date            | Returns corresponding information when user asks about current time, date, or day of week    | User says: "What day is today?" → Returns current day of week                                                   |
| `schedule_task`           | Create a scheduled task                    | Users can specify task execution time and content for timed reminders                        | User says: "Remind me to drink water every day at 8 AM." → `time: '08:00', content: 'Remind me to drink water'` |
| `open_application`        | Open specified application on Mac computer | Users can specify application name, script will launch corresponding app on Mac              | User says: "Open Safari." → `application_name: 'Safari'`                                                        |
| `web_search`              | Search specified keywords online           | Returns corresponding search results based on user-provided search content                   | User says: "Search for latest tech news." → `query: 'latest tech news'`                                         |
| `aigc_manus`              | General-purpose AI that can do anything    | Task description to execute, returns task execution results                                  | User says: "Analyze specific stock market trends" → `query: 'Analyze specific stock market trends'`             |

## Contributing Guidelines

Welcome any form of contribution! If you have suggestions for improving the Bailing project or discover issues, please provide feedback through [GitHub Issues](https://github.com/wwbin2017/bailing/issues) or submit a Pull Request.

## Open Source License

This project is open source under the [MIT License](LICENSE). You are free to use, modify, and distribute this project, but must retain the original license statement.

## Contact

For any questions or suggestions, please contact:

- GitHub Issues: [Project Issue Tracking](https://github.com/wwbin2017/bailing/issues)

---

## Disclaimer

Bailing is an open source project intended for personal learning and research purposes. Please note the following disclaimer when using this project:

1. **Personal Use**: This project is for personal learning and research only, not suitable for commercial use or production environments.
2. **Risk and Responsibility**: Using Bailing may cause data loss, system failures, or other issues. We are not responsible for any loss, damage, or problems caused by using this project.
3. **Support**: This project does not provide any form of technical support or warranty. Users should bear the risks of using this project themselves.

Before using this project, please ensure you understand and accept these disclaimers. If you do not agree to these terms, please do not use this project.

Thank you for your understanding and support!

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=wwbin2017/bailing&type=Date)](https://star-history.com/#wwbin2017/bailing&Date)
