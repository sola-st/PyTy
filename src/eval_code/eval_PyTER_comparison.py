import json

def may_be_type_cast(old_code, new_code):
    # casts that are supported by PyTER (best-effort guess based on https://github.com/kupl/pyter_tool/blob/main/my_tool/template/template_to_ast.py)
    return "int(" in new_code or "str(" in new_code or "bool(" in new_code or "bytes(" in new_code or "list(" in new_code or "tuple(" in new_code or "set(" in new_code or "dict(" in new_code

def may_be_isinstance_check(old_code, new_code):
    return "isinstance" in new_code

def may_be_exception_handling(old_code, new_code):
    return "except" in new_code

def ask_to_classify(old_code, new_code, possible_template_matches):
    print(f"\nDoes the following fix match any of the PyTER fix templates? ({', '.join(possible_template_matches)})\n")
    print(f"Old code:\n{old_code}\n")
    print(f"New code:\n{new_code}\n")
    print("Type 'y' for yes, 'n' for no, 'q' for quit.")
    answer = input()
    return answer

with open("output/test_data_baseline_top50_pyter_comparison.json") as f:
    test_data = json.load(f)
    print(f"Number of entries: {len(test_data)}")

maybe_type_casts = []
maybe_isinstance_checks = []
maybe_exception_handlings = []
certainly_unsupported = []
for entry in test_data:
    old_code = entry["source_code"]
    new_code = entry["target_code"]

    if "maybe_pyter_supported" in entry:
        print(f"Skipping already classified example")
        continue

    # check if the fix may match one of the fix templates of PyTER
    maybe_supported = False
    possible_template_matches = []
    if may_be_type_cast(old_code, new_code):
        maybe_type_casts.append(entry)
        maybe_supported = True
        possible_template_matches.append("type cast")
    if may_be_isinstance_check(old_code, new_code):
        maybe_isinstance_checks.append(entry)
        maybe_supported = True
        possible_template_matches.append("isinstance check")
    if may_be_exception_handling(old_code, new_code):
        maybe_exception_handlings.append(entry)
        maybe_supported = True
        possible_template_matches.append("exception handling")
    
    if maybe_supported:
        answer = ask_to_classify(old_code, new_code, possible_template_matches)
        if answer == "y":
            entry["maybe_pyter_supported"] = True
        elif answer == "n":
            entry["maybe_pyter_supported"] = False
        elif answer == "q":
            break
    if not maybe_supported:
        certainly_unsupported.append(entry)
        entry["maybe_pyter_supported"] = False

print(f"Number of maybe type casts: {len(maybe_type_casts)}")
print(f"Number of maybe isinstance checks: {len(maybe_isinstance_checks)}")
print(f"Number of maybe exception handlings: {len(maybe_exception_handlings)}")
print(f"Number of certainly unsupported: {len(certainly_unsupported)}")

with open("output/test_data_baseline_top50_pyter_comparison.json", "w") as f:
    json.dump(test_data, f, indent=2)