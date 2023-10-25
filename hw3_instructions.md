# Homework 3. Easing the Pain with Version Control

Modern use of computers generally involves distributing code to many different nodes on the internet. So far we were 
logging in to each node and sending code by manual copying. This model doesn’t scale. Instead, we will introduce a 
method of code distribution using an internet resource — [GitHub](https://github.com).  Getting introduced to `git` and GitHub will have other advantages for us, down the road. The model we will introduce is widely used. 

If you are new to Github, you might consult this [Quickstart](https://docs.github.com/en/get-started/quickstart/hello-world)

## Short Answer Questions

On Canvas, navigate to Files -> Readings -> Github.

#### History of Git (Welcome to the Jungle article)

Read the "History of Git: The Road to Domination" article. Answer the following questions.

1. What is claimed to be Linus Torvalds' reason for the name “git”. 

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

4. Who currently owns Github? 

5. What are some concerns people had when Github was acquired?

6. Who are some competitors of Github?

#### Github Stars and the h-index (Vanderkam article)

The h-index arose as a method to quantify influence of authors in academia. It assigns a value to the author based
on how many citations each paper by the author has gotten. In “GitHub Stars and the h-index” Vanderkam creates a 
similar notion for github repos based on Github Stars. Read the article and answer the following questions.

1. Name some highly starred repos.

2. Name some highly h-indexed-repo authors. 

3. Using resources available to you (e.g. Google, Wikipedia, etc.), look up and describe how the (usual academic publishing) h-index is calculated.
   
4. Explain how the 'github star h-index' is calculated.

#### Growth Hacking Github (Lin article)

Read the "Growth Hacking Github" article by Lin and answer the following questions.

1. To what factors does the author attribute the success of Redux Toolkit?
2. To what factors does the author attribute the success of Huggingface Transformers?
3. Describe, in your own words, ten strategies the author recommends for increasing the number of Github stars.

#### Look-Up Questions

Using the resources available to you (e.g. Google, Wikipedia, etc.), answer the following questions.

1. Github is a commercial site. Some of it’s commercial services include Github copilot. Explain this service. 

2. Github copilot is based on a secondary use for the code that’s made available on public github repos by github users. What is this secondary use? 

3. Are Github customers aware that their code is put to this secondary use? 

4. How much code do you think is available for the Github company to put to this secondary use? 

5. Who is the owner of github and largest investor in OpenAI? 

6. Does OpenAI make use of Github code?

7. Name and explain some disadvantages of Github for doing data science.
   
8. Do you have an existing Github account? If so, is it paid or free?  
If so, have you created any public or private repos? 
If not, have you ever tried to use Github before? Name any obstacles or frictions you faced?
(In either case, say a bit about your motivations and experiences.)

## Computing activity

To run our code on many systems of different scale -- laptop, server, cluster, and supercomputer -- we need to distribute the same user-specific code to each computation node. As you now understand, we can use github to supply the user-specific code we hope to run everywhere, across many nodes. We will do this below. 

But wait, there's one more wrinkle. Let's call the user-specific code the *top of our stack*. Beneath it sits the whole computational environment our user-specific code is depending on, for examply python, git, certain database applications etc. Let's call this the *rest of the stack*.

Just because we use github to supply the 'top of the stack' software, and just because the different target nodes actually 'have python' or 'have git' or 'have SQLLite' or ... that doesn't mean that all those nodes have the *same python* or the *same git* or .... If different nodes have different instances of such applications, we are not entitled to assume that running user-specific code successfully on one node implies running successfully on another node. 

So actually, we were lucky that in last week's homework, the user-specific code we had, ran on *both* our laptop and also on the compute node we accessed over FarmShare/Sherlock. It might conceivably have run on one but not the other!

In the future, it's better to specify the *entire stack* we are assuming, including specific versions of software, and install exactly the specified stack on each node, so that we can be sure that every node has the same computational environment, and can run the same code. 

As Python programmers, we will use a system for managing stacks of scientific code called [Conda](https://docs.conda.io/en/latest/). It allows us to efficiently and conveniently define and install `the rest of our stack' as a computational environment.  

You can install Conda on your laptop. [Mac here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/macos.html) and [Windows here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html). You have a choice of Miniconda or Anaconda; Miniconda is installed via the command line while Anaconda has a GUI; your choice. The configuration of your Python environment is managed in an `environment.yml` file.

In this HW the code is a modest rewriting of HW2, which should be functionally almost the same. Unlike last week, the authoritative version of this week's code lives in a GitHub repository, [Stats285_hw3](https://github.com/adonoho/Stats285_hw3), and then is cloned to your laptop and also to any FarmShare/Sherlock node you connect to. This way, as we said, the user-specific code on your servers will be the same as the user-specific code you tested on your laptop.

This assignment expects you to already have a free GitHub account.

#### Running code on your Laptop

1. Open a terminal window on your laptop. In the shell, run this command:
    `echo -n -e "\033]0;LAPTOP\007"`

2. Issue the following command:  
	`git clone https://github.com/adonoho/Stats285_hw3`

3. Change directory to:  
	`cd Stats285_hw3/`

4. Issue the following command:  
	`conda env create --name stats285 --file environment.yml`

5. Issue the following command:  
	`conda activate stats285`

6. Issue the following command:  
	`python --version`  
	You should see: `Python 3.11.6`.

7. Issue the following command:  
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

#### Running code on a server

1. Open another terminal window on your laptop. In the shell, run this command:
    `echo -n -e "\033]0;FARMSHARE\007"`

2. Login to FarmShare. [or Sherlock, if you have an account there]

3. Issue the following command:  
	`git clone https://github.com/adonoho/Stats285_hw3`

4. Change directory to  
	`cd Stats285_hw3/`

5. Examine the contents; does it look modestly familiar?

6. Check if the `conda` environment `stats285` is still around?  
```
	ml anaconda3/2023.07
	conda env list
```

7. If so, delete it:  
	`conda env remove --name stats285`

8. Create a new environment:  
	`conda env create --name stats285 --file environment.yml`  
	(This can take a few minutes.)

9. Turn it on:  
	`source activate stats285`  
	(Note, FarmShare is different from other Unix/Linux shells.)

10. Execute the same command from last week:  
	`sbatch hw2.sh`  
	`squeue`

23. Unlike hw2, we now are using the logging tool in Python. FarmShare will place this data in the error stream, `hw2.err`. In that file, you should see a similar output to step 13 above.  
```
	INFO:root:Data Generated
	INFO:root:nrow = 1000
	INFO:root:ncol = 1000
	INFO:root:u_alignment = -0.999944174288061
	INFO:root:v_alignment = -0.9999459499387543
	INFO:root:signal_error = 4.4479196451017426e-05
	INFO:root:--- 0.509589433670044 seconds ---
	2.05user 0.29system 0:03.47elapsed 67%CPU (0avgtext+0avgdata 177812maxresident)k
	545112inputs+208outputs (108major+31186minor)pagefaults 0swaps
```

24. We also have written a new format `.csv` file, `hw2data.csv`. It shows some characteristics of `numpy`/`pandas` where scalars, the parameters in our case, are "broadcast" to match the "shape" of the observables.  
```
	index,nrow,ncol,seed,u_est,v_est,u_true,v_true
	0,1000,1000,285,-0.03236102757929593,0.031223329570119786,0.03162277660168379,-0.03162277660168379
	1,1000,1000,285,0.03139612247692286,-0.03127049843880714,-0.03162277660168379,0.03162277660168379
```

