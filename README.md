# **Eliza Engine: A Script-Based Chatbot Framework**

**Eliza Engine** is an extensible, script-based chatbot framework inspired by Joseph Weizenbaum's original ELIZA program. This project goes beyond a simple replica by providing a robust engine that can be loaded with any personality (or "persona") defined in a JSON script. It features a modern Python backend, strong data validation, and a friendly web interface for interaction.

The core idea is to separate the chatbot's logic from its personality. The Python engine handles the conversation flow, while simple JSON files define what the chatbot says and how it reacts. This allows anyone to create entirely new chatbot characters without writing any Python code.

This repository includes a variety of personas in the `scripts` folder;

![image](https://github.com/user-attachments/assets/67f537d7-0c15-4a0d-bee8-b6c58f08126b)

## **✨ Key Features**

* **Dynamic Personas**: Load different chatbot personalities on-the-fly from JSON files.  
* **Extensible by Design**: Create new chatbots by simply writing a new JSON script—no changes to the Python codebase are needed.  
* **Robust Script Validation**: Uses Pydantic to ensure that persona scripts are well-formed and logically consistent before they are loaded, preventing runtime errors.  
* **Interactive Web UI**: Built with Streamlit, the application provides a user-friendly interface to select, edit, and chat with different personas.  
* **Modern Codebase**: Clean, commented, and type-hinted Python code.

## **📂 Project Structure**

The project is organized into several key files:
```
.  
├── app.py              # The main Streamlit web application  
├── eliza.py            # The core chatbot engine class  
├── validator.py        # Pydantic models for script validation  
├── requirements.txt    # Project dependencies  
└── scripts/  
    ├── eliza.json      # The default ELIZA persona script  
    └── *.json          # Custom persona scripts
```

* **app.py**: Entry point for the application. It handles the UI, file uploads, and state management.  
* **eliza.py**: Contains the Eliza class, which parses input, matches it against rules from the loaded script, and generates responses.  
* **validator.py**: Defines the data structure of a valid persona script using Pydantic. It checks for required fields, valid goto statements, and correct synonym references.  
* **scripts/**: A directory to store all the JSON persona files.

## **🔧 How It Works**

The engine's logic is based on the pattern-matching system of the original ELIZA program.

1. **Load Script**: The application starts by loading a user-selected JSON persona script.  
2. **Validate**: The script's content is validated against the ElizaScript model in validator.py.  
3. **Initialize**: An instance of the Eliza class is created with the validated script.  
4. **Process Input**: When the user sends a message, the engine:  
   * Normalizes the input (lowercase, substitutions like "i'm" \-\> "i am").  
   * Scans the input for keywords defined in the script.  
   * Selects the keyword with the highest rank (priority).  
   * Matches the input against the keyword's decomposition rules.  
   * Constructs a response using the corresponding reassembly rule.  
5. **Respond**: The generated response is displayed to the user.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- `uv` (a fast Python package installer)

### Installation

1. **Install `uv` (if you don't have it):**
```
pip install uv
```

2. **Clone the repository:**
```
git clone https://github.com/eduresser/eliza-engine.git
cd eliza-engine
````

3. **Create and activate a virtual environment using `uv`:**
```
uv venv
source .venv/bin/activate
# On Windows, use: .venv\Scripts\activate
```

4. **Install the required dependencies using `uv`:**
```
uv pip sync requirements.txt
```
(**Note:** The `requirements.txt` file should contain `streamlit`, `pydantic`, and `streamlit-ace`)

5. **Running the Application:**

Once the dependencies are installed, run the Streamlit application from your terminal:
```
streamlit run app.py
```
Your web browser should open with the application running at `http://localhost:8501`.

## **✍️ Creating a New Persona**

You can create your own chatbot persona by adding a new `.json` file to the `scripts/` directory. The file must follow the structure validated by validator.py.

Below is a template with a more advanced example rule that uses wildcards (`*`), synonym groups (`@`), and capture groups (`(n)`).
```
{
  "name": "YourBotName",
  "initials": [
    "Hello, how can I help you today?",
    "Greetings."
  ],
  "finals": [
    "Goodbye.",
    "It was a pleasure talking to you."
  ],
  "quits": [
    "bye",
    "exit"
  ],
  "pres": {
    "i'm": "i am"
  },
  "posts": {
    "am": "are",
    "i": "you",
    "my": "your"
  },
  "synons": {
    "sad": ["unhappy", "depressed", "miserable"],
    "happy": ["glad", "joyful"]
  },
  "keywords": [
    {
      "key": "xnone",
      "rank": 0,
      "rules": [
        {
          "decomp": "*",
          "reasmb": ["Please tell me more."]
        }
      ]
    },
    {
      "key": "i",
      "rank": 2,
      "rules": [
        {
          "decomp": "* i am @sad *",
          "reasmb": [
            "I am sorry to hear that you are (3).",
            "Do you think coming here will help you not to be (3)?",
            "I'm sure it's not pleasant to be (3)."
          ]
        }
      ]
    }
  ]
}
```
### Explanation of the Advanced Rule:

Let's break down this keyword rule: `"decomp": "* i am @sad *"`

- This rule is triggered by the keyword `"i"`.
- The `decomp` pattern looks for a sentence containing `"i am"` followed by a word from the `"sad"` synonym group.
- The `*` are wildcards.
    - The first `*` captures everything before `"i am"`. This will be `(1)`.
    - The part `"i am @sad"` is matched literally (with `@sad` matching `"sad"`, `"unhappy"`, or `"miserable"`). This will be `(2)`.
    - The second `*` captures everything after the sad feeling. This will be `(3)`.

If a user says, `"It's true that i am unhappy today"`, the engine will:

1. Match the `i` keyword.
2. Match the decomposition `rule * i am @sad *`.
3. Capture the parts:
    - `(1)` -> "it's true that"
    - `(2)` -> "i am unhappy"
    - `(3)` -> "today"
4. Choose a response from reasmb, like `"I am sorry to hear that you are (3)."`, and substitute `(3)` with `"today"`.
5. Final response: `"I am sorry to hear that you are today."` (Note: `posts` rules would further refine this).

## **📜 License**

This project is licensed under the MIT License.
