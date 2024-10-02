# This is largely based on GEMBA-MQM: https://github.com/MicrosoftTranslator/GEMBA/blob/main/gemba_mqm.py

import pandas as pd
from llm_fewshot_examples import TEMPLATE_GEMBA_CONTEXT_MQM_1shot
from openai import OpenAI
from collections import defaultdict
import argparse
import os

lang_dict={
    "en": "English",
    "de": "German"
}

def apply_template(template, data):
    if isinstance(template, str):
        return template.format(**data)
    elif isinstance(template, list):
        prompt = []
        for conversation_turn in template:
            p = conversation_turn.copy()
            p['content'] = p['content'].format(**data)
            prompt.append(p)
        return prompt
    else:
        raise ValueError(f"Unknown template type {type(template)}")

def get_bilingual_context(df, doc_id, seg_id, k):
  context_text = []
  for con_seg_id in range(max(0, seg_id-k), seg_id):
    row = df[(df["doc_id"]==doc_id) & (df["segment_id"]==con_seg_id)].values
    assert len(row)==1
    context_text.append(f"{row[0][4]} ({row[0][2]}): {row[0][-2]}")
  return ("\n").join(context_text)

def get_response(client, prompt):
  parameters = {
              "temperature": 0,
              "max_tokens": 100,
              "top_p": 1,
              "n": 1,
              "frequency_penalty": 0,
              "presence_penalty": 0,
              "stop": None,
              "model": "gpt-4",
              "messages": prompt,
          }
  response = client.chat.completions.create(**parameters)
  return response.choices[0].message.content.strip()

def parse_error_class(error):
    # parse error from error description, errors are ['accuracy', 'fluency', 'locale convention', 'style', 'terminology', 'non-translation', 'other']
    #  locale convention (currency, date, name, telephone, or time format), style (awkward), terminology (inappropriate for context, inconsistent use),
    class_name = "unknown"
    if "accuracy" in error:
        class_name = "accuracy"
        for subclass in ["addition", "mistranslation", "omission", "untranslated text"]:
            if subclass in error:
                class_name = f"accuracy-{subclass}"
    elif "fluency" in error:
        class_name = "fluency"
        for subclass in ["character encoding", "grammar", "inconsistency", "punctuation", "register", "spelling"]:
            if subclass in error:
                class_name = f"fluency-{subclass}"
    elif "locale convention" in error:
        class_name = "locale convention"
        for subclass in ["currency", "date", "name", "telephone", "time"]:
            if subclass in error:
                class_name = f"locale convention-{subclass}"
    elif "style" in error:
        class_name = "style"
    elif "terminology" in error:
        class_name = "terminology"
        for subclass in ["inappropriate", "inconsistent"]:
            if subclass in error:
                class_name = f"terminology-{subclass}"
    elif "non-translation" in error:
        class_name = "non-translation"
    elif "other" in error:
        class_name = "other"

    return class_name

def parse_mqm_answer(x, full_desc=True):
    if x is None:
        return None

    x = str(x)
    if x.startswith('{"improved translation"'):
      print("here")
    else:
        x = x.lower()
        errors = {'critical': [], 'major': [], 'minor': []}
        error_level = None
        for line in x.split('\n'):
            line = line.strip()
            if "no-error" in line or "no error" in line or "no errors" in line or "" == line:
                continue
            if "critical:" == line:
                error_level = "critical"
                continue
            elif "major:" == line:
                error_level = "major"
                continue
            elif "minor:" == line:
                error_level = "minor"
                continue

            if "critical" in line or "major" in line or "minor" in line:
                if not any([line.startswith(x) for x in ['accuracy', 'fluency', 'locale convention', 'style', 'terminology', 'non-translation', 'other']]):
                    print(line)

            if error_level is None:
                print(f"No error level for {line}")
                continue

            if "non-translation" in line:
                errors["critical"].append(line)
            else:
                errors[error_level].append(line)

    error_classes = defaultdict(list)
    final_score = 0
    error_counter = {'critical':0, 'major':0, 'minor':0}
    for error_level in ['critical', 'major', 'minor']:
        if error_level not in errors:
                continue
        for error in errors[error_level]:
            final_score += 10 if error_level == 'critical' else 5 if error_level == 'major' else 1
            error_counter[error_level] += 1

            if full_desc:
                error_classes[error_level].append(error)
            else:
                class_name = parse_error_class(error)
                error_classes[error_level].append(class_name)

    # We remove this for chat data as human annotations were collected without this constraint unlike other WMT tasks
    # if final_score > 25:
    #     final_score = 25

    return pd.Series([-final_score, error_counter['critical'], error_counter['major'], error_counter['minor']])

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lp", type=str, default="en-de")
    parser.add_argument("--model_name", type=str,  default="gpt-4o-mini")
    parser.add_argument("--tgt_col", default="submission_unbabel+it", type=str)
    parser.add_argument("--context_size", type=int, default=8)
    args = parser.parse_args()
    return args

def main(args):
    credentials = {
        "deployments": {args.model_name: args.model_name},
        "api_key": "", # add api-key
        "requests_per_second_limit": 1,
        "organization": "", # add org-key
    }

    client = OpenAI(api_key=credentials["api_key"],
                    organization=credentials['organization'],)

    dfs_all = pd.read_csv(f"all_submissions/{args.lp}-scores.csv", index_col=None)
    dfs_all["src_len"] = dfs_all["source"].apply(lambda x: len(x.split(" ")))

    dfs_all["sender"] = dfs_all["sender"].replace("agent", "Agent")
    dfs_all["sender"] = dfs_all["sender"].replace("customer", "Customer")


    dfs_all["lp"] = dfs_all['source_language'] + "_" +  dfs_all['target_language'] 

    all_df = []
    for _, gr_df in dfs_all.groupby("doc_id"):
        gr_df["segment_id"] = list(range(0, len(gr_df)))
        all_df.append(gr_df)
    dfs_all = pd.concat(all_df)
    
    dfs_all["source_language"] = dfs_all["source_language"].apply(lambda x: lang_dict[x])
    dfs_all["target_language"] = dfs_all["target_language"].apply(lambda x: lang_dict[x])

    dfs_all.rename(columns={'source': 'source_seg',
                            f'{args.tgt_col}': 'target_seg',
                            'source_language': 'source_lang',
                            'target_language': 'target_lang'}, inplace=True)

    dfs_all = dfs_all[["doc_id", "segment_id", "source_lang", "target_lang", "sender", 'source_seg', 'target_seg', "lp"]]

    context = []
    for _, row in dfs_all.iterrows():
        if row['segment_id'] == 0:
            context.append('')
        else:
            context.append(get_bilingual_context(dfs_all, row["doc_id"], row["segment_id"], args.context_size))

    dfs_all["context"] = context
    dfs_all["context_prompt"] = dfs_all.apply(lambda x: apply_template(TEMPLATE_GEMBA_CONTEXT_MQM_1shot, x), axis=1)

    dfs_all[f"{args.model_name}-result"] = dfs_all["context_prompt"].apply(lambda x: get_response(client, x))
    dfs_all[[f"{args.model_name}-score", f"{args.model_name}-critical-count", f"{args.model_name}-major", f"{args.model_name}-minor"]] = dfs_all[f"{args.model_name}-result"].apply(parse_mqm_answer)

    dfs_all.to_csv(f"{args.model_name}/{args.lp}-{args.tgt_col}.csv", index=None)


if __name__ == "__main__":
    args = get_args()
    main(args)