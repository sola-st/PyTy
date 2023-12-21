import json

# Read the JSON file
with open('gpt-4_fixes_gpt4.json') as file:
    data = json.load(file)

true_count_top1 = 0
true_count_top5 = 0
true_count_top50 = 0

# Iterate over the data and count occurrences of True and False in the "fixed" field
for entry in data[:-1]:
    i = 0
    #print(entry[f'pred_top-1']["warning_removed"])
    #print(entry[f'top_predictions'][0]["fixed"] )
    #break
    #i = -1
    try:
        while i < 49:
            i+=1
            if entry[f'top_predictions'][i]["fixed"] == str(True):
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
         
        print('Error', e, i)
        #break

# Print the counts
print("GPT4 Exact match")
print('Top-1:', round((true_count_top1 / len(data))*100, 1))
print('Top-5:', round((true_count_top5 / len(data))*100,1))
print('Top-50:', round((true_count_top50 / len(data))*100,1))
