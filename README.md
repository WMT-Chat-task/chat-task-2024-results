This repositoy includes the **automatic evaluation** results of the WMT 2024 chat shared task submissions.

The results are presented in excel sheets with **one sheet per language pair**. It includes the following:

- **``results.xlsx``**: results of COMET-22, BLEU, ChrF and Contextual-COMET-QE metrics. Systems are ranked based on the COMET-22 score.
  
- **``results_muda.xlsx``**: precision, recall and F1 accuracy scores for different discourse phenomena. Systems are ranked based on F1 score.

- **``results_human.xlsx``**: sentence and document-level results based on human evaluation.

- **``generate_results.ipynb``**: scripts to reproduce the automatic evaluation results.

- **``generate_human_ranks.ipynb``**: scripts to reproduce the human evaluation results.

-  **``test``**: test data with references.

-  **``all_submissions``**: main submissions of all teams grouped by language pair.

-  **``human_eval``**: raw human evaluation data for all language pairs.
