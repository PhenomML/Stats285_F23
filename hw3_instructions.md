# Homework 3. Easing the Pain with Version Control

One of the first rules of code is that it changes. Version control systems have migrated to the center of the server and supercomputer ecosystems. Today's homework is the beginning of showing you how code evolves. We will start with a modest rewriting of HW2 to use functions and embrace associating parameters and observables. Unlike last week though, the code is delivered as a URL to a GitHub repository, [Stats285_hw3](https://github.com/adonoho/Stats285_hw3). Why is this important? Because code written by others changes. This code is going to change. We will be updating it to do the tall and skinny SVD and to write the results to a remote database.

This assignment expects you to already have a free GitHub account.

1. Login to FarmShare.

2. Issue the following command: `git clone https://github.com/adonoho/Stats285_hw3`

3. Change directory to `Stats285_hw3`.

4. Examine the contents; does it look modestly familiar?

5. Execute the same command from last week: `sbatch hw2.sh`, followed by `squeue` .

6. Look at the branches of different code already in this project: `git branch -a`

7. You will see both local and remote branches. On the remote branches, you will see where hw3 will be developed. If you use the GitHub feature to watch the repo, GitHub will email you when it changes.

### Our current status:

Parallel systems are heavily protected on the internet. We originally planned to host a database on Sherlock and get each of you credentials to write your data to the DB and then run the gather phase on your personal laptop. You would use the same code repository on FarmShare and your laptop. Alas, FarmShare codes cannot access Sherlock resources. We are looking at either using a Stanford managed instance of MySQL or a group managed instance of PostgreSQL on GCP. This will all be resolved by Wednesday and the code published on GitHub.
