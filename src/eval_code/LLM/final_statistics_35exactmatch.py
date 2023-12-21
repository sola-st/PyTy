import json

# Read the JSON file
with open('./output/gpt-3.5-turbo_fixes.json') as file:
    data = json.load(file)

true_count_top1 = 0
true_count_top5 = 0
true_count_top50 = 0

# Iterate over the data and count occurrences of True and False in the "fixed" field
for entry in data:
    try:
        for index, prediction in enumerate(entry['top_predictions']):
            
            if prediction['fixed'] == 'True':
                if index < 1:
                    true_count_top1+=1
                    true_count_top5+=1
                    true_count_top50+=1
                    break
                elif index < 5:
                    true_count_top5+=1
                    true_count_top50+=1
                    break
                else:
                    true_count_top50+=1
                    break
    except: 
        pass
        #print('Error')

# Print the counts
print("GPT 3.5 Exact match")
print('Top-1:', round(((true_count_top1 / 281)*100),1))
print('Top-5:', round(((true_count_top5 / 281)*100),1))
print('Top-50:', round(((true_count_top50 / 281)*100),1))
