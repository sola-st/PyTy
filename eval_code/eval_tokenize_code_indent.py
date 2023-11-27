# Add indentation and dedentation tokens to the Python source code data
import io
import json
import logging
import os
import subprocess
import sys
import tokenize
import traceback
from os.path import exists
from pathlib import Path


def str_to_token_list(s, line_idx, line_count):
    tokens = []  # list of tokens extracted from source code.
    buf = io.StringIO(s)
    tokens_generator = tokenize.generate_tokens(buf.readline)
    try:
      prev_line = -1
      prev_col_end = -1
      for token in tokens_generator:
        # ignore tokens that are not in our diff and ignore multi-line tokens that go beyond our diff, e.g. multi-line comments
        if (
          not (line_idx <= token[2][0] < line_idx + line_count) or
          not (line_idx <= token[3][0] < line_idx + line_count)
        ):
          prev_line = token[3][0]
          prev_col_end = token[3][1]
          continue        
        # Calculate the whitespace btw tokens
        if (prev_line != -1 and prev_line != token[2][0]): # new line
          tokens.append(' '*(token[2][1]))
        elif (prev_line != -1 and prev_line == token[2][0]) and (prev_col_end != -1 and prev_col_end < token[2][1]):
          tokens.append(' '*(token[2][1] - prev_col_end))
        # if token[1].strip() != '':
        #     tokens.append(token[1])
        # elif token[0] == tokenize.NEWLINE:
        #     tokens.append('NEWLINE')
        tokens.append(token[1])
        if token[0] == tokenize.INDENT:
            tokens.append('<IND>')
        elif token[0] == tokenize.DEDENT:
            tokens.append('<DED>')
        # else:
        #     tokens.append(token[1])
        prev_line = token[3][0]
        prev_col_end = token[3][1]
    # suppress raise from buggy code
    # Note: Exception is only raised at EOF
    except Exception as e:
      print(traceback.format_exc())
    return tokens

logging.basicConfig(
  format='%(asctime)s %(levelname)-8s %(message)s', 
  level=logging.INFO, 
  datefmt='%Y-%m-%d %H:%M:%S', 
  filename='./tokenize_code_indent.log')

directory = r'eval_output/warnings/'
for data_file in os.listdir(directory):
    with open(directory+data_file) as f:
      try:
        data = json.load(f) 
        for d in data: 
          try:
            p = d['project']
            p_path = p.replace('/', '-')
            commit = d['commit_hash']  
            repo_dir = "../TypeAnnotation_Study/GitHub/" + p_path
            # Tokenize source lines
            # You should not need to checkout again, the repo is already at the correct commit hash
            # Uncomment this line if you are not sure
            # subprocess.run(f"git checkout -f {commit}".split(" "), check=True, cwd=repo_dir)
            src_file = repo_dir+'/'+d['file_name']
            before = Path(src_file).read_text()
            line_idx, line_count = d['line_num']-2, 5
            tokens = str_to_token_list(before, int(line_idx), int(line_count))
            code_with_indent = ''.join(tokens)
            if code_with_indent.replace('<IND>','').replace('<DED>','').split() == d['source_code'].split():
              d['source_code_with_indent'] = code_with_indent
              d['source_code_with_indent_exact_match'] = True
            else:
              d['source_code_with_indent'] = code_with_indent
              d['source_code_with_indent_exact_match'] = False
            # print(code_with_indent)
            # print(d['source_code'])
            # sys.exit()
          except Exception as e:
            logging.info(traceback.format_exc())
            logging.info(f)
            pass
      except Exception:
        logging.info(traceback.format_exc())
        logging.info(f)
    
    # Write the updated fields back to the file
    with open(directory+data_file, "w") as f:
      json.dump(data, f, indent=2)
    # sys.exit()
      
print('Done')
