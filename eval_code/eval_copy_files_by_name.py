import json
import os

# copy dirs from a dir to another dir, according to a name txt file
def copy_file_by_name(src_dir, dst_dir, name_file):
    with open(name_file, 'r') as f:
        names = f.readlines()
    for name in names:
        name = name.strip()
        src_file = src_dir + name
        dst_file = dst_dir + name
        if os.path.exists(src_file):
          with open(src_file, 'r') as f:
              data = json.load(f)
          with open(dst_file, 'w') as f:
              json.dump(data, f)


copy_file_by_name('./eval_output/warnings/',
                  './eval_output/warnings_active_daily_project/', 'eval_active_daily_project.txt')
