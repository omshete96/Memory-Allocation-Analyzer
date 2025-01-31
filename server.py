from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

def detect_language(code):
    """Detects the programming language based on syntax."""
    if re.search(r'#include\s*<\w+>', code) or re.search(r'int\s+main\(\)', code):
        return "C/C++"
    elif re.search(r'public\s+class\s+\w+', code) or "System.out.println" in code:
        return "Java"
    elif "def " in code and ":" in code:
        return "Python"
    elif "function " in code or "const " in code or "let " in code or "var " in code:
        return "JavaScript"
    else:
        return "Unknown"

def analyze_c_cpp(code):
    """Analyzes memory locations of variables in C/C++ code."""
    results = []
    lines = code.split('\n')
    global_vars = set()

    for line in lines:
        line = line.strip()

        # Detect global variables before main()
        if "int main()" in line or "void main()" in line:
            break

        if re.match(r"(int|float|double|char|bool)\s+\w+", line):
            variable = line.split()[1].strip(";")
            global_vars.add(variable)
            results.append({'variable': variable, 'memory': 'Data Segment'})

    # Process variables inside functions
    for line in lines:
        line = line.strip()

        if '=' in line:
            parts = line.split('=')
            variable = parts[0].strip().split()[-1]

            if variable in global_vars:
                continue  # Already classified as global

            if any(kw in line for kw in ['new ', 'malloc', 'calloc']):
                results.append({'variable': variable, 'memory': 'Heap'})
            elif 'const ' in line or 'static ' in line:
                results.append({'variable': variable, 'memory': 'Data Segment'})
            else:
                results.append({'variable': variable, 'memory': 'Stack'})
        elif re.match(r"(int|float|double|char|bool)\s+\w+", line):
            variable = line.split()[1].strip(';')
            if variable not in global_vars:
                results.append({'variable': variable, 'memory': 'Stack'})

    return results

def analyze_java(code):
    """Analyzes memory locations of variables in Java."""
    results = []
    lines = code.split('\n')

    for line in lines:
        line = line.strip()

        if '=' in line:
            parts = line.split('=')
            variable = parts[0].strip().split()[-1]

            if 'new ' in line:
                results.append({'variable': variable, 'memory': 'Heap'})
            elif 'static ' in line:
                results.append({'variable': variable, 'memory': 'Method Area (Data Segment)'})
            else:
                results.append({'variable': variable, 'memory': 'Stack'})

        elif re.match(r"(int|float|double|char|boolean|String)\s+\w+", line):
            variable = line.split()[1].strip(';')
            results.append({'variable': variable, 'memory': 'Stack'})

    return results

def analyze_python(code):
    """Analyzes memory locations of variables in Python."""
    results = []
    lines = code.split('\n')

    for line in lines:
        line = line.strip()
        if '=' in line and not line.startswith("def "):
            variable = line.split('=')[0].strip()
            results.append({'variable': variable, 'memory': 'Heap'})  # Python stores variables on the Heap

    return results

def analyze_javascript(code):
    """Analyzes memory locations of variables in JavaScript."""
    results = []
    lines = code.split('\n')

    for line in lines:
        line = line.strip()
        if '=' in line:
            variable = line.split('=')[0].strip().replace("var ", "").replace("let ", "").replace("const ", "")
            results.append({'variable': variable, 'memory': 'Heap'})  # JavaScript stores objects on the Heap

    return results

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    code = data.get("code", "")
    
    language = detect_language(code)

    if language == "C/C++":
        analysis = analyze_c_cpp(code)
    elif language == "Java":
        analysis = analyze_java(code)
    elif language == "Python":
        analysis = analyze_python(code)
    elif language == "JavaScript":
        analysis = analyze_javascript(code)
    else:
        analysis = [{"error": "Unknown programming language"}]

    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True)
