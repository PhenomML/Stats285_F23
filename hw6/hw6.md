# Homework 6: XGBoost and Weights & Biases

In this homework, you will perform an XYZ experiment in a 
Colaboratory Notebook and log the results to weights and biases.

## Setup

1. Go to [https://wandb.ai/site/research](https://wandb.ai/site/research) 
   and sign up for a free Weights and Biases account using your *Stanford email*.

   (If you don't already have one.)

2. Go to the `XGBoost_demo.ipynb` notebook ([here](https://github.com/adonoho/Stats285_F23/blob/main/hw6/XGBoost_demo.ipynb)) in this folder and click the 
   "Open in Colab" button.

   (This is the demo we did in class.)

3. In colaboratory, sure you are logged into your *Stanford email*.

4. Click "File" -> "Save a copy in Drive" to save a copy of the notebook to your Google Drive.

   (Otherwise, you will not be allowed to save changes.)

## XGBoost

1. Click "File" -> "Save a copy in Drive" to save a copy of the notebook to your Google Drive.

   (Otherwise, you will not be allowed to save changes.)

2. Rename the copied file to `hw6_xgboost.ipynb`.

3. Change the project name in the `wandb.init` call to `stats-285-xgboost` 
   by changing the relevant line to the following:
   ```python
   project="stats-285-xgboost"
   ```

2. In class, we varied the number of `lambda` and `depth` parameters.

   Look through the XGBoost documentation: 
   [https://xgboost.readthedocs.io/en/stable/parameter.html](https://xgboost.readthedocs.io/en/stable/parameter.html)
   #####

3. **XYZ Experiment:** Choose (at least) two *different* parameters than in the original demo. Run an XYZ experiment varying these parameters.
   Your experiment should contain *at least* 50 different runs (trained models).

   ***Note:*** If a parameter has an `alias` name in the documentation, the alias
   name is the one you should use in `model.fit()`. For example, in the demo,
   `lambda` has an alias name of `reg_lambda`, so we passed `reg_lambda = ...` to `model.fit(...)`.

3. **Submit:** For this part, you will need to submit the following:
   * A screenshot of the Weights and Biases dashboard showing this experiment.
   * A copy of the colab notebook you created as a `.ipynb` file. (Use "File" -> "Download .ipynb").
   * A *write up* analyzing the results of your experiment. 
     * Across what settings did you choose to conduct your XYZ experiment? Why?
     * What did you learn from your experiment? 
     * What settings gave the best test accuracy? the best train accuracy?
       Interpret these results.

## CatBoost
1. Click "File" -> "Save a copy in Drive" to save a copy of the notebook to your Google Drive.

   (Otherwise, you will not be allowed to save changes.)

2. Rename the copied file to `hw6_catboost.ipynb`.

3. Change the project name in the `wandb.init` call to `stats-285-catboost` 
   by changing the relevant line to the following:
   ```python
   project="stats-285-catboost"
   ```
   
   4. Follow the instructions in the **XYZ Experiment** and **Submit** sections above, 
      but this time using the CatBoost library instead of XGBoost.

      (You may use any parameters now.)
      ####
      Look at the "CatBoost:Simple Demo" boxes at the end 
      and CatBoost documentation ([https://catboost.ai/docs/concepts/python-reference_parameters-list.html](https://catboost.ai/docs/concepts/python-reference_parameters-list.html))
      to get started.
      ####
      **Clarification:** You are still required to log these CatBoost results to Weights and Biases in the manner that XGBoost was. 

## LightGBM
1. Click "File" -> "Save a copy in Drive" to save a copy of the notebook to your Google Drive.

   (Otherwise, you will not be allowed to save changes.)
2. Rename the copied file to `hw6_lightgbm.ipynb`.

3. Change the project name in the `wandb.init` call to `stats-285-lightgbm` 
   by changing the relevant line to the following:
   ```python
   project="stats-285-lightgbm"
   ```
4. Follow the instructions in the **XYZ Experiment** and **Submit** sections above, 
   but this time using the LightGBM library instead of XGBoost.

   (You may use any parameters now.)
   ####
   LightGBM documentation: [https://lightgbm.readthedocs.io/en/latest/Parameters.html](https://lightgbm.readthedocs.io/en/latest/Parameters.html)
   ####
   **Clarification:** You are still required to log these LightGBM results to Weights and Biases in the manner that XGBoost was.

# Submission on Canvas

On Canvas, submit the following:
* All the screenshots, ipynb-files, write-ups requested in the previous sections.
* Answers to the following short-answer questions:
  * Which library performed the best?
  * Did you notice any differences in the training time?
  * Did you notice any differences in the average and best performance metrics?
  * Which one would you prefer if you were to use it in a real-world application? Why?

All the write-ups and short answers should be combined into a single PDF file.
