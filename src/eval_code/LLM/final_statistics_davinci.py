import json

# Read the JSON file
with open('./output/error_removal_analysis_openai_davinci_top50.json') as file:
    data = json.load(file)

true_count_top1 = 0
true_count_top5 = 0
true_count_top50 = 0

# Iterate over the data and count occurrences of True and False in the "fixed" field
for entry in data:
    i = 0
    #print(entry[f'pred_top-1']["warning_removed"])
    
    try:
        while i < 5:
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
         
        print('Error', e)
        #break

# Print the counts
print('Top-1:', (true_count_top1 / 309)*100)
print('Top-5:', (true_count_top5 / 309)*100)
print('Top-50:', (true_count_top50 / 309)*100)
