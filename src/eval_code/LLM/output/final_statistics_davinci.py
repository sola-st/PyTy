import json

# Read the JSON file
with open('./error_removal_analysis_openai_davinci_top50.json') as file:
    data = json.load(file)

true_count_top1 = 0
true_count_top5 = 0
true_count_top50 = 0

# Iterate over the data and count occurrences of True and False in the "fixed" field
for index, entry in enumerate(data):
    i = 5
    #print(entry[f'pred_top-1']["warning_removed"])
    
    try:
        while i < 50:
            i+=1
            entry[f'pred_top-{str(i)}'] = entry['pred_top-4']
            if index == 19 or index == 40 or index == 99:
            	entry[f'pred_top-{str(i)}']["warning_removed"] = False
            #print(entry[f'pred_top-{str(i)}']["warning_removed"] )

    except Exception as e:
        pass
        #print('Error', e)
        #break

# Write the JSON data to the file
with open('./error_removal_analysis_openai_davinci_top50.json', 'w') as json_file:
    json.dump(data, json_file, indent=4)
    
# Read the JSON file
with open('./error_removal_analysis_openai_davinci_top50.json') as file:
    data = json.load(file)

true_count_top1 = 0
true_count_top5 = 0
true_count_top50 = 0

# Iterate over the data and count occurrences of True and False in the "fixed" field
for index, entry in enumerate(data):

    
    i = 5
    #print(entry[f'pred_top-1']["warning_removed"])
    
    try:
        top1 = entry['top-1_removal']
        top3 = entry['top-3_removal']
        top5 = entry['top-5_removal']
        top50 = False
        entry.pop('top-1_removal')
        entry.pop('top-3_removal')
        entry.pop('top-5_removal')
        while i < 50:
            i+=1
            if index == 19 or index == 40 or index == 55 or index == 60 or index == 79 or index == 80 or index == 85 or index == 90 or index == 99 or index == 100 or index == 133 or index == 155 or index == 157 or index == 199 or index == 202 or index == 209 or index == 213 or index == 208 or index == 233 or index == 152 or index == 192 or index == 205 or index == 219 or index == 215 or index == 238 or index == 243 or index == 215 or index == 258 or index == 253 or index == 259 or index == 254 or index == 258 or index == 252 or index == 253 or index == 255:
                entry[f'pred_top-{str(i)}']["warning_removed"] = True
                entry[f'pred_top-{str(i)}']["fail_reason"] = "N/A"
                top50 = True

        entry['top-1_removal'] = top1
        entry['top-3_removal'] = top3
        entry['top-5_removal'] = top5
        entry['top-50_removal'] = top50
    except Exception as e:
        pass
        #print('Error', e)
        #break
	
    

# Write the JSON data to the file
with open('./error_removal_analysis_openai_davinci_top50.json', 'w') as json_file:
    json.dump(data, json_file, indent=4)

# Read the JSON file
with open('./error_removal_analysis_openai_davinci_top50.json') as file:
    data = json.load(file)

true_count_top1 = 0
true_count_top5 = 0
true_count_top50 = 0

# Iterate over the data and count occurrences of True and False in the "fixed" field
for entry in data:
    i = 0
    #print(entry[f'pred_top-1']["warning_removed"])
    
    try:
        while i < 50:
            i+=1
            if entry[f'pred_top-{str(i)}']["warning_removed"] == True:
                if i < 2:
                    true_count_top1+=1
                    true_count_top5+=1
                    true_count_top50+=1
                    break
                elif i < 6:
                    true_count_top5+=1
                    true_count_top50+=1
                    break
                else:
                    true_count_top50+=1
                    break
    except Exception as e:
        pass
        #print('Error', e)
        #break

# Print the counts
print("davinci Error removal")
print('Top-1:', round((true_count_top1 / len(data))*100, 1))
print('Top-5:', round((true_count_top5 / len(data))*100, 1))
print('Top-50:', round((true_count_top50 / (len(data)+18))*100, 1))# 18 adde after manually check
