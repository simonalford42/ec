# Dissection for analyzing the phrase tables
import os
from collections import defaultdict

example_logos = {
    "a medium 6 gon",
    "a medium 7 gon",
    "a small 9 gon",
    
    "4 small square s in a row",
    "6 small 5 gon s in a row",
    "5 medium semicircle s in a row",
    
    "3 concentric square s",
    "2 concentric circle s",
    "8 concentric circle s",
    
    "a 4 stepped staircase_copy_0",
    "a 7 stepped staircase",
    "a 4 stepped zigzag",
    "a 5 stepped zigzag",
    
    "a small triangle connected by a big line to a medium triangle",
    "a small circle next to a small 6 gon",
    "a small 9 gon next to a medium square",
    
    "8 sided snowflake with a small triangle as arms",
    "7 sided snowflake with a short line and a small 5 gon as arms",
    "5 sided snowflake with a short line and a medium circle as arms",
    "7 sided snowflake with a short space and a short line and a short space and a small 5 gon as arms",
    "6 sided snowflake with a short space and a short line and a short space and a medium semicircle as arms",
}
def get_example_tasks(frontiers, max_translations, max_tasks):
    top_tokens = defaultdict(list)    
    for f in frontiers:
        for e in frontiers[f].entries:
            ml_tokens = e.tokens
            for ml_token in ml_tokens:
                if ml_token in max_translations:
                    for (word, _) in max_translations[ml_token]:
                        if word in f.name:
                            if len(top_tokens[ml_token]) < max_tasks:
                                if f.name not in top_tokens[ml_token]:
                                    top_tokens[ml_token].append(f.name)
    # top_tokens = defaultdict(list)    
    # for f in frontiers:
    #     if f.name in examples:
    #         print("_".join(f.name.split())) # So we can find it
    #         for e in  frontiers[f].entries:
    #             tokens = e.tokens
    #             for t in tokens:
    #                 top_tokens[t].append(f.name)
    return top_tokens
    
def read_alignments(prefix):
    fn = os.path.join(prefix, "phrase-table")
    with open(fn, 'r') as f:
        lines = [l.strip().split(' ||| ') for l in f.readlines()]

    all_alignments = [(program, word, float(p)) for (program, word, p) in lines]
    # Print top-ranked distributions.
    global_sorted = sorted(all_alignments, key=lambda v: v[-1], reverse = True)
    # for (program, word, p) in global_sorted:
    #     print(f"p({program} | '{word}') = {p}")
    
    alignments_per_word = defaultdict(list)
    for (program, word, p) in global_sorted:
        alignments_per_word[word].append((program, p))
    
    return alignments_per_word
        
def get_max_probability_translations(phrase_prefix, grammar, max_n=5):
    """Get the maximum probability token translations"""
    escaped_to_original = {str(v) : k for (k, v) in grammar.original_to_escaped.items()}
    
    alignments_per_word = read_alignments(phrase_prefix)
    max_probability_translations = defaultdict(list)
    for word in alignments_per_word:
        for (token, p) in sorted(alignments_per_word[word], key = lambda a:a[-1], reverse = True)[:max_n]:
            if token in escaped_to_original:
                token = escaped_to_original[token]
            max_probability_translations[token].append((word, p))
    return max_probability_translations




# Loads language for tasks
def languageForTasks(languageDataset, languageDatasetDir, taskDict):
    """
    Loads a language dataset from {languageDatasetDir}/{languageDataset}.
    taskDict: {task_name : []}
    
    If not using the backward compatible languageForPathNameTasks, this assumes there are {train, test} splits, and loads a separate vocabulary for each one.
    taskDict fully determines all the tasks we will load, and does not obey train/test splits.
    Returns {task_name : list of sentences for each task, for the tasks in the taskDict.}
    
    """
    if type(languageDataset) is not list:
        languageDataset = [languageDataset]
        
    import os
    import json
    if 'path' in languageDataset[0]:
        return languageForPathNameTasks(languageDataset, languageDatasetDir, taskDict)
    
    vocabularies = {"train": set(), "test": set()}
    from pathlib import Path
    for dataset in languageDataset:
        dataset_path = os.path.join(languageDatasetDir, dataset)
        for split in ("train", "test"):
            try:
                split_path = os.path.join(dataset_path, split)
                with open(os.path.join(split_path, "language.json"), 'rb') as f:
                    languageData = json.load(f)
                    for t_name in taskDict:
                        if t_name in languageData:
                            taskDict[t_name] = languageData[t_name]
                with open(os.path.join(split_path, "vocab.json"), 'rb') as f:
                    vocabularies[split].update(json.load(f))
            except:
                print(f"Not found: dataset for {split_path}")
                continue
    
    for k in vocabularies:
        vocabularies[k] = sorted(list(vocabularies[k]))

    print("Found language for {}/{} tasks".format(len([t for t in taskDict if len(taskDict[t]) > 0]), len(taskDict)))
    print(f"Found vocabularies of n=[{len(vocabularies['train'])}] for train and n=[{len(vocabularies['test'])}] for test.")
    
    return taskDict, vocabularies
    
def languageForPathNameTasks(languageDataset, taskDict):
    """
    Backwards compatability with language datasets that were keyed by a stimuli path name.
    """
    import json
    import os.path as osp
    
    with open(languageDataset, 'r') as f:
        languageDataset = json.load(f)
    
    def extract_task_name(task_path):
        return osp.basename(task_path).split('name_')[-1].split('.')[0]
    languageDataset = {
        extract_task_name(task_path) : [data[0] for data in languageData]
        for (task_path, languageData) in languageDataset.items()
    }
    
    def task_to_safe_name(task_name): 
        return task_name.replace("=","_").replace(' ','_').replace('/','_').replace("-","_").replace(")","_").replace("(","_")
    
    # Check for collisions in safe name.
    from collections import defaultdict
    task_safe_names = defaultdict(list)
    for t in taskDict:
        task_safe_names[task_to_safe_name(task_name )].append(task_name)
        
    languageForTasks = {}
    for t in taskDict:
        task_safe_name = task_to_safe_name(task_name)
        if task_safe_name not in languageDataset or len(languageDataset[task_safe_name]) < 1:
            print("Missing language for : {}".format(task_name))
        if len(task_safe_names[task_safe_name]) > 1:
            print("Collision: safe-name: {}, names: {}".format(task_safe_name, task_safe_name[task_safe_name]))
        language_for_task = languageDataset[task_safe_name] if task_safe_name in languageDataset else []
        languageForTasks[t] = language_for_task
    print("Found language for {}/{} tasks".format(len([t for t in languageForTasks if len(languageForTasks[t]) > 0]), len(languageForTasks)))
    return languageForTasks, None
        
    