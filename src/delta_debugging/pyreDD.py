from typing import Set, Union
import DD
import subprocess
import difflib
import patch_modified as patch_module
import copy
from parse import parse

def run_pyre(cwd='~/dd-py3/pyre_input/'):
    try:
        cmd = "pyre incremental"
        data = subprocess.check_output(cmd, cwd=cwd, shell=True, universal_newlines=True, stderr=subprocess.STDOUT)
        status = 0
    except subprocess.CalledProcessError as ex:
        data = ex.output
        status = ex.returncode
    if data[-1:] == '\n':
        data = data[:-1]
    return status, data

class MyDD(DD.DD):
    def __init__(self, warning: str, project_path: str, buggy_filepath: str, buggy_filename: str, new_w_set: Set[str]):
        DD.DD.__init__(self)
        self.warning = warning
        self.project_path = project_path
        self.buggy_filepath = buggy_filepath
        self.buggy_filename = buggy_filename
        self.new_w_set = new_w_set
        self.window_size = 1 # i.e. Default window size is +- 1 line from the buggy line
        self.found = False

    def _test(self, deltas):
        # Revert the buggy file
        subprocess.run(f"git checkout -f {self.commit}^".split(" "), cwd=self.project_path)

        # Should only have 1 item
        assert len(self.patches.items) == 1, 'PatchSet should only have 1 Patch'
        local_patches = copy.deepcopy(self.patches)
        local_patches.items[0].hunks = [j for i, j in enumerate(self.patches.items[0].hunks, 1) if i in deltas]
        # Apply directly on the buggy file
        res = local_patches.apply()
        if res == False: # return UNRESOLVED if failed to apply patch
            return self.UNRESOLVED
        # Invoke pyre
        (status, output) = run_pyre(self.project_path)

        print("Pyre output:\n", '\n'.join([o for o in output.split('\n') if o.startswith(self.buggy_filename+':')]))
        # print("Exit code", status)

        # Determine outcome
        if self.buggy_filename+':1:1 Parsing failure [404]' in output:
            return self.UNRESOLVED

        res = self.check_if_warning_fixed(local_patches, output)

        if res == self.PASS:
            return res
        else: # i.e. Warning is fixed
            # We want Set(current warnings) - Set(old warnings) = empty.
            # For comparing warnings, we only look at the content, i.e. excluding line/columns as they will change.
            # This is heuristic approach as warnings could have the same content.
            result_set = set([w.split(' ',1)[1] for w in output.split('\n') if w.startswith(self.buggy_filename+':')]) - self.warnings_before_patch
            if len(result_set) > 0:
                return self.PASS
            else:
                print('Fixed!!!: ' + self.warning)
                self.found = True
                return self.FAIL
                

    def check_if_warning_fixed(self, local_patches: patch_module.PatchSet, pyre_output: str) -> Union[DD.DD.PASS, DD.DD.FAIL]:
        """ "Fail" if warning is not found.
        """
        [loc, msg] = self.warning.split(' ',1)
        filename, warning_line_no, warning_col_no = loc.split(':',2)
        warning_line_no = int(warning_line_no)
        new_warning_line_no = warning_line_no
        # msg_regexp = msg.replace('[','\[').replace(' ','\s')
        # regexp = re.compile(r"temp_file_for_dd.py:\d+:\d+\s"+msg_regexp)
        # elif not regexp.search(output):

        # Track the warning line after patching, this line should not have warnings
        for p in local_patches.items[0].hunks:
            # patches should be sorted by their startsrc
            if (p.startsrc + p.linessrc - 1) < warning_line_no:
                new_warning_line_no += (p.linestgt - p.linessrc)
            # if warning_line is in a patch:                
            elif p.startsrc <= warning_line_no <= (p.startsrc + p.linessrc - 1):
                # If no. of removed lines ==  no. of inserted lines:
                # estimate the error line to be at the same line
                if p.linessrc == p.linestgt:                    
                    if self.buggy_filename+':'+str(new_warning_line_no)+':' in pyre_output:
                        return self.PASS
                    else:
                        return self.FAIL
                line_no_diff = new_warning_line_no - warning_line_no
                # Else: lines in this patch should not have new errors
                new_linestgt2 = p.startsrc + line_no_diff
                for l in range(new_linestgt2, new_linestgt2 + p.linestgt):
                    if self.buggy_filename+':'+str(l)+':' in pyre_output:
                        return self.PASS 
                return self.FAIL
            # The rest of the patches are after warning_line_no
            else:
                break
        # Add columns number too in case there is >1 errors at the same line
        if (self.buggy_filename+':'+ str(new_warning_line_no) +":"+str(warning_col_no)) not in pyre_output:
            return self.FAIL
        return self.PASS
        
    # Just for pretty-printing the code (after applying deltas) during delta-debugging
    def coerce(self, deltas):
        return '\n--------------------------------------'

def dd(warning: str, before: str, after: str, project_path: str, buggy_filepath: str, fixed_filepath: str, project: str, filename: str, commit: str, new_w_introduced: Set[str]) -> str:
    # Load deltas from buggy_file
    deltas = []
    index = 1

    buggy_file = before
    fixed_file = after

    diffs = difflib.unified_diff(buggy_file.splitlines(True), fixed_file.splitlines(True), buggy_filepath, buggy_filepath, n=1, lineterm='\n')
    diffs_str = ''
    for d in diffs:
        diffs_str += d
    patches = patch_module.fromstring(diffs_str.encode('utf-8')) # default to utf-8
    assert len(patches.items) == 1, 'PatchSet should only have 1 Patch, but it has '+str(len(patches.items))
    assert patches.apply() != False, 'Applying all patches must not fail'
    assert len(patches.items[0].hunks) <= 64, 'Cannot have more than 64 hunks in a file'
    for p in patches:
        for hunk in p:
            deltas.append(index)
            index = index + 1
    mydd = MyDD(warning, project_path, buggy_filepath, filename, new_w_introduced)
    mydd.patches = patches
    mydd.commit = commit
    # Revert after patches.apply(), then get warnings in buggy file
    subprocess.run(f"git checkout -f {commit}^".split(" "), cwd=project_path)
    (status, output) = run_pyre(project_path)

    warnings_before_patch = set()
    for w in output.split('\n'):
        if w.startswith(filename):
            warnings_before_patch.add(w.split(' ',1)[1])    
    mydd.warnings_before_patch = warnings_before_patch

    # --- 
    # Isolate a failure-inducing difference
    # --- 
    print("Isolating the failure-inducing difference...")
    # (c, c1, c2) = mydd.dd(deltas)	# Invoke DD
    c = mydd.ddmin(deltas) # Invoke DDMIN
    print(len(deltas))
    # Metadata
    [loc, msg] = warning.split(' ',1)
    warning_line_no = int(loc.split(':',2)[1])
    buggy_file_line_list = buggy_file.split('\n')
    buggy_line = buggy_file_line_list[warning_line_no-1]
    [rule_id, msg_content] = msg.split(':', 2)
    if not mydd.found:
        print("Did not find minimal error-fixing hunks for:", warning)
        return {
            'project': project, 
            'commit': commit, 
            'filename': filename, 
            'filename_after_commit': fixed_filepath, 
            'file_hunks_size': len(patches.items[0].hunks),
            'min_patch_found': False, 
            'single_hunk': False, 
            'fit_TFix': False, 
            'delete_only_patch': False, 
            'has_suppression_all_hunks': False, 
            'full_warning_msg': warning, 
            'message': msg_content, 
            'rule_id': rule_id, 
            'warning_line_no': warning_line_no, 
            'warning_line': buggy_line, 
        }

    print("The minimal error-fixing hunks are", c)
    min_patch = []
    for delta in c:
        fit_TFix = False
        delete_only = False
        has_suppression = False
        hunk = patches.items[0].hunks[delta-1]
        # only delete and equality diff, i.e. old code
        source_code = ''.join([d.decode()[1:] for d in hunk.text if d.startswith(b'+') != True])      
        # only insert and equality diff, i.e. new code
        target_code = ''.join([d.decode()[1:] for d in hunk.text if d.startswith(b'-') != True])
       
        # Check if there is any insert-diff
        if not any(d.startswith(b'+') == True for d in hunk.text):
            delete_only = True
        
        # Check if this hunk uses any suppression
        suppressions = ['pyre-fixme', 'pyre-ignore', 'type: ignore', 'pyre-ignore-all-errors']
        if any(d.startswith(b'+') == True and sup in d.decode() for sup in suppressions for d in hunk.text):
            has_suppression = True
            
        unidiff_form = "@@ -{},{} +{},{} @@\n".format(hunk.startsrc, hunk.linessrc, hunk.starttgt, hunk.linestgt)
        for line in hunk.text:
            unidiff_form += line.decode()

        # Check if warning line lies in line_window (via counting line no.)
        inside_window = False
        line_info = parse('@@ -{},{} +{},{} @@', unidiff_form.splitlines()[0]) # first line is @@ ... @@
        startsrc = int(line_info[0])
        linessrc = int(line_info[1])
        if startsrc <= d['warning_line_no'] <= startsrc+linessrc-1:
            inside_window = True        
        
        if (
            inside_window and 
            sum([1 for d in hunk.text if d.startswith(b'+') == True]) <= 3 and 
            sum([1 for d in hunk.text if d.startswith(b'-') == True]) <= 3 and
            len(source_code) <= 256 and
            len(target_code) <= 256
        ):
            fit_TFix = True

        min_patch.append({
            'hunk_fit_TFix': fit_TFix, 
            'inside_window': inside_window, 
            'delete_only': delete_only, 
            'has_suppression': has_suppression, 
            "source_code": source_code,
            "source_code_len": len(source_code),
            "target_code": target_code,
            "target_code_len": len(target_code),
            "diff_format": unidiff_form
        })
    return {
        'project': project, 
        'commit': commit, 
        'filename': filename, 
        'filename_after_commit': fixed_filepath, 
        'file_hunks_size': len(patches.items[0].hunks),
        'min_patch_found': True, 
        'single_hunk': True if len(min_patch) == 1 else False, 
        'fit_TFix': True if len(min_patch) == 1 and min_patch[0]['hunk_fit_TFix'] else False, 
        'delete_only_patch': all(h['delete_only'] == True for h in min_patch),
        'has_suppression_all_hunks': all(h['has_suppression'] == True for h in min_patch),
        'full_warning_msg': warning, 
        'message': msg_content, 
        'rule_id': rule_id, 
        'warning_line_no': warning_line_no, 
        'warning_line': buggy_line, 
        'min_patch': min_patch,
    }
