# ICS Generator  
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
It will prompt you to enter your details in **normal English**, processes the text, then generates an ICS file!

🔹 **Import to Google Calendar**  
1. Open [Google Calendar](https://calendar.google.com/).  
2. Click the ⚙️ **Settings** → **Import & Export**.  
3. Upload your `.ics` file, and all events will be added to your calendar.  

🔹 **Add to Apple Calendar (Mac & iPhone)**  
1. Open the **Calendar** app.  
2. Click **File → Import** and select the `.ics` file.  
3. Events will be added instantly!  

🔹 **Use in Microsoft Outlook**  
1. Open **Outlook** and go to **File → Open & Export**.  
2. Select **Import an iCalendar (.ics) file** and upload your file. 

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