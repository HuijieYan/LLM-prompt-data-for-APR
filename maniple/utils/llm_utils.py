import json
import math
import os
import pickle
import time
import traceback

import openai
import tiktoken
from openai import OpenAI

import ollama

from maniple.utils.misc import print_in_red, print_in_yellow, \
    extract_function_and_imports_from_code_block, find_patch_from_response


use_ollama_flag = os.getenv("USE_OLLAMA", "False").lower() == "true"
use_llama3_flag = os.getenv("USE_LLAMA3", "False").lower() == "true"
if use_ollama_flag:
    openai_client = None
    print('Using ollama backend')

elif use_llama3_flag:
    print('Using llama3 backend')
    base_url = os.getenv("LLAMA3_BASE_URL")
    api_key = os.getenv("LLAMA3_API_KEY")
    openai_client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

else:
    print('Using default openai backend')
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")
    openai_client = OpenAI(api_key=api_key)


def query_LLM(llm_model: str, messages: list, trials: int, temperature=1, seed=42):
    # TODO: extend this function
    if use_ollama_flag:
        return ollama.chat(model=llm_model, messages=messages, keep_alive=True)
    else:
        return openai_client.chat.completions.create(
            model=llm_model,
            messages=messages,
            n=trials,
            temperature=temperature,
            seed=seed
        )


def get_and_save_response_with_fix_path(prompt: str, llm_model: str, actual_group_bitvector: str, database_dir: str,
                                        project_name: str, bug_id: str, trial: int, data_to_store: dict,
                                        start_index: int, permutation: str = None) -> dict:
    bug_dir = os.path.join(database_dir, project_name, bug_id)
    output_dir: str = os.path.join(database_dir, project_name, bug_id, actual_group_bitvector)

    if permutation is not None:
        output_dir = os.path.join(output_dir, permutation)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    require_generation = False
    for index in range(trial):
        file_index = index + start_index
        response_md_file_name = "response_" + str(file_index) + ".md"
        response_md_file_path = os.path.join(output_dir, response_md_file_name)

        if not os.path.exists(response_md_file_path):
            require_generation = True
            break

        with open(response_md_file_path, "r", encoding="utf-8") as response_md_file:
            previous_response = response_md_file.read()

        if previous_response == "":
            print_in_red(f"Detect empty previous response {project_name}:{bug_id}:{actual_group_bitvector}:{file_index}. Regenerate")
            require_generation = True
            break

    if not require_generation:
        print_in_yellow(f"Skip {project_name}:{bug_id}:{actual_group_bitvector}: all responses already generated")
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

    with open(os.path.join(bug_dir, "static-dynamic-facts.json"), "r") as bug_data_file:
        bug_data: dict = next(iter(json.load(bug_data_file).values()))
        user_dir: str = list(bug_data)[0]
        buggy_function_name: str = bug_data[user_dir]["buggy_functions"][0]["function_name"]
        buggy_function_start_line: str = bug_data[user_dir]["buggy_functions"][0]["start_line"]
        # buggy_function_source_code: str = bug_data[user_dir]["buggy_functions"][0]["function_code"]

        prefix = f"{project_name}_{bug_id}"
        start_idx = user_dir.find(prefix) + len(prefix) + 1
        buggy_location_file_name = user_dir[start_idx:]

    responses = None
    try:
        responses = LLMConnection().get_response_with_fix_path(prompt, llm_model, trial, buggy_function_name)
    except QueryException as error:
        error_str = str(error)
        print_in_yellow(error_str)
    except Exception as error:
        error_str = str(error)
        print_in_red(error_str)
        traceback.print_exc()

    for index in range(trial):
        file_index = index + start_index
        response_md_file_name = "response_" + str(file_index) + ".md"
        response_json_file_name = "response_" + str(file_index) + ".json"

        response_md_file_path = os.path.join(output_dir, response_md_file_name)
        response_json_file_path = os.path.join(output_dir, response_json_file_name)

        if responses is not None:
            response = responses["responses"][index]

            with open(response_md_file_path, "w", encoding='utf-8') as md_file:
                md_file.write(response["response"])

            with open(response_json_file_path, "w", encoding='utf-8') as json_file:
                test_data = {
                    "bugID": int(bug_id),
                    "start_line": buggy_function_start_line,
                    "file_name": buggy_location_file_name,
                    "replace_code": response["replace_code"],
                    "import_list": response["import_list"]
                }

                if data_to_store is not None:
                    test_data = {**data_to_store, **test_data}

                test_input_data = {
                    project_name: [test_data]
                }
                json.dump(test_input_data, json_file, indent=4)

        else:
            with open(response_md_file_path, "w", encoding='utf-8') as md_file:
                md_file.write(error_str)

            with open(response_json_file_path, "w", encoding='utf-8') as json_file:
                test_data = {
                    "bugID": int(bug_id),
                    "start_line": buggy_function_start_line,
                    "file_name": buggy_location_file_name,
                    "replace_code": None,
                    "import_list": []
                }

                if data_to_store is not None:
                    test_data = {**data_to_store, **test_data}

                test_input_data = {
                    project_name: [test_data]
                }
                json.dump(test_input_data, json_file, indent=4)

            print_in_yellow(f"write response error to {response_md_file_path}")

    if responses is not None:
        completion_file_path = os.path.join(output_dir, "raw_data.pkl")

        with open(completion_file_path, 'wb') as completion_file:
            pickle.dump((responses["prompt_messages"], responses["response_completions"]), completion_file)

        return responses["total_token_usage"]

    else:
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }


class LLMConnection:
    def __init__(self):
        self.max_generation_count = 3
        # self.max_conversation_count = 3
        self.buggy_function_name = ""

    def get_response_with_fix_path(self, prompt: str, llm_model: str, trial: int, buggy_function_name: str) -> dict:
        self.max_generation_count = 3
        self.buggy_function_name = buggy_function_name

        messages = [{"role": "user", "content": prompt}]

        responses = self.get_response_with_valid_patch(messages, llm_model, trial)

        if len(responses["responses"]) < trial:
            for _ in range(trial - len(responses["responses"])):
                responses["responses"].append({
                    "response": "Run out of generation count",
                    "fix_patch": None,
                    "replace_code": None,
                    "import_list": []
                })

        assert len(responses["responses"]) == trial

        return responses

    def get_response_with_valid_patch(self, messages: list, llm_model: str, trial: int) -> dict:
        start_time = time.time()

        responses = _get_responses_from_messages(messages, llm_model, math.ceil(trial * 1.5))
        responses["prompt_messages"] = messages
        responses["responses"] = [{"response": value} for value in responses["responses"] if find_patch_from_response(value, self.buggy_function_name) is not None]

        while self.max_generation_count > 0:
            if len(responses["responses"]) >= trial:
                responses["responses"] = responses["responses"][:trial]

                for response in responses["responses"]:
                    fix_patch = find_patch_from_response(response["response"], self.buggy_function_name)
                    response["fix_patch"] = fix_patch
                    replace_code, import_list = extract_function_and_imports_from_code_block(fix_patch, self.buggy_function_name)
                    response["replace_code"] = replace_code
                    response["import_list"] = import_list

                end_time = time.time()
                if end_time - start_time > 60:
                    print_in_red(f"long time for generation")
                    print(end_time - start_time)

                return responses

            self.max_generation_count -= 1

            next_query_responses = _get_responses_from_messages(messages, llm_model, trial)
            next_query_responses["responses"] = [{"response": value} for value in next_query_responses["responses"] if find_patch_from_response(value, self.buggy_function_name) is not None]
            responses["total_token_usage"] = combine_token_usage(responses["total_token_usage"], next_query_responses["total_token_usage"])

            if len(next_query_responses["responses"]) > 0:
                responses["responses"] = responses["responses"] + next_query_responses["responses"]
                responses["response_completions"] = responses["response_completions"] + next_query_responses["response_completions"]

        if len(responses["responses"]) > 0:
            print_in_yellow(f"Tried 3 times still fail to get enough responses")
            responses["responses"] = responses["responses"][:trial]

            for response in responses["responses"]:
                fix_patch = find_patch_from_response(response["response"], self.buggy_function_name)
                response["fix_patch"] = fix_patch
                replace_code, import_list = extract_function_and_imports_from_code_block(fix_patch, self.buggy_function_name)
                response["replace_code"] = replace_code
                response["import_list"] = import_list

            return responses

        elif len(responses["responses"]) == 0:
            responses["responses"] = []
            return responses


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def combine_token_usage(usage_1, usage_2) -> dict:
    if not isinstance(usage_1, dict):
        usage_1 = {
            "prompt_tokens": usage_1.prompt_tokens,
            "completion_tokens": usage_1.completion_tokens,
            "total_tokens": usage_1.total_tokens
        }

    if not isinstance(usage_2, dict):
        usage_2 = {
            "prompt_tokens": usage_2.prompt_tokens,
            "completion_tokens": usage_2.completion_tokens,
            "total_tokens": usage_2.total_tokens
        }

    return {
        "prompt_tokens": usage_1["prompt_tokens"] + usage_2["prompt_tokens"],
        "completion_tokens": usage_1["completion_tokens"] + usage_2["completion_tokens"],
        "total_tokens": usage_1["total_tokens"] + usage_2["total_tokens"]
    }


def get_responses_from_messages(messages: list, llm_model: str, trial: int, retry_max_count: int = 4, default_safe: bool = False, temperature: float = 1.0) -> dict:
    responses = _get_responses_from_messages(messages, llm_model, math.ceil(trial * 1.5), temperature=temperature)
    responses["prompt_messages"] = messages

    while retry_max_count > 0:
        retry_max_count -= 1

        if len(responses["responses"]) >= trial:
            responses["responses"] = responses["responses"][:trial]
            return responses

        next_query_responses = _get_responses_from_messages(messages, llm_model, trial, temperature=temperature)
        responses["responses"] = responses["responses"] + next_query_responses["responses"]
        responses["response_completions"] = responses["response_completions"] + next_query_responses["response_completions"]
        responses["total_token_usage"] = combine_token_usage(responses["total_token_usage"], next_query_responses["total_token_usage"])

    if default_safe:
        return responses

    else:
        raise QueryException(f"Tried {str(retry_max_count)} times still fail to get enough responses")


def _get_responses_from_messages(messages: list, llm_model: str, trial: int, temperature: float = 1.0) -> dict:
    for message in messages:
        num_tokens = num_tokens_from_string(message["content"], "cl100k_base")

        if use_llama3_flag and num_tokens > 8192:
            raise QueryException(f"{num_tokens} exceed maximum 8192 token size")

        elif num_tokens > 16385:
            raise QueryException(f"{num_tokens} exceed maximum 16385 token size")

    responses = {
        "responses": [],
        "response_completions": [],
        "total_token_usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

    retry_count = 3

    while retry_count > 0:
        try:
            time.sleep(0.1)

            # TODO replace this with ollama, make the function more generic
            chat_completion = query_LLM(llm_model, messages, trial, temperature=temperature)

            for choice in chat_completion.choices:
                finish_reason = choice.finish_reason
                if finish_reason == "length":
                    raise QueryException("Exceed model maximum token size")

                if finish_reason != "stop":
                    print_in_yellow(f"drop 1 response due to not stop, finish reason: {finish_reason}")
                    continue

                if choice.message.content != "":
                    responses["responses"].append(choice.message.content)

            responses["response_completions"].append(chat_completion)

            if openai_client is not None:
                responses["total_token_usage"] = chat_completion.usage
            else:
                responses["total_token_usage"] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }

            break

        except openai.RateLimitError:
            print_in_yellow("Meet ratelimit error, wait for 5 seconds")
            time.sleep(10)
            retry_count -= 1

    return responses


def get_responses_from_prompt(prompt: str, model: str, trial: int, temperature: float = 1.0) -> dict:
    messages = [{"role": "user", "content": prompt}]

    return get_responses_from_messages(messages, model, trial, temperature=temperature)


class QueryException(Exception):
    pass
