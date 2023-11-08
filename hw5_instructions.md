# Homework 5. Driving Parameters while Growing into a Cluster.

Heretofore, we have been running on a single node. Today's computing activity will introduce our use of parameter ramps and the beginnings of using a cluster -- first on a larger node and then on an array of nodes.

## Computing activity

We have been very careful to keep our code simple. Why? Debugging a server is quite a bit more difficult than debugging code on your laptop, a parallel server, unsurprisingly, more so. Hence, we want you to perfect your code on your laptop and then scale it up without change. To this end, we introduced simple code that created the results of a 1000 x 1000 SVD of noisy data. We then repackaged it as a function that takes keyword arguments and returns a DataFrame. This code we ran on both your laptop and a server. That brings us to our fourth computer activity -- computing with a cluster to create the core data for a 1,000,000 x 1,000 SVD and saving your data to the cloud. Once the data is in the cloud, it is easy to read it into a Jupyter or Colab notebook to finish the tall and skinny SVD calculation.

We are starting by following the advice of the Stanford Research Computing Center, SRCC, staff to use the `sbatch array` command to launch a group of tasks while allowing `sbatch` to assign some of your parameters. In this example, we take the same experimental function, `map_function.py` in the project, and drive it from the command line. We also introduce saving the data to the remote database, Google BigQuery. What you will find is that the `sbatch array` command is really oriented around the command line and creating text files. It isn't a good fit for database centric computing. Hence, we play to the strengths of the traditional supercomputing infrastructure to write the data as files, gather them together and then write them to the remote database. As we've maintained in this course, almost anytime you create a file, it is an opportunity for human intervention and higher friction. Hence, there are three functions involved: `map_function.py`, `gather_csv_to_gbq.py`, and `HW5_analysis.ipynb`. `map_function.py` creates a bunch of `.csv` files; which are read into `gather_csv_to_gbq.py` and are sent to Google BigQuery. This experiment is driven by the `sbatch` script `hw5_array.sh`. 

To replace your burden on gathering computational results, we are going to start using a simple system to run many independent tasks and write the results to the remote database. This system, [EMS or Experiment Management System](https://github.com/adonoho/EMS), takes a definition of your parameters as arrays and then calls your function with the combination of all parameter values. It then stores the result of each function in a database. (This is the beginning of a research tool for the Stanford Donoho Lab. Yet, even at this early date, it is useful.)

Because modern laptops contain many processors, the one I am writing this on has 6 symmetric cores and can run 12 concurrent tasks, you can frequently run your code quite a bit faster than normal using EMS. EMS depends upon a Python system called Dask which can allow quite complex parallel operations. As our tasks are embarrassingly parallel, we will not be exploiting Dask for other than processor/thread/worker management. But it is available for more advanced work. For example, there is an advanced way to use Dask to solve the [Tall & Skinny SVD problem](https://examples.dask.org/machine-learning/svd.html#Compute-SVD-of-Tall-and-Skinny-Matrix).

EMS always saves your data locally via SQLite in your `data/` directory. On Mac or Windows, you can examine this file using [SQLite Studio](https://sqlitestudio.pl). Hence, you can always use EMS without a cloud database. This is quite useful for debugging your code. You can easily compare your data between runs by just changing your table name. Then, when you are ready to start more formal experimentation, we can start telling EMS to additionally use a cloud database, Google Big Query in this class. If you insist, EMS also includes a Python script to copy a table from the local database to a `.csv` file.

To turn on saving your data to the cloud database, we need to do two things. First, we need to save credentials that tell the database to accept data from our task in a standard location and then tell EMS to use them. The class will provide you with these credentials and we will show you where to install them on FarmShare and your laptop. These credentials are focussed upon just Google Big Query operations. Nonetheless, you can hurt yourself and your classmates by misusing these permissions. Be nice.

We then have two kinds of servers to use -- a single large server and a cluster of smaller servers. On FarmShare, both are invoked via SLURM in a way that is almost identical to your earlier homework. Once the cluster server is running, it then asks SLURM to give it more processors. If they are available, SLURM complies. The cluster server can actually be smaller than the nodes it requests to calculate its answers. All it does is dole out parameters and save DataFrames locally and to the cloud.

The computer activity is rounded out by loading your data into a notebook and then finishing the Tall & Skinny SVD. 

#### Getting Database Access Credentials onto your laptop and Farmshare account

1. Open a terminal window on your laptop. In the shell, run this command:  
    `echo -n -e "\033]0;LAPTOP\007"`

2. Login to FarmShare. [or Sherlock, if you have an account there]  
    `echo -n -e "\033]0;FARMSHARE\007"`

3. Download the security credentials from the Canvas system. (On Mac, the file will end up in your `~/Downloads/` directory.)

4. On your laptop at your login directory:  
	`mkdir .config/gcloud`  
	`cp ~/Downloads/stanford-stats-285-donoho-0dc233389eb9.json ~/.config/gcloud/`

5. On FarmShare at your login directory:  
	`mkdir .config/gcloud`  
	`scp  ~/Downloads/stanford-stats-285-donoho-0dc233389eb9.json su_id@rice.stanford.edu:~/.config/gcloud/`

#### Running code on a server

1. Clone the HW repository. (Note: It's name has changed.):  
	`git clone https://github.com/adonoho/Stats285_F23`

4. Change directory to  
	`cd Stats285_F23/`

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

10. Execute `map_function.py` on a large node:  
	`sbatch hw5_array.sh`  
	`squeue -u $USER`

11. Look inside `hw5_array.err`. 
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

#### Running code on your Laptop

1. Open a terminal window on your laptop. In the shell, run this command:  
    `echo -n -e "\033]0;LAPTOP\007"`

2. Issue the following command:  
	`git clone https://github.com/adonoho/Stats285_F23`

3. Change directory to:  
	`cd Stats285_F23/`

6. Check if the `conda` environment `stats285` is still around?  
	`conda env list`

7. If so, delete it:  
	`conda env remove --name stats285`

8. Create a new environment:  
	`conda env create --name stats285 --file environment.yml`  
	(This can take a few minutes.)

5. Issue the following command:  
	`conda activate stats285`

6. Issue the following command:  
	`python --version`  
	You should see: `Python 3.11.6`.

7. Issue the following command:  
	`python main.py`

	You should see something like:
```
(stats285) awd@Mazikeen Stats285_F23 % python main.py 
INFO:EMS.manager:<Client: 'tcp://127.0.0.1:65285' processes=4 threads=12, memory=32.00 GiB>
ERROR:EMS.manager:(sqlite3.OperationalError) no such table: stats285_adonoho_slurm_wide_small_hw4_1000_blocks
[SQL: SELECT DISTINCT ncol,nrow,seed FROM stats285_adonoho_slurm_wide_small_hw4_1000_blocks]
(Background on this error at: https://sqlalche.me/e/20/e3q8)
INFO:EMS.manager:Number of Instances to calculate: 1000
INFO:root:Seed: 778; 6.318756103515625 seconds.
INFO:root:Seed: 563; 6.379151105880737 seconds.
INFO:root:Seed: 329; 6.416765928268433 seconds.
INFO:root:Seed: 659; 6.467713117599487 seconds.
INFO:root:Seed: 947; 6.609302997589111 seconds.
INFO:root:Seed: 635; 6.593518972396851 seconds.
INFO:root:Seed: 629; 6.604357004165649 seconds.
INFO:root:Seed: 461; 6.622162818908691 seconds.
INFO:root:Seed: 364; 6.653280019760132 seconds.
INFO:root:Seed: 522; 6.6136579513549805 seconds.
INFO:root:Seed: 332; 6.716217041015625 seconds.
INFO:root:Seed: 411; 6.6921021938323975 seconds.
INFO:EMS.manager:Count: 10; Time: 8; Seconds/Instance: 0.7887; Remaining (s): 781; Remaining Count: 990
INFO:EMS.manager:   nrow  ncol  seed  v_alignment     ve000     ve001     ve002  ...     ve993     ve994     ve995     ve996    ve997     ve998     ve999
0  1000  1000   411    -0.999947  0.031999 -0.031529  0.031496  ... -0.031423  0.032273 -0.030896  0.031236 -0.03182  0.031309 -0.031774

[1 rows x 1004 columns]
```

