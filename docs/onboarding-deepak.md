# Onboarding review: Deepak

Task 1: Install and use faultgate following the README, and record where a new user gets struck.

## 1. Environment:
- OS: Windows 11 Home Single Language, version 10.0.26200
- Shell: Windows PowerShell 5.1, run inside VS Code
- Python: 3.14.0
- faultgate: 0.4.1
- Date of run: 28 October 2026

Things to mention:
- pip packages were cached from an earlier session on the same machine, so the install was faster than the first time.

## 2. Time to first working check

- Start: 17:11:05
- First sucessful 'faultgate check': between 17:30:34 and 17:31:26, about 20 minutes in total.
- About 15 minutes went on working out that 'examples/' is only in the cloned repo.

## 3. Commands run and actual output

### Install and version
'''
(.venv) PS C:\Users\Deepak Babu P K> pip install faultgate
Requirement already satisfied: faultgate in .\.venv\Lib\site-packages (0.4.1)
Requirement already satisfied: pydantic>=2 in .\.venv\Lib\site-packages (from faultgate) (2.14.1)
Requirement already satisfied: annotated-types>=0.6.0 in .\.venv\Lib\site-packages (from pydantic>=2->faultgate) (0.8.0)
Requirement already satisfied: pydantic-core==2.50.1 in .\.venv\Lib\site-packages (from pydantic>=2->faultgate) (2.50.1)
Requirement already satisfied: typing-extensions>=4.16.0 in .\.venv\Lib\site-packages (from pydantic>=2->faultgate) (4.16.0)
Requirement already satisfied: typing-inspection>=0.4.4 in .\.venv\Lib\site-packages (from pydantic>=2->faultgate) (0.4.4)
(.venv) PS C:\Users\Deepak Babu P K> git clone https://github.com/Faultline-lab/faultgate.gitfaultgate --version
error: unknown option `version'
usage: git clone [<options>] [--] <repo> [<dir>]

    -v, --[no-]verbose    be more verbose
    -q, --[no-]quiet      be more quiet
    --[no-]progress       force progress reporting
    --[no-]reject-shallow don't clone shallow repository
    -n, --no-checkout     don't create a checkout
    --checkout            opposite of --no-checkout
    --[no-]bare           create a bare repository
    --[no-]mirror         create a mirror repository (implies --bare)
    -l, --[no-]local      to clone from a local repository
    --no-hardlinks        don't use local hardlinks, always copy
    --hardlinks           opposite of --no-hardlinks
    -s, --[no-]shared     setup as shared repository
    --[no-]recurse-submodules[=<pathspec>]
                          initialize submodules in the clone
    --[no-]recursive[=<pathspec>]
                          alias of --recurse-submodules
    -j, --[no-]jobs <n>   number of submodules cloned in parallel
    --[no-]template <template-directory>
                          directory from which templates will be used
    --[no-]reference <repo>
                          reference repository
    --[no-]reference-if-able <repo>
                          reference repository
    --[no-]dissociate     use --reference only while cloning
    -o, --[no-]origin <name>
                          use <name> instead of 'origin' to track upstream
    -b, --[no-]branch <branch>
                          checkout <branch> instead of the remote's HEAD
    --[no-]revision <rev> clone single revision <rev> and check out
    -u, --[no-]upload-pack <path>
                          path to git-upload-pack on the remote
    --[no-]depth <depth>  create a shallow clone of that depth
    --[no-]shallow-since <time>
                          create a shallow clone since a specific time
    --[no-]shallow-exclude <ref>
                          deepen history of shallow clone, excluding ref
    --[no-]single-branch  clone only one branch, HEAD or --branch
    --[no-]tags           clone tags, and make later fetches not to follow them
    --[no-]shallow-submodules
                          any cloned submodules will be shallow
    --[no-]separate-git-dir <gitdir>
                          separate git dir from working tree
    --[no-]ref-format <format>
                          specify the reference format to use
    -c, --[no-]config <key=value>
                          set config inside the new repository
    --[no-]server-option <server-specific>
                          option to transmit
    -4, --ipv4            use IPv4 addresses only
    -6, --ipv6            use IPv6 addresses only
    --[no-]filter <args>  object filtering
    --[no-]also-filter-submodules
                          apply partial clone filters to submodules
    --[no-]remote-submodules
                          any cloned submodules will use their remote-tracking branch
    --[no-]sparse         initialize sparse-checkout file to include only files at root
    --[no-]bundle-uri <uri>
                          a URI for downloading bundles before fetching from origin remote

(.venv) PS C:\Users\Deepak Babu P K> faultgate --version
faultgate 0.4.1
(.venv) PS C:\Users\Deepak Babu P K> faultgate checks
search_loop      rule   Run ended with no answer at the step budget and most tool calls returned nothing.
abstention       rule   Final answer explicitly says the information could not be found.
policy           rule   A tool call broke the policy: unlisted tool, denied argument pattern, oversized argument, call budget, argument limit, identity mismatch, missing prerequisite, per-value budget, value not allowed, missing required argument, missing confirmation, or (with require_complete) an incomplete run.
repeated_call    rule   Same tool and arguments called >=3 times with identical results.
unrecovered_tool_error rule   A tool call produced a structural error and the tool was never used successfully afterwards.
context_overflow rule   The run hit the context window or output token limit (finish reason or provider error).
wrong_answer     golden Answered, but the expected answer is not in the final answer (needs --golden).
truncation       golden Answer has the head of the expected token but not the whole token (needs --golden).
wrong_direction  judge  Agent searched the dependency chain backwards on a multi-hop task.
outcome          outcome The user's own evaluator marked the scenario failed (needs --outcomes).
'''

### README first example, before cloning

'''
PS C:\Users\Deepak Babu P K> faultgate check examples/traces.json
>> 
note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ
note: wrong_answer skipped — it needs --golden golden.json (expected answers)
note: truncation skipped — it needs --golden golden.json (expected answers)
faultgate: no such file: examples\traces.json
'''

### README first example, after 'git clone and 'cd faultgate'

'''
PS C:\Users\Deepak Babu P K\faultgate> faultgate check examples/traces.json                                      
>> 
note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ
note: wrong_answer skipped — it needs --golden golden.json (expected answers)
note: truncation skipped — it needs --golden golden.json (expected answers)
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow
------------------------------------------------------------------------------------------------------------------------------
fc2cdab304bd  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
6d1f9d67a2d4  ok   1.00         FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
8bf3879339eb  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
3a9e507a0f6d  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
2ab3b6c1e891  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       

2/5 traces failed · search_loop=1, abstention=1, policy=0, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s
'''

### Precheck

'''
PS C:\Users\Deepak Babu P K\faultgate> faultgate precheck examples/formats/langfuse.json --sample 0              
>> 
precheck: OK · format langfuse · checked 1 of 1 traces · 2 tool steps read · 0 error(s), 0 warning(s)
'''

### Policy

'''
PS C:\Users\Deepak Babu P K\faultgate> faultgate check examples/traces.json --policy examples/policy_support.json 
>> 
note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ
note: wrong_answer skipped — it needs --golden golden.json (expected answers)
note: truncation skipped — it needs --golden golden.json (expected answers)
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow
------------------------------------------------------------------------------------------------------------------------------
fc2cdab304bd  FAIL 1.00         ok   1.00         FAIL 1.00         ok   1.00         ok   1.00         ok   1.00       
6d1f9d67a2d4  ok   1.00         FAIL 1.00         FAIL 1.00         ok   1.00         ok   1.00         ok   1.00       
8bf3879339eb  ok   1.00         ok   1.00         FAIL 1.00         ok   1.00         ok   1.00         ok   1.00       
3a9e507a0f6d  ok   1.00         ok   1.00         FAIL 1.00         ok   1.00         ok   1.00         ok   1.00       
2ab3b6c1e891  ok   1.00         ok   1.00         FAIL 1.00         ok   1.00         ok   1.00         ok   1.00       

5/5 traces failed · search_loop=1, abstention=1, policy=5, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.0s
'''

### Baseline and gate

'''
PS C:\dev\test\faultgate> faultgate baseline examples/gate/baseline_glm_run1.json examples/gate/baseline_glm_run2.json --out band.json
>> 
note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ
note: wrong_answer skipped — it needs --golden golden.json (expected answers)
note: truncation skipped — it needs --golden golden.json (expected answers)
examples/gate/baseline_glm_run1.json: 30 traces · clean rate 0.93 · 0.0s
examples/gate/baseline_glm_run2.json: 30 traces · clean rate 0.93 · 0.0s
note: 2 baseline runs measure noise poorly; use 3 or more
band [0.93, 0.93] over 30 scenarios × 2 runs · 26 clean in every run · written to band.json
(.venv) PS C:\dev\test\faultgate> faultgate check examples/gate/candidate_gpt.json --band band.json
>> 
note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ
note: wrong_answer skipped — it needs --golden golden.json (expected answers)
note: truncation skipped — it needs --golden golden.json (expected answers)
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow
------------------------------------------------------------------------------------------------------------------------------
4dc5e933abe8  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
51c15300072b  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
99b74422ab15  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
b6f824a010a7  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
7e74e68d7296  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
c0dd8b5da365  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
10fa2370723e  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
10a63caed2d6  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
04a16662742e  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
b80e27d064fe  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
82ebbe674967  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
ab3503d28cda  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
4d6f5e788fe1  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
5d42e09e02ac  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
3bffa6d137ae  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
316bcde0d931  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
8fd42bacf992  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
8ba08f457b23  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
09a946f2c89d  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
54f099f8147e  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
ac2a7d9eaf68  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
6f508650cff0  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
25465761c097  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
4c78f65e849d  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
8e4ab8196357  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
bd90adcda31f  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
a3131ab0f714  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
ee8fd1f42934  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
6919ae5e42fd  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
a262cc90be4e  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       

18/30 traces failed · search_loop=18, abstention=0, policy=0, repeated_call=0, unrecovered_tool_error=0, context_overflow=0 · judge none · 0.1s
warning: band built from 2 baseline runs; use 3 or more for a stable noise estimate
gate: FAIL · clean rate 0.40 vs band [0.93, 0.93] from 2 baseline runs · fail below 0.83 · p=0.000
regressions (clean in every baseline, not now): r-0208, r-0214, r-0216, r-0224, r-0226, r-0232, r-0258, r-0263, r-0279, r-0286, r-0292, r-0317, r-0320, r-0322, r-0330, r-0344, r-0350
(.venv) PS C:\dev\test\faultgate> echo $LASTEXITCODE
>> 
1
'''

### Golden section

'''
PS C:\dev\test\faultgate> faultgate baseline examples/gate/baseline_glm_run1.json examples/gate/baseline_glm_run2.json --golden examples/gate/golden.json --out band.json
>> 
note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ
examples/gate/baseline_glm_run1.json: 30 traces · clean rate 0.80 · 0.1s
examples/gate/baseline_glm_run2.json: 30 traces · clean rate 0.87 · 0.1s
note: 2 baseline runs measure noise poorly; use 3 or more
band [0.80, 0.87] over 30 scenarios × 2 runs · 21 clean in every run · written to band.json
(.venv) PS C:\dev\test\faultgate> faultgate check examples/gate/candidate_gpt.json --golden examples/gate/golden.json --band band.json
>> 
note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow  wrong_answer      truncation      
------------------------------------------------------------------------------------------------------------------------------------------------------------------
4dc5e933abe8  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
51c15300072b  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
99b74422ab15  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
b6f824a010a7  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
7e74e68d7296  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
c0dd8b5da365  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
10fa2370723e  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
10a63caed2d6  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
04a16662742e  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
b80e27d064fe  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
82ebbe674967  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
ab3503d28cda  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
4d6f5e788fe1  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
5d42e09e02ac  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
3bffa6d137ae  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
316bcde0d931  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
8fd42bacf992  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
8ba08f457b23  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
09a946f2c89d  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
54f099f8147e  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
ac2a7d9eaf68  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
6f508650cff0  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
25465761c097  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
4c78f65e849d  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
8e4ab8196357  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
bd90adcda31f  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
a3131ab0f714  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
ee8fd1f42934  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
6919ae5e42fd  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
a262cc90be4e  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       

21/30 traces failed · search_loop=18, abstention=0, policy=0, repeated_call=0, unrecovered_tool_error=0, context_overflow=0, wrong_answer=3, truncation=3 · judge none · 0.1s
warning: band built from 2 baseline runs; use 3 or more for a stable noise estimate
gate: FAIL · clean rate 0.30 vs band [0.80, 0.87] from 2 baseline runs · fail below 0.70 · p=0.000
regressions (clean in every baseline, not now): r-0214, r-0216, r-0226, r-0258, r-0279, r-0286, r-0292, r-0317, r-0320, r-0322, r-0324, r-0330, r-0332, r-0344, r-0350
(.venv) PS C:\dev\test\faultgate> echo $LASTEXITCODE
>> 
1
(.venv) PS C:\dev\test\faultgate> faultgate check examples/gate/candidate_qwen.json --golden examples/gate/golden.json --band band.json
>> 
note: wrong_direction skipped — it needs a judge (--judge laya | litellm:<model>); see README for each judge's measured κ
trace         search_loop       abstention        policy            repeated_call     unrecovered_tool_error  context_overflow  wrong_answer      truncation      
------------------------------------------------------------------------------------------------------------------------------------------------------------------
4f779ee5d4e0  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
dd645f5dbeb9  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
e922bfa7198f  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
33e90020e857  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
c95027c3cd1a  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
1f708cb49f23  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
0e6b713c4cfd  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
13a3dd5ec657  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
4de4198f4485  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
fb2d58bcf68b  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
782c872960d1  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00       
73a8dcf5ee0c  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
bff95c355acf  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
e01058672d4b  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
62936f53617c  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
e0231bce2c5d  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
df5146080085  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
1e4ef812786e  FAIL 1.00         ok   1.00         ok   1.00         FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
005bd3a507a9  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
3e137b6a973a  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
0a78d74504b4  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
3c15c5db02ef  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
69cf8328f148  FAIL 1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
e5a04fcd3f28  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       
831372f98e14  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
14fba8d79c95  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
310784499cdf  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
ff1801721d91  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
7888b021e126  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00       
461987cf2fc6  ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         ok   1.00         FAIL 1.00         FAIL 1.00       

18/30 traces failed · search_loop=9, abstention=0, policy=0, repeated_call=1, unrecovered_tool_error=0, context_overflow=0, wrong_answer=9, truncation=8 · judge none · 0.1s
warning: band built from 2 baseline runs; use 3 or more for a stable noise estimate
gate: FAIL · clean rate 0.40 vs band [0.80, 0.87] from 2 baseline runs · fail below 0.70 · p=0.000
regressions (clean in every baseline, not now): r-0214, r-0242, r-0258, r-0279, r-0292, r-0307, r-0318, r-0320, r-0324, r-0330, r-0349, r-0350
(.venv) PS C:\dev\test\faultgate> echo $LASTEXITCODE
1
'''

## 4. What worked

Every numeric result I compared matched the README: the 2/5 failures, the band values, the gate verdicts (FAIL at 0.40, PASS at 0.93, FAIL at 0.30 and 0.40 with golden), the clean rates 0.80 and 0.87, and the exit codes. All four trace formats passed `precheck`.


## 5. Problems found

### Problem 1:  the examples need a clone, and the README doesn't say so
create a new virtual environment, run `pip install faultgate`, then run the README's first example, `faultgate check examples/traces.json`.
output: `faultgate: no such file: examples\traces.json`.
Reason:
the `examples/` folder is in the GitHub repo, not in the pip package, and the Install section only says `pip install faultgate`.

### Problem 2: the wildcard example fails on Windows PowerShell (error)
from the repo root in PowerShell, run `faultgate baseline examples/gate/baseline_glm_run*.json --golden examples/gate/golden.json --out band.json`.
output: `faultgate: no such file: examples\gate\baseline_glm_run*.json`, exit code 2.
Reason: I believe the cause is that bash expands '*' before the program sees it, while PowerShell passes it through literally and faultgate does not expand it itself.

### Problem 3: policy failures show no reason in the terminal (confusing)

run `faultgate check examples/traces.json --policy examples/policy_support.json`.
output: all 5 traces show `FAIL` in the `policy` column and no reason. Before this, only 2 of the 5 traces failed any check.
Reason:
I haven't found the reason for this policy failure.

### Small suggestions
- The README shows `echo $?` for the exit code. PowerShell needs `$LASTEXITCODE`.

## 6. Bugs
- "No bugs confirmed. The findings above are documentation issues."

## 7. Three suggestions

1. **Add a Quickstart that includes the clone.** For example: install, `git clone` the repo, `cd faultgate`.
2. **Add a short Windows/PowerShell note**: use `$LASTEXITCODE` instead of `echo $?`.
3. **Explain the output once.** Say what the number next to each result means, what the `skipped` notes mean, and where failure reasons appear. Printing the first reason in the terminal when a policy check fails would remove the main point of confusion.