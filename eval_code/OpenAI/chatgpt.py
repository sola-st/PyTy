import json
import os
import re
import time
import openai
import random
import datetime

# Set up OpenAI API credentials
openai.api_key = '' # Add your key here
model = 'gpt-3.5-turbo'

# Path to the directory containing JSON files
json_directory = './input'
# List to store the fixes
json_fixes = []

start_time = time.time()

j=0
correct = 0
wrong = 0
# Iterate through each JSON file in the directory
for filename in os.listdir(json_directory):
    if filename.endswith('.json'):
        json_path = os.path.join(json_directory, filename)

        # Read the JSON file
        with open(json_path) as file:
            data = json.load(file)

        for error in data:
            j+=1
            print("Fixing sample", j)
            try:
                # Extract source code and error message from JSON
                source_code = error['source_code']
                error_message = error["linter_report"]['message']
                warning_line = error['warning_line']

                # Ask ChatGPT to fix the code
                prompt = f"""
                ===== TASK =====
                Fix the following Python code with a Type error.\n
                ===== BUGGY CODE =====
                \n{source_code}\n
                ===== ERROR MESSAGE =====
                Error: {error_message}\n
                ===== LINE WITH THE ERROR =====
                Line with the warning: {warning_line}\n
                ===== SOLUTION =====
                Solution: Add the entire fixed snippet of code between these keywords <STARTSNIPPET>...<ENDSNIPPET> so I can use regexs.\n
                Do not add comments, only the code."""
                #print(prompt)
                random.seed()

                    # Call the OpenAI API to generate a response
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "system", 'content': prompt}],
                    max_tokens=182,
                    n=50,
                    temperature=0.3,
                    top_p=1,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    #seed=random.randint(1, 1000)  # Generate a random seed
                )
                # Get the response text from the API response
                #response_text = response['choices'][0]['message']['content']

                ground_truth = error['target_code']
                fixes = []

                # Print the top responses
                for i, choice in enumerate(response['choices']):
                    # Extract the fixed code from ChatGPT's response
                    #fixed_code = choice.text.strip()
                    fixed_code = choice['message']['content'].strip()

                    #print(fixed_code)

                    # Define the regular expression pattern
                    pattern = r"<STARTSNIPPET>(.*?)<ENDSNIPPET>"

                    # Find matches using the regex pattern
                    matches = re.search(pattern, fixed_code, re.DOTALL)

                    # Extract the snippet (first match)
                    if matches:
                        fixed_snippet = matches.group(1).strip()
                        #print(snippet)
                    else:
                        print("No snippet found, wrong solution")
                                    # Create a dictionary with the code and fix
                        fix_data = {
                            #'ground_truth': ground_truth,
                            'fixed_snippet': 'nothing',
                            'fixed': 'False'
                        }

                        # Append the fix data to the list
                        fixes.append(fix_data)
                        continue

                    # Compare the fixed code with the ground truth
                    is_correct = fixed_snippet.replace(" ", '').replace("\n","") == ground_truth.replace(" ", '').replace("\n","").replace("<IND>","").replace("<DED>","")

                    # Create a dictionary with the code and fix
                    fix_data = {
                        #'ground_truth': ground_truth,
                        'fixed_snippet': fixed_snippet,
                        'fixed': str(is_correct)
                    }

                    # Append the fix data to the list
                    fixes.append(fix_data)

                    if is_correct:
                        correct+=1
                    else:
                        wrong+=1

                    #i+=1
                    #print(i)
                    #if i > 2:
                    #    break
                
                top_fix_data = {
                        'ground_truth': ground_truth,
                        'top_predictions': fixes
                    }
                json_fixes.append(top_fix_data)

                time.sleep(10) # to avoid API error
            except Exception as e:
                print(e) 
                continue

# Record the end time
end_time = time.time()

# Compute the duration in minutes
duration_minutes = (end_time - start_time) / 60

# Convert duration to human-readable format
duration = datetime.timedelta(minutes=duration_minutes)

timestampt = {
    'Start_time': str(start_time),
    'End_time': str(end_time),
    'Total_time': str(duration)
}

json_fixes.append(timestampt)

print("Correct:", correct)
print("Wrong", wrong)
# Write the fixes to a JSON file
with open(f'{model}_fixes.json', 'w') as file:
    json.dump(json_fixes, file, indent=4)
