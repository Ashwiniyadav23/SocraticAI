import os
import re

def audit_coverage():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
    
    pos_calls = 0
    raw_prompts = 0
    raw_files = []
    
    # Matches old imports or direct usages
    raw_pattern = re.compile(r"(PromptTemplate|SYSTEM_PROMPT|MODE_PROMPTS)")
    # Matches PromptService calls
    pos_pattern = re.compile(r"PromptService\.render")
    
    for root, dirs, files in os.walk(base_dir):
        # Ignore tests and scripts, focus on app logic
        if "tests" in root or "scripts" in root:
            continue
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            has_raw = bool(raw_pattern.search(content))
            has_pos = bool(pos_pattern.search(content))
            
            # Count instances instead of just boolean? 
            # We'll just count files that contain them for simplicity, or count occurrences.
            pos_count = len(pos_pattern.findall(content))
            raw_count = len(raw_pattern.findall(content))
            
            pos_calls += pos_count
            raw_prompts += raw_count
            
            if raw_count > 0:
                raw_files.append(file_path)
                
    total = pos_calls + raw_prompts
    coverage = (pos_calls / total * 100) if total > 0 else 100.0
    
    print(f"Number of PromptService calls: {pos_calls}")
    print(f"Number of remaining hardcoded prompts: {raw_prompts}")
    print(f"Coverage percentage: {coverage:.2f}%")
    if raw_files:
        print("Files containing raw prompts:")
        for f in raw_files:
            print(f" - {f}")

if __name__ == "__main__":
    audit_coverage()
