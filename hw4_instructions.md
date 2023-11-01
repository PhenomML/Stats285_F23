# Homework 4. Driving Parameters while Growing into a Cluster.

Heretofore, we have been running on a single node. Today's computing activity will introduce our use of parameter ramps and the beginnings of using a cluster -- first on a larger node and then on an array of nodes.

## Short Answer Questions

On Canvas, navigate to Files -> Readings -> *Insert Here*

#### History of *Clusters*

*Insert Cluster Questions*


#### History of Github (Evans & Debacker article)

*Insert Cluster Questions*

#### Github Stars and the h-index (Vanderkam article)

*Insert Cluster Questions*

#### Growth Hacking Github (Lin article)

*Insert Cluster Questions*

#### Look-Up Questions

*Insert Cluster Questions*

## Computing activity

We have been very careful to keep our code simple. Why? Debugging a server is quite a bit more difficult than debugging code on your laptop, a parallel server, unsurprisingly, more so. Hence, we want you to perfect your code on your laptop and then scale it up without change. To this end, we introduced simple code that created the results of a 1000 x 1000 SVD of noisy data. We then repackaged it as a function that takes keyword arguments and returns a DataFrame. This code we ran on both your laptop and a server. That brings us to our fourth computer activity -- computing with a cluster to create the core data for a 1,000,000 x 1,000 SVD and saving your data to the cloud. Once the data is in the cloud, it is easy to read it into a Jupyter or Colab notebook to finish the tall and skinny SVD calculation.

We are going to start using a simple system to run many independent tasks, also known as an embarrassingly parallel problem. This system, [EMS or Experiment Management System](https://github.com/adonoho/EMS), takes a definition of your parameters as arrays and then calls your function with the combination of all parameter values. It then stores the result of each function in a database. (This is the beginning of a research tool for the Stanford Donoho Lab. Yet, even at this early date, it is useful.)

Because modern laptops contain many processors, the one I am writing this on has 6 symmetric cores and can run 12 concurrent tasks, you can frequently run your code quite a bit faster than normal using EMS. EMS depends upon a Python system called Dask which can allow quite complex parallel operations. As our tasks are embarrassingly parallel, we will not be exploiting Dask for other than processor/thread/worker management. But it is available for more advanced work. For example, there is an advanced way to use Dask to solve the [Tall & Skinny SVD problem](https://examples.dask.org/machine-learning/svd.html#Compute-SVD-of-Tall-and-Skinny-Matrix).

EMS always saves your data locally via SQLite in your `data/` directory. On Mac or Windows, you can examine this file using [SQLite Studio](https://sqlitestudio.pl). Hence, you can always use EMS without a cloud database. This is quite useful for debugging your code. You can easily compare your data between runs by just changing your table name. Then, when you are ready to start more formal experimentation, we can start telling EMS to additionally use a cloud database, Google Big Query in this class. If you insist, EMS also includes a Python script to copy a table from the database to a `.csv` file.

To turn on saving your data to the cloud database, we need to do two things. First, we need to save credentials that tell the database to accept data from our task in a standard location and then tell EMS to use them. The class will provide you with these credentials and we will show you where to install them on FarmShare and your laptop. These credentials are focussed upon just Google Big Query operations. Nonetheless, you can hurt yourself and your classmates by misusing these permissions. Be nice.

We then have two kinds of servers to use -- a single large server and a cluster of smaller servers. On FarmShare, both are invoked via SLURM in a way that is almost identical to your earlier homework. Once the cluster server is running, it then asks SLURM to give it more processors. If they are available, SLURM complies. The cluster server can actually be smaller than the nodes it requests to calculate its answers. All it does is dole out parameters and save DataFrames locally and to the cloud.

The computer activity is rounded out by loading your data into a notebook and then finishing the Tall & Skinny SVD. 

```
mkdir .config/gcloud
scp stanford-stats-285-donoho-0dc233389eb9.json adonoho@rice.stanford.edu:~/.config/gcloud/
```

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

11. Unlike hw2, we now are using the logging tool in Python. FarmShare will place this data in the error stream, `hw2.err`. In that file, you should see a similar output to laptop step 7 above.  
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

12. We also have written a new format `.csv` file, `hw2data.csv`. It shows some characteristics of `numpy`/`pandas` where scalars, the parameters in our case, are "broadcast" to match the "shape" of the observables.  
```
	index,nrow,ncol,seed,u_est,v_est,u_true,v_true
	0,1000,1000,285,-0.03236102757929593,0.031223329570119786,0.03162277660168379,-0.03162277660168379
	1,1000,1000,285,0.03139612247692286,-0.03127049843880714,-0.03162277660168379,0.03162277660168379
```

