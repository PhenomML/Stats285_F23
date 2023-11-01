# Homework 4: Visualizations with Tableau

### Downloading Tableau
Download Tableau Prep and Tableau Desktop using the instructions below.
1. Go to https://www.tableau.com/academic/students
2. Click on the "Get Tableau for Free" button.
3. Fill out the form and click on the "Verify Student Status" button.
4. You will receive an email with a license and a link to download Tableau Desktop and Tableau Prep.
5. Download and install Tableau Desktop and Tableau Prep.
6. Open Tableau Desktop and click on the "Activate" button.
7. Enter the license key from the email.
8. You should now be able to use Tableau Desktop and Tableau Prep.

### Connecting to Database
We uploaded a database called "kaggle_survey_2022_responses.csv" to Google Big Query. You can connect to it as follows:
1. In Tableau Prep, find the "Connect To Data" button and click it. In Tableau Desktop, find the "Connect" bar on the left.
   The remaining instructions for connecting to the data are the same in both softwares.
2. In both, scroll to the "To A Server" section and choose "Google Big Query". 
3. If it asks you to download a driver, do it.
4. A pop-up drop-down menu will ask you to choose an Authentication method. Choose "Sign In Using OAuth". Then, click "Sign In".
5. A browser window should pop up. Sign in using your _\<suid\>@stanford.edu email address_.
6. It will ask for Tableau to access your Google account. Click "Allow".
7. Back in Tableau, you should see two dropdown menus in the left bar: "Billing Project" and "Project". 
8. Choose "Stanford-Stats-285-Donoho" for both.
9. Then, you will see a "Dataset" dropdown, choose "Kaggle".
10. Finally, you will see a "Table" dropdown, choose "kaggle_survey_2022_responses".

This should connect you to the database. If you are having trouble, email X.Y. ([xiaoyanh@stanford.edu](xiaoyanh@stanford.edu)) with a screenshot of the error you are getting.

### Homework

You have two options for this homework: A preferred option and a backup option. 
Please spend at least **60 minutes** on the **preferred option** before switching to the backup option, if needed.

* **Preferred Option:** Use Tableau Prep and Tableau Desktop to generate 3 plots similar in style to the Kaggle 2017 
    plots shown in class, but using the "kaggle_survey_2022_responses" dataset.
  * When using Tableau Prep, you can either export your cleaned data as a local file or save it into the cloud database.
    If you choose to save it in the database, please _include your SUID_ in the table name (otherwise, it might get 
    overwritten by someone else's table).
  * For each plot, write a few sentences explaining what the plot shows and what insights we can derive from it about 
    the state of data science in 2022. 
  * Save the Tableau Prep Flow and Tableau Desktop Workbook.

* **Back Up Option:** Replicate the Tableau Prep Flow and Tableau Desktop Workbook that X.Y. created in the 10/30 lecture.
  * In 1-3 paragraphs, explain why the Tableau framework had more "friction" than you expected. Describe what challenges
    and obstacles prevented you from completed the "preferred option" above. What do you think could have been done to 
    reduce the friction? What other tool (ggplot, matplotlib, etc) would you have otherwise used to complete the task?
  * Save the replicated Tableau Prep Flow and Tableau Desktop Workbook.

### Short Answer Questions
Additionally, please answer the following question:

* Have you used ggplot, matplotlib, or seaborn before (in R, Python, or MATLAB)? If so, how does Tableau compare to 
  these tools? If not, what tools have you used for plotting before? How does Tableau compare to these tools?
* What is your preference for data visualization tool now for data visualization (it's okay if it's not Tableau)? Explain why.

### Submission Instructions

Submit the requested write-ups and short answer responses as a PDF on Canvas. Also, submit the Tableau Prep Flow and Tableau
Desktop workbooks you created on Canvas.

