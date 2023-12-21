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

directory = r'Output/'
for data_file in os.listdir(directory):
    with open(directory+data_file) as f:
      try:
        data = json.load(f) 
        for d in data: 
          try:
            if d.get('min_patch'):
              p = d['project']
              p_path = p.replace('/', '-')
              commit = d['commit']  
              repo_dir = "~/TypeAnnotation_Study/GitHub/" + p_path
              # Tokenize source lines
              subprocess.run(f"git checkout -f {commit}^".split(" "), check=True, cwd=repo_dir)
              src_file = repo_dir+'/'+d['filename']
              before = Path(src_file).read_text()
              for hunk in d['min_patch']:
                if hunk.get('source_code_with_indent_exact_match'):
                  continue
                diff_meta = hunk['diff_format'].splitlines()[0]
                line_idx, line_count = diff_meta.split('+')[0].strip('@- ').split(',', 1)
                tokens = str_to_token_list(before, int(line_idx), int(line_count))
                code_with_indent = ''.join(tokens)
                if code_with_indent.replace('<IND>','').replace('<DED>','').split() == hunk['source_code'].split():
                  hunk['source_code_with_indent'] = code_with_indent
                  hunk['source_code_with_indent_exact_match'] = True
                else:
                  hunk['source_code_with_indent'] = code_with_indent
                  hunk['source_code_with_indent_exact_match'] = False
                  # logging.info(code_with_indent)
                  # logging.info(hunk['source_code'])
                  # raise Exception('"source_code_with_indent" does not match "source_code".')

              # Tokenize target lines
              subprocess.run(f"git checkout -f {commit}".split(" "), check=True, cwd=repo_dir)              
              tgt_file = d['filename_after_commit']
              after = Path(tgt_file).read_text()
              for hunk in d['min_patch']:
                if hunk.get('target_code_with_indent_exact_match'):
                  continue
                diff_meta = hunk['diff_format'].splitlines()[0]
                line_idx, line_count = diff_meta.split('+')[1].strip('@- ').split(',', 1)
                tokens = str_to_token_list(after, int(line_idx), int(line_count))
                code_with_indent = ''.join(tokens)
                if code_with_indent.replace('<IND>','').replace('<DED>','').split() == hunk['target_code'].split():
                  hunk['target_code_with_indent'] = code_with_indent
                  hunk['target_code_with_indent_exact_match'] = True
                else:
                  hunk['target_code_with_indent'] = code_with_indent
                  hunk['target_code_with_indent_exact_match'] = False
                  # logging.info(code_with_indent)
                  # logging.info(hunk['target_code'])
                  # raise Exception('"target_code_with_indent" does not match "target_code".')

          except Exception as e:
            logging.info(traceback.format_exc())
            logging.info(f)
            pass
          # sys.exit()
      except Exception:
        logging.info(traceback.format_exc())
        logging.info(f)
    
    # Write the updated fields back to the file
    with open(directory+data_file, "w") as f:
      json.dump(data, f, indent=2)
      
print('Done')
