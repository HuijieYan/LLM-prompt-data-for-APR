Please fix the buggy function provided below and output a corrected version.
Following these steps:
1. Analyze the buggy function and its relationship with corresponding error message, the expected input/output values, the GitHub issue.
2. Identify potential error locations within the buggy function.
3. Explain the cause of the bug using the buggy function, the corresponding error message, the expected input/output variable values, the GitHub Issue information.
4. Suggest a strategy for fixing the bug.
5. Given the buggy function below, provide a corrected version. The corrected version should pass the failing test, satisfy the expected input/output values, resolve the issue posted in GitHub.


Assume that the following list of imports are available in the current environment, so you don't need to import them when generating a fix.
```python
from thefuck.specific.git import git_support
```

## The source code of the buggy function
```python
# The relative path of the buggy file: thefuck/rules/git_fix_stash.py

# this is the buggy function you need to fix
@git_support
def match(command):
    return (command.script.split()[1] == 'stash'
            and 'usage:' in command.stderr)

```

### The error message from the failing test
```text
def test_not_match():
>       assert not match(Command("git", stderr=git_stash_err))

tests/rules/test_git_fix_stash.py:27: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
<decorator-gen-8>:2: in match
    ???
thefuck/specific/git.py:32: in git_support
    return fn(command)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

command = Command(script=git, stdout=, stderr=
usage: git stash list [<options>]
   or: git stash show [<stash>]
   or: git stas... [-k|--[no-]keep-index] [-q|--quiet]
		       [-u|--include-untracked] [-a|--all] [<message>]]
   or: git stash clear
)

    @git_support
    def match(command):
>       return (command.script.split()[1] == 'stash'
                and 'usage:' in command.stderr)
E       IndexError: list index out of range

thefuck/rules/git_fix_stash.py:8: IndexError

```



## Expected values and types of variables during the failing test execution
Each case below includes input parameter values and types, and the expected values and types of relevant variables at the function's return. If an input parameter is not reflected in the output, it is assumed to remain unchanged. A corrected function must satisfy all these cases.

### Expected case 1
#### The values and types of buggy function's parameters
command.script, expected value: `'git'`, type: `str`

command, expected value: `Command(script=git, stdout=, stderr=
usage: git stash list [<options>]
   or: git stash show [<stash>]
   or: git stash drop [-q`, type: `Command`

command.stderr, expected value: `'\nusage: git stash list [<options>]\n   or: git stash show [<stash>]\n   or: git stash drop [-q`, type: `str`

#### Expected values and types of variables right before the buggy function's return
splited_script, expected value: `['git']`, type: `list`



## A GitHub issue for this bug

The issue's title:
```text
git_fix_stash rule fails when script is just git
```

The issue's detailed description:
```text
thefuck master 🔧  git
usage: git [--version] [--help] [-C <path>] [-c name=value]
           [--exec-path[=<path>]] [--html-path] [--man-path] [--info-path]
           [-p|--paginate|--no-pager] [--no-replace-objects] [--bare]
           [--git-dir=<path>] [--work-tree=<path>] [--namespace=<name>]
           <command> [<args>]

The most commonly used git commands are:
   add        Add file contents to the index
   bisect     Find by binary search the change that introduced a bug
   branch     List, create, or delete branches
   checkout   Checkout a branch or paths to the working tree
   clone      Clone a repository into a new directory
   commit     Record changes to the repository
   diff       Show changes between commits, commit and working tree, etc
   fetch      Download objects and refs from another repository
   grep       Print lines matching a pattern
   init       Create an empty Git repository or reinitialize an existing one
   log        Show commit logs
   merge      Join two or more development histories together
   mv         Move or rename a file, a directory, or a symlink
   pull       Fetch from and integrate with another repository or a local branch
   push       Update remote refs along with associated objects
   rebase     Forward-port local commits to the updated upstream head
   reset      Reset current HEAD to the specified state
   rm         Remove files from the working tree and from the index
   show       Show various types of objects
   status     Show the working tree status
   tag        Create, list, delete or verify a tag object signed with GPG

'git help -a' and 'git help -g' lists available subcommands and some
concept guides. See 'git help <command>' or 'git help <concept>'
to read about a specific subcommand or concept.
thefuck master 🗡  fuck
[WARN] Rule git_fix_stash:
Traceback (most recent call last):
  File "/usr/local/lib/python3.4/dist-packages/thefuck/types.py", line 211, in is_match
    if compatibility_call(self.match, command):
  File "/usr/local/lib/python3.4/dist-packages/thefuck/utils.py", line 224, in compatibility_call
    return fn(*args)
  File "<string>", line 2, in match
  File "/usr/local/lib/python3.4/dist-packages/thefuck/specific/git.py", line 32, in git_support
    return fn(command)
  File "/usr/local/lib/python3.4/dist-packages/thefuck/rules/git_fix_stash.py", line 8, in match
    return (command.script.split()[1] == 'stash'
IndexError: list index out of range
----------------------------
```



