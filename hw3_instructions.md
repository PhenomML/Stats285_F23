# Homework 3. Easing the Pain with Version Control

Modern use of computers generally involves distributing code to many different nodes on the internet. So far we were logging in to each node and sending code by manual copying. This model doesn’t scale. Instead, we will introduce a method of code distribution using an internet resource — [GitHub](https://github.com).  Getting introduced to `git` and GitHub will have other advantages for us, down the road. The model we will introduce is widely used. 

### Short Answer Questions

On Canvas, navigate to Files -> Readings -> Github.

#### History of Git (Welcome to the Jungle article)

Read the "History of Git: The Road to Domination" article. Answer the following questions.

1. What is claimed to be Linus Torvalds reason for the name “git”. 

2. Who does Linus Torvalds credit as the project lead for “git”? 

3. Why did Torvalds think that he needed to design and start “git”? 

4. What is the relation between “git” and Linux? 

5. What is the relation between Linux and “the cloud”? 

6. What is the relation between “git” and “github”? 

7. Is Torvalds involved in Github?

#### History of Github (Evans & Debacker article)

Read the "History of GitHub" article from Evans & Debacker. Answer the following questions.

1. When did Github pass 1 million repos? 

2. When did it pass 10 million repos? 

3. How many repos are there now?

#### Growth Hacking Github (Lin article)

Read the "Growth Hacking Github" article by Lin. Answer the following questions.

1The h-index arose as a method to quantify influence of authors in academia. It assigns a value to the author based on how many citations each paper by the author has gotten. In “GitHub Stars and the h-index” Vanderkam creates a similar notion for github repos based on Github Stars. In “Growth Hacking Github — how to get github stars” the author identifies some highly-starred repos. Name some highly starred repos. name some highly h-indexed-repo authors. 

#### Look-Up Questions

Using the resources available to use (e.g. Google, Wikipedia, etc.), answer the following questions.

1. Github is a commercial site. Some of it’s commercial services include Github copilot. Explain this service. 

4. Github copilot is based on a secondary use for the code that’s made available on github repos by github users. What is this secondary use? 

5. Are Github customers aware that their code is put to this secondary use? 

6. How much code do you think is available for the Github company to put to this secondary use? 

7. Who owns Github? 

8. Who is the largest investor in OpenAI? 

9. Does OpenAI make use of github code?

4. Do you have an existing Github account? If so, is it Paid or Free?  If so, have you created any public repos? Private repos? Say a bit about your motivations and experiences.

6. Name some push practices that are frowned upon in a data science community. Explain why they are frowned upon.


### Exercises

To run our code on many systems of different scale -- laptop, server, cluster, and supercomputer -- we need to distribute the same code to each computation node. And we need to ensure that we have the same computational environment everywhere. As Python programmers, we will use a system for managing scientific code called [Conda](https://docs.conda.io/en/latest/). (In hw2, you were likely lucky to have your code run. We need to remove luck from your scientific process by controlling your computational/experimental environment.) You can install Conda for [Mac here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html) and [Windows here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html). You have a choice of Miniconda or Anaconda; Miniconda is installed via the command line versus Anaconda has a GUI; your choice. The configuration of your Python environment is managed in an `environment.yml` file.

Version control systems have migrated to the center of the server and supercomputer ecosystems. Today's homework is the beginning of showing you how code evolves. We will start with a modest rewriting of HW2 to use functions and embrace associating parameters and observables. Unlike last week though, the code is delivered as a URL to a GitHub repository, [Stats285_hw3](https://github.com/adonoho/Stats285_hw3). Why is this important? Because you want the code on your servers to be the same as the code you developed and tested on your laptop. This is something that version control systems do very well. We should exploit them.

This assignment expects you to already have a free GitHub account.

1. Open a terminal window on your laptop.

8. Issue the following command:  
	`git clone https://github.com/adonoho/Stats285_hw3`

9. Change directory to:  
	`cd Stats285_hw3/`

10. Issue the following command:  
	`conda env create --name stats285 --file environment.yml`

11. Issue the following command:  
	`conda activate stats285`

12. Issue the following command:  
	`python --version`  
	You should see: `Python 3.11.6`.

13. Issue the following command:  
	`python main.py`  

	You should see something like:
```
	INFO:root:Data Generated
	INFO:root:nrow = 1000
	INFO:root:ncol = 1000
	INFO:root:u_alignment = -0.9999441742880615
	INFO:root:v_alignment = -0.9999459499387543
	INFO:root:signal_error = 4.447919645101738e-05
	INFO:root:--- 0.38405895233154297 seconds ---
```

14. Login to FarmShare.

15. Issue the following command:  
	`git clone https://github.com/adonoho/Stats285_hw3`

16. Change directory to  
	`cd Stats285_hw3/`

17. Examine the contents; does it look modestly familiar?

18. Check if the `conda` environment `stats285` is still around?  
```
	ml anaconda3/2023.07
	conda env list
```

19. If so, delete it:  
	`conda env remove --name stats285`

20. Create a new environment:  
	`conda env create --name stats285 --file environment.yml`  
	(This can take a few minutes.)

21. Turn it on:  
	`source activate stats285`  
	(Note, FarmShare is different from other Unix/Linux shells.)

22. Execute the same command from last week:  
	`sbatch hw2.sh`  
	`squeue`
