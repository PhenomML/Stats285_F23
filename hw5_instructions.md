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

10. Execute `map_function.py` on an array of nodes:  
	`sbatch hw5_array.sh`  
	`squeue -u $USER`
```
	(stats285) adonoho@rice03:~/Stats285_F23$ squeue -u $USER
			 JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
		   2422878_0      normal hw5_arra  adonoho  R       0:14      1 wheat08
		   2422878_100    normal hw5_arra  adonoho  R       0:14      1 wheat08
		   2422878_200    normal hw5_arra  adonoho  R       0:14      1 wheat08
		   2422878_300    normal hw5_arra  adonoho  R       0:14      1 wheat08
		   2422878_400    normal hw5_arra  adonoho  R       0:14      1 wheat08
		   2422878_500    normal hw5_arra  adonoho  R       0:14      1 wheat08
		   2422878_600    normal hw5_arra  adonoho  R       0:14      1 wheat08
		   2422878_700    normal hw5_arra  adonoho  R       0:14      1 wheat08
		   2422878_800    normal hw5_arra  adonoho  R       0:14      1 wheat08
		   2422878_900    normal hw5_arra  adonoho  R       0:14      1 wheat08
```
11. Upon completion, about 2 minutes, look inside `hw5_array.err`.  
The beginning of the file:
```
	INFO:root:./map_function.py 1000 1000 300 su_id_hw5
	INFO:root:./map_function.py 1000 1000 200 su_id_hw5
	INFO:root:./map_function.py 1000 1000 100 su_id_hw5
	INFO:root:./map_function.py 1000 1000 0 su_id_hw5
	INFO:root:./map_function.py 1000 1000 400 su_id_hw5
	INFO:root:./map_function.py 1000 1000 900 su_id_hw5
	INFO:root:./map_function.py 1000 1000 700 su_id_hw5
	INFO:root:./map_function.py 1000 1000 800 su_id_hw5
	INFO:root:./map_function.py 1000 1000 500 su_id_hw5
	INFO:root:./map_function.py 1000 1000 600 su_id_hw5
	INFO:root:Seed: 300; 1.3961942195892334 seconds.
	INFO:root:Seed: 200; 1.4054896831512451 seconds.
	INFO:root:Seed: 0; 1.4151535034179688 seconds.
	INFO:root:Seed: 100; 1.4287505149841309 seconds.
	INFO:root:Seed: 600; 1.8204312324523926 seconds.
	INFO:root:Seed: 700; 1.8267004489898682 seconds.
	INFO:root:Seed: 800; 1.836639642715454 seconds.
	INFO:root:Seed: 500; 1.8410115242004395 seconds.
	INFO:root:Seed: 400; 1.8435065746307373 seconds.
	INFO:root:Seed: 900; 1.8431742191314697 seconds.
	INFO:root:Seed: 301; 1.026653528213501 seconds.
	INFO:root:Seed: 201; 1.046555757522583 seconds.
	INFO:root:Seed: 1; 1.0573809146881104 seconds.
	INFO:root:Seed: 101; 1.0570011138916016 seconds.
```  
The end of the file:  
```
	INFO:root:Seed: 99; 0.8401017189025879 seconds.
	INFO:root:/home/adonoho/Stats285_F23/su_id_hw5_000.csv
	INFO:root:Seed: 994; 0.9245727062225342 seconds.
	INFO:root:Seed: 695; 0.951512336730957 seconds.
	INFO:root:Seed: 299; 0.8551983833312988 seconds.
	INFO:root:Seed: 796; 0.9350428581237793 seconds.
	INFO:root:/home/adonoho/Stats285_F23/su_id_hw5_200.csv
	INFO:root:Seed: 595; 0.9323587417602539 seconds.
	INFO:root:Seed: 496; 0.9254944324493408 seconds.
	INFO:root:Seed: 896; 1.025771141052246 seconds.
	INFO:root:Seed: 995; 0.910144567489624 seconds.
	INFO:root:Seed: 797; 0.9598126411437988 seconds.
	INFO:root:Seed: 696; 0.9822354316711426 seconds.
	INFO:root:Seed: 596; 1.0276415348052979 seconds.
	INFO:root:Seed: 497; 1.1631739139556885 seconds.
	INFO:root:Seed: 996; 0.9988284111022949 seconds.
	INFO:root:Seed: 897; 1.3057270050048828 seconds.
	INFO:root:Seed: 798; 0.9735469818115234 seconds.
	INFO:root:Seed: 697; 0.9932045936584473 seconds.
	INFO:root:Seed: 597; 0.9295105934143066 seconds.
	INFO:root:Seed: 498; 0.916872501373291 seconds.
	INFO:root:Seed: 997; 0.9672515392303467 seconds.
	INFO:root:Seed: 898; 0.9448280334472656 seconds.
	INFO:root:Seed: 799; 0.9604976177215576 seconds.
	INFO:root:/home/adonoho/Stats285_F23/su_id_hw5_700.csv
	INFO:root:Seed: 698; 0.9734225273132324 seconds.
	INFO:root:Seed: 598; 0.9164829254150391 seconds.
	INFO:root:Seed: 499; 0.90018630027771 seconds.
	INFO:root:/home/adonoho/Stats285_F23/su_id_hw5_400.csv
	INFO:root:Seed: 998; 0.9398007392883301 seconds.
	INFO:root:Seed: 899; 1.0349164009094238 seconds.
	INFO:root:/home/adonoho/Stats285_F23/su_id_hw5_800.csv
	INFO:root:Seed: 699; 0.9158093929290771 seconds.
	INFO:root:/home/adonoho/Stats285_F23/su_id_hw5_600.csv
	INFO:root:Seed: 599; 0.8771994113922119 seconds.
	INFO:root:/home/adonoho/Stats285_F23/su_id_hw5_500.csv
	INFO:root:Seed: 999; 0.9271728992462158 seconds.
	INFO:root:/home/adonoho/Stats285_F23/su_id_hw5_900.csv
```
12. Now we will gather the results together on the login node and send them to GBQ. (GBQ will need a `table_name`, `su_id_hw5` in the example below. You should change the `su_id` to your Stanford ID.):
```
	(stats285) adonoho@rice03:~/Stats285_F23$ python3 gather_csv_to_gbq.py su_id_hw5 *.csv
```
`gather_csv_to_gbq.py` will log its command line arguments and will be followed by GBQ acknowledging the receipt of 1000 rows of data.
```
	INFO:root:gather_csv_to_gbq.py su_id_hw5 su_id_hw5_000.csv su_id_hw5_100.csv su_id_hw5_200.csv su_id_hw5_300.csv su_id_hw5_400.csv su_id_hw5_500.csv su_id_hw5_600.csv su_id_hw5_700.csv su_id_hw5_800.csv su_id_hw5_900.csv
	1000 out of 1000 rows loaded.
```

13. 
```
(stats285) adonoho@rice03:~/Stats285_F23$ squeue -u $USER
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
           2422892    normal hw5_larg  adonoho  R       1:28      1 wheat12
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

