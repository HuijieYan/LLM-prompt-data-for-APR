import json
import os
import random
import pandas as pd

stratum_path = "first-stratum"
first_stratum_path = os.listdir(stratum_path)

data = {
    "Project": [],
    "Bug_id": [],
    "1.3.2: Buggy file name": [],
    "1.2.4: Buggy file scope invoked method signature": [],
    "1.2.1: Buggy class declaration": [],
    "1.3.4: Buggy class scope invoked function signature": [],
    "2.1.1: Test code": [],
    "2.1.2: Test file name": [],
    "2.2.1: Error message": [],
    "2.2.2: Error stack trace": [],
    "3.1.1: Github linked issue title": [],
    "3.1.2: Github linked issue description": [],
    "cot: Chain of Thought prompt technique": [],
    "Pass Test": [],
    "result_filename": []
}

for bug_dir in first_stratum_path:
    project_name = bug_dir.rsplit('-', 1)[0]
    bug_id = bug_dir.rsplit('-', 1)[1]

    bug_path = os.path.join(stratum_path, bug_dir)
    result_files = [path for path in os.listdir(bug_path) if "result.json" in path]

    for result_file_name in result_files:
        with open(result_file_name, "r") as result_file:
            result = json.load(result_file)
            pass_test = random.randint(0, 1)

        used_facts = [int(char) for char in result_file_name[:11]]

        data["Project"].append(project_name)
        data["Bug_id"].append(bug_id)
        data["1.3.2: Buggy file name"].append(used_facts[0])
        data["1.2.4: Buggy file scope invoked method signature"].append(used_facts[1])
        data["1.2.1: Buggy class declaration"].append(used_facts[2])
        data["1.3.4: Buggy class scope invoked function signature"].append(used_facts[3])
        data["2.1.1: Test code"].append(used_facts[4])
        data["2.1.2: Test file name"].append(used_facts[5])
        data["2.2.1: Error message"].append(used_facts[6])
        data["2.2.2: Error stack trace"].append(used_facts[7])
        data["3.1.1: Github linked issue title"].append(used_facts[8])
        data["3.1.2: Github linked issue description"].append(used_facts[9])
        data["cot: Chain of Thought prompt technique"].append(used_facts[10])
        data["Pass Test"].append(pass_test)
        data["result_filename"].append(result_file_name)

df = pd.DataFrame(data)
df.to_excel(".", index=False)
