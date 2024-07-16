from typing import Literal
from pathlib import Path
from maniple.llm.LLMConnection import LLMConnection, ModelType, PlatformType
from maniple.llm.PromptGenerator import PromptGenerator
from maniple.utils.misc import find_patch_from_response
import json, os

class ManipleDataAdaptor(LLMConnection):
    def __init__(self, 
                 data_dir: str, 
                 patch_dir: str, 
                 dataset: Literal['BGP314', 'BGP32'],
                 platform: PlatformType,
                 model: ModelType,
                 endpoint_url: str = '',
                 trial=1):
        
        api_key = os.getenv('api-key', '')
        
        super().__init__(
            platform=platform,
            model=model,
            api_key=api_key,
            endpoint_url=endpoint_url,
            trial=trial,
            max_concurrent_requests=10,
            max_generation_count=3,
            log_file='llm_connection.log'
        )

        self.__dataset = dataset

        self.__data_dir_path = Path(data_dir)
        self.__patch_dir_path = Path(patch_dir)

        template_file = Path(data_dir) / 'prompt_template.json'
        self.__template = json.loads(template_file.read_text())

        bitvectors_file = Path(data_dir) / 'stratas.json'
        self.__bitvectors = json.loads(bitvectors_file.read_text())

    def generate_patch(self, project_name: str, bug_id: str, use_prompt_file=False):
        print(f'processing {project_name}:{bug_id}')
        patch_path = self.__patch_dir_path / project_name / bug_id

        for bitvector in self.__bitvectors.keys():
            bitvector_path: Path = patch_path / bitvector
            bitvector_path.mkdir(parents=True, exist_ok=True)

            prompt_file = bitvector_path / 'prompt.md'
            if use_prompt_file:
                prompt = prompt_file.read_text()
            else:
                prompt = self.__generate_prompt(project_name, bug_id, bitvector)
                prompt_file.write_text(prompt)

            responses = self.chat(prompt, f'bugid={project_name}:{bug_id},bitvector={bitvector}')
            for idx, res in enumerate(responses):
                response_file = bitvector_path / f'response_{idx+1}.md'
                response_file.write_text(res[0])

    def __generate_prompt(self, project_name: str, bug_id: str, bitvector: str) -> str:
        bug_data_path = self.__data_dir_path / 'bug-data' / project_name / bug_id
        with open(bug_data_path / 'processed-facts.json', 'r') as f:
            processed_facts = json.load(f)

        with open(bug_data_path / 'static-dynamic-facts.json', 'r') as f:
            static_dynamic_facts = json.load(f)

        gen = PromptGenerator(
            project_name=project_name,
            bug_id=bug_id,
            facts=processed_facts,
            static_dynamic_facts=static_dynamic_facts,
            strata_bitvector=self.__bitvectors[bitvector],
            prompt_template=self.__template
        )

        self.__buggy_function_name = gen.buggy_function_name

        prompt = gen.get_prompt().strip()

        return prompt
    
    def generate_and_write_all_prompt(self):
        if self.__dataset == 'BGP32':
            with open(self.__data_dir_path / 'datasets-list/BGP32.json') as f:
                bugids = json.load(f)
        elif self.__dataset == 'BGP314':
            with open(self.__data_dir_path / 'datasets-list/BGP314.json') as f:
                bugids = json.load(f)
        
        for project_name, ids in bugids.items():
            for id in ids:
                print(f'generate prompt for {project_name}:{id}')
                for bitvector in self.__bitvectors.keys():
                    folder_path: Path = self.__patch_dir_path / project_name / str(id) / bitvector
                    folder_path.mkdir(parents=True, exist_ok=True)
                    prompt = self.__generate_prompt(project_name, str(id), bitvector)
                    prompt_file_path: Path = folder_path / 'prompt.md'
                    prompt_file_path.write_text(prompt)
    
    def process_response(self, response: str) -> str | None:
        return find_patch_from_response(response, self.__buggy_function_name)


if __name__ == "__main__":
    
    connection = ManipleDataAdaptor(
        data_dir='experiment-data',
        patch_dir='test_patches',
        dataset='BGP32',
        platform='DeepInfra',
        model='meta-llama/Meta-Llama-3-8B-Instruct',
        endpoint_url='https://api.deepinfra.com/v1/openai',
        trial=1
    )
    connection.generate_and_write_all_prompt()
    connection.close()
