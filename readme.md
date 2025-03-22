# 🗓️ ICS Generator  
### Converts a prompt into an ICS file to import events into calendar using natural language processing  


[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)

**ICS Generator** is a python based tool that converts plain text descriptions into `.ics` calendar events. For example saying that:  
> "I have a chemistry exam on June 19th at 9 AM and a meeting the day after"  
It will **automatically extract the details** and generate an `.ics` file to import into your calendar!  

## 🌟 Features  
✅ **AI-powered text interpretation** – No need to format your input, just describe your events naturally!  
✅ **Automatic date & time extraction** – Supports phrases like "tomorrow," "next Monday," and specific dates.  
✅ **Exports to `.ics` format** – Easily import into Google Calendar, Apple Calendar, and Outlook.  
✅ **Command-line interface (CLI)** – Simple and interactive terminal usage.  

## 📜 Table of Contents  
- [Installation](#installation)  
- [Usage](#usage)  
- [Examples](#examples)  
- [Configuration](#configuration)  
- [Contributing](#contributing)  
- [License](#license)  

## 🛠 Installation  

### 1️⃣ Clone the repo  
```bash
git clone https://github.com/yourusername/ics-generator.git
cd ics-generator
```

### 2️⃣ Install Dependencies  
```bash
pip install -r requirements.txt
```

### 3️⃣ Download Language Model  
Ensure you have **spaCy's English model** for NLP processing:  
```bash
python -m spacy download en_core_web_sm
```

## 🚀 Usage  
Run the script and input your event details:  
```bash
python icsGen.py
```
It will prompt you to enter event details in **plain English**, process the text, and generate an ICS file!

## 🔥 Example  
**Input:**  
```
I have a Physics exam on May 10th at 2 PM and a project deadline on the 15th at noon.
```

**Generated `.ics` file:**  
```plaintext
BEGIN:VEVENT
DTSTART:20240510T140000Z
DTEND:20240510T150000Z
SUMMARY:Physics Exam
END:VEVENT

BEGIN:VEVENT
DTSTART:20240515T120000Z
DTEND:20240515T130000Z
SUMMARY:Project Deadline
END:VEVENT
```



---

**🎯 Plans:**  
- Add support for **recurring events**  
- Improve AI to handle **more complex date/time inputs**  
- Create a **web interface** for easier usage  