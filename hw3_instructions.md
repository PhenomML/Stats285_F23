# Homework 3. Easing the Pain with Version Control

Modern use of computers generally involves distributing code to many different nodes on the internet. So far we were logging in to each node and sending code by manual copying. This model doesn’t scale. Instead, we will introduce a method of code distribution using an internet resource — [GitHub](https://github.com).  Getting introduced to `git` and GitHub will have other advantages for us, down the road. The model we will introduce is widely used. 

1. In course readings on canvas, find the github folder. In the history of “git” article, what is claimed to be Linus Torvalds reason for the name “git”. Who does Linus Torvalds credit as the project lead for “git”? Why did Torvalds think that he needed to design and start “git”? What is the relation between “git” and Linux? What is the relation between Linux and “the cloud”? What is the relation between “git” and “github”? Is Torvalds involved in Github?

2. In the “history of github” article, when did Github pass 1 million repos? When did it pass 10 million repos? How many repos are there now?

3. Github is a commercial site. Some of it’s commercial services include Github copilot. Explain this service. This service is based on a secondary use for the code that’s made available on github repos by github users. What is this secondary use? Are Github customers aware that their code is put to this secondary use? How much code do you think is available for the Github company to put to this secondary use? Who owns Github? Who is the largest investor in OpenAI? Does OpenAI make use of github code?

4. Do you have an existing Github account? If so, is it Paid or Free?  If so, have you created any public repos? Private repos? Say a bit about your motivations and experiences.

5. The h-index arose as a method to quantify influence of authors in academia. It assigns a value to the author based on how many citations each paper by the author has gotten. In “GitHub Stars and the h-index” Vanderkam creates a similar notion for github repos based on Github Stars. In “Growth Hacking Github — how to get github stars” the author identifies some highly-starred repos. Name some highly starred repos. name some highly h-indexed-repo authors. 

6. Name some push practices that are frowned upon. Explain why they are frowned upon.

To run our code on many systems of different scale -- laptop, server, cluster, and supercomputer -- we need to distribute the same code to each computation node. We use a distributed version control system called `git` and a service called [GitHub](https://github.com) to reliably distribute our code.

One of the first rules of code is that it changes. Version control systems have migrated to the center of the server and supercomputer ecosystems. Today's homework is the beginning of showing you how code evolves. We will start with a modest rewriting of HW2 to use functions and embrace associating parameters and observables. Unlike last week though, the code is delivered as a URL to a GitHub repository, [Stats285_hw3](https://github.com/adonoho/Stats285_hw3). Why is this important? Because code written by others changes. This code is going to change. We will be updating it to do the tall and skinny SVD and to write the results to a remote database.

This assignment expects you to already have a free GitHub account.

1. Open a terminal window on your laptop.

2. Issue the following command: `git clone https://github.com/adonoho/Stats285_hw3`

3. Change directory to `Stats285_hw3`.

1. Login to FarmShare.

2. Issue the following command: `git clone https://github.com/adonoho/Stats285_hw3`

3. Change directory to `Stats285_hw3`.

4. Examine the contents; does it look modestly familiar?

5. Execute the same command from last week: `sbatch hw2.sh`, followed by `squeue` .

6. Look at the branches of different code already in this project: `git branch -a`

7. You will see both local and remote branches. On the remote branches, you will see where hw3 will be developed. If you use the GitHub feature to watch the repo, GitHub will email you when it changes.

### Our current status:

Parallel systems are heavily protected on the internet. We originally planned to host a database on Sherlock and get each of you credentials to write your data to the DB and then run the gather phase on your personal laptop. You would use the same code repository on FarmShare and your laptop. Alas, FarmShare codes cannot access Sherlock resources. We are looking at either using a Stanford managed instance of MySQL or a group managed instance of PostgreSQL on GCP. This will all be resolved by Wednesday and the code published on GitHub.
