# Homework 5. Deploying Many Jobs, Served Three Ways. Hot.

Our earlier homeworks were run on a single compute node. Today's computing activity will introduce the beginnings of using a cluster -- first on a larger node and then on an array of nodes.

## Computing activity

You will see that we now have 4 bash scripts: `hw5_large.sh` `hw5_cluster.sh` and `hw5_array.sh` `hw5_personalize.sh` and three python scripts: `main.py`, `map_function.py`; we also have two Jupyterlab notebooks `reading_gbq.ipynb` and `hw5_reduce.ipynb`. 

So far, we introduced simple code that created the results of a **1000 x 1000** SVD of noisy data. We then repackaged it as a function that takes keyword arguments and returns a DataFrame. This code we ran on both your laptop and a server. 

In this week's computer activity -- we are computing with a cluster to (approximately) do (part of) a **1,000,000 x 1,000** SVD, within the divide and recombine (map-reduce) paradigm. The same basic code we used before is re-used to make a mapper function, applied in 1,000 separate `map` instances, each of size 1000 x 1000. Notionally, each `map` instance saves  results to the cloud. Once all the `map` results are in the cloud, we will eventually do the `reduce` step. 

To do the `map` job distribution into 1000 instances, and get the results up to the cloud, we follow one of several *strategies*.

### `hw5_array.sh`

Our first strategy is implemented by `hw5_array.sh` and `map_function.py`. It heeds the advice of the Stanford Research Computing Center (SRCC) staff to use the `sbatch array` shell command to deploy many instances on its cluster. Like `sbatch`, `sbatch array` launches jobs; unlike simple `sbatch`, which we have used before, `sbatch array` can launch many instances of `map_function.py` as a result of this one one shell command. `hw5_array.sh` uses this strategy to launch 10 instances of `map_function.py` as in some sense *meta instances*, which each iterate through 100 actual instances, thereby computing 1000 instances of total work. Each instance saves its results; ultimately to be reduced. 

We had hoped to follow the original notional model discussed above, to use the cloud database to save individual instance results immediately, as they were produced.  Unfortunately, we found that straightforward use of `sbatch array` on Sherlock/FarmShare was not compatible with instance-by-instance upload of results to GBQ (some network issues intervened). To find a way forward, we had to resort to an ugly Kluge -- fallback to files. Thus the delivered `hw5_array.sh` and `map_function.py` combination first writes the instance results as .csv files. These will later separately be amalgamated into a DataFrame and written to GBQ by a separate program: `gather_csv_to_gbq.py`.  Results are stored under the table_name <SUID>_hw5, where in place of <SUID> would be the suid that you use for login to Stanford systems. (It is possible to use other table_names, for example for debugging purposes; but note that the script `hw5_personalize.sh` embeds your suid into actual code, and this would need to be overridden.)

### `hw5_large.sh`

A different strategy involves using more cores; it is implemented by `hw5_large.sh`, it is invoked via SLURM using `sbatch` commands that at first glance looks identical to your earlier single-instance homework. In fact, some of the `#SBATCH` directives are different.

Modern laptops contain many cores; the one I am writing this on has 6 symmetric cores and can run 12 concurrent tasks. You can frequently run your code quite a bit faster on a laptop if you use all the available cores. 

To exploit multiple cores, we use the Python system `Dask' for processor/thread/worker management. We will not now be using all its capabilities.

To access Dask, we use a homebrew system [EMS or Experiment Management System](https://github.com/adonoho/EMS). It assumes you have written a pure function for your computational task; it inputs an array of desired parameter values and calls your function one time for each distinct combination of parameter values. It stores the result of each function call in a database. 

*Aside 1. EMS to Local DB.* EMS always saves your data locally via SQLite in your `data/` directory. On Mac or Windows, you can examine this file using [SQLite Studio](https://sqlitestudio.pl). Hence, you can always use EMS without a cloud database. 

*Aside 2. Debugging option.* You can easily preserve data between runs by just changing your table_name. 

*Aside 3. EMS to Cloud DB.* EMS can also use a cloud database, Google Big Query in this class. EMS also includes a Python script to copy a table from the local database to a `.csv` file. To turn on saving your data to the cloud database, we need to do two things. First, we need to save credentials that tell the database to accept data from our task in a standard location and then tell EMS to use them. The class will provide you with these credentials and we will show you where to install them on FarmShare and your laptop. These credentials are focused upon just Google Big Query operations. 

*Aside 4. Warning/Request.* When using the Cloud DB option, you can erase your work or that of your classmates by misusing Cloud DB permissions. Be nice.

### `hw5_cluster.sh` 

We actually can use DASK in two ways on Sherlock/FarmShare -- it can request a single large server with many cores; or it can ask for a cluster of smaller servers. `hw5_large.sh` used the first approach. `hw5_cluster.sh` uses the second approach. 

`hw5_cluster.sh` is a bash script using `sbatch` commands which, again, at first glance looks similar to your earlier single-instance homework. In fact, some of the `#SBATCH` directives are different. Once the cluster server is running, it asks SLURM to give it more processors. If they are available, SLURM complies. The cluster server can actually be smaller than the nodes it requests to calculate its answers. All it does is dole out parameters and save DataFrames locally and to the cloud.

### `hw5_reduce.ipynb` Reduce task

The reduce step is implemented by `hw5_reduce.ipynb`. This involves loading your data into a notebook and then finishing the Tall & Skinny SVD. 

#### Getting Database Access Credentials onto your laptop and Farmshare account

1. Open a terminal window on your laptop. In the shell, run this command:  
    `echo -n -e "\033]0;LAPTOP\007"`

2. Open another terminal window. Login to FarmShare. [or Sherlock, if you have an account there]  In the shell, run this command:
    `echo -n -e "\033]0;FARMSHARE\007"`

3. [LAPTOP WEB BROWSER] Download the security credentials from Canvas > Files > Homework. (On Mac, the file will end up in your `~/Downloads/` directory.)

4. [LAPTOP terminal] On your laptop at your login directory:  
	`mkdir .config/gcloud`  
	`cp ~/Downloads/stanford-stats-285-donoho-0dc233389eb9.json ~/.config/gcloud/`

5. [FARMSHARE terminal] On FarmShare at your login directory:  
	`mkdir .config/gcloud`  
	`scp  ~/Downloads/stanford-stats-285-donoho-0dc233389eb9.json su_id@rice.stanford.edu:~/.config/gcloud/`

#### Running code on a FarmShare/Sherlock

*the following commands are all inside the [FARMSHARE terminal] window*

1. Clone the HW repository. (Note: Its name has changed.):  
	`git clone https://github.com/adonoho/Stats285_F23`

2. Change directory to  
	`cd Stats285_F23/`

3. Examine the contents; does it look modestly familiar?
4.  Personalize the environment for your Stanford ID (Replace `SU_ID` with your actual Stanford ID.):  
	`export TABLE_NAME=SU_ID_hw5`

5. Check if the `conda` environment `stats285` is still around?  
```
	ml anaconda3/2023.07
	conda env list
```

5. If so, delete it:  
	`conda env remove --name stats285`

6. Create a new environment:  
	`conda env create --name stats285 --file environment.yml`  
	(This can take a few minutes.)

7. Turn it on:  
	`source activate stats285`  
	(Note, FarmShare is different from other Unix/Linux shells.)

8. Execute `map_function.py` on an array of nodes:  
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
9. Upon completion, about 2 minutes, look inside `hw5_array.err`.  
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
10. Now we will gather the results together on the login node and send them to GBQ. (GBQ will need a `table_name`, `su_id_hw5` in the example below.):
```
	python3 gather_csv_to_gbq.py ${TABLE_NAME} *.csv
```
`gather_csv_to_gbq.py` will log its command line arguments and will be followed by GBQ acknowledging the receipt of 1000 rows of data.
```
	INFO:root:gather_csv_to_gbq.py su_id_hw5 su_id_hw5_000.csv su_id_hw5_100.csv su_id_hw5_200.csv su_id_hw5_300.csv su_id_hw5_400.csv su_id_hw5_500.csv su_id_hw5_600.csv su_id_hw5_700.csv su_id_hw5_800.csv su_id_hw5_900.csv
	1000 out of 1000 rows loaded.
```

11. While it is important to know how your local supercomputer works, it is more important to maintain a common workflow. The `sbatch array` is a very different kind of wrapping code and introduces its own complexity of distributed filesystem mediated communication. The EMS system, exploited in `main.py`, runs the same on your laptop and on a large node on FarmShare. This symmetry builds confidence that you are going to get the same answer only faster. As you will see, EMS also launches a cluster on FarmShare with very modest changes and no complex `sbatch` scripting. 
   
    ####
    After, run the following command:  
`sbatch hw5_large.sh`  
`squeue -u $USER`  
    ####
    A line similar to the following should be displayed:
    ```
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
           2422892    normal hw5_larg  adonoho  R       1:28      1 wheat12
    ```

12. In `main.py`, comment out lines 110-111, `do_local_experiment()` and uncomment lines 112-113, `do_cluster_experiment()`. Run the following command:  
`sbatch hw5_cluster.sh`  
`squeue -u $USER`  
Lines similar to the following should be displayed:
```
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
           2422900    normal dask-wor  adonoho  R       0:05      1 wheat12
           2422901    normal dask-wor  adonoho  R       0:05      1 wheat12
           2422902    normal dask-wor  adonoho  R       0:05      1 wheat13
           2422903    normal dask-wor  adonoho  R       0:05      1 wheat13
           2422904    normal dask-wor  adonoho  R       0:05      1 wheat14
           2422897    normal dask-wor  adonoho  R       0:08      1 wheat08
           2422898    normal dask-wor  adonoho  R       0:08      1 wheat10
           2422899    normal dask-wor  adonoho  R       0:08      1 wheat11
           2422896    normal hw5_clus  adonoho  R       0:22      1 wheat08
```

13. Both versions of the EMS code produce similar logs in `hw5_large.err` and `hw5_cluster.err`. Here's an example from the cluster:
```
INFO:root:#!/usr/bin/env bash

#SBATCH -J dask-worker
#SBATCH -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=4G
#SBATCH -t 00:15:00

/home/adonoho/.conda/envs/stats285/bin/python3 -m distributed.cli.dask_worker tcp://171.67.51.68:44039 --nthreads 8 --memory-limit 4.00GiB --name dummy-name --nanny --death-timeout 60

INFO:EMS.manager:<Client: 'tcp://171.67.51.68:44039' processes=0 threads=0, memory=0 B>
ERROR:EMS.manager:Reason: 404 Not found: Table stanford-stats-285-donoho:EMS.stats285_su_ID_slurm_cluster_2_hw5_1000_blocks was not found in location US

Location: US
Job ID: 2b4f24b6-7361-4884-b160-58dc6877eea9

INFO:EMS.manager:Number of Instances to calculate: 1000
INFO:EMS.manager:Count: 10; Time: 12; Seconds/Instance: 1.2081; Remaining (s): 1196; Remaining Count: 990
INFO:EMS.manager:   nrow  ncol  seed  v_alignment  ...     ve996     ve997     ve998     ve999
0  1000  1000   748    -0.999943  ...  0.031577 -0.031767  0.031941 -0.031332

[1 rows x 1004 columns]
INFO:EMS.manager:Count: 20; Time: 12; Seconds/Instance: 0.6092; Remaining (s): 597; Remaining Count: 980
INFO:EMS.manager:   nrow  ncol  seed  v_alignment  ...     ve996     ve997     ve998     ve999
0  1000  1000   271    -0.999943  ...  0.032514 -0.031106  0.031448 -0.030869

[1 rows x 1004 columns]
INFO:EMS.manager:Count: 30; Time: 13; Seconds/Instance: 0.4340; Remaining (s): 421; Remaining Count: 970
INFO:EMS.manager:   nrow  ncol  seed  v_alignment  ...     ve996     ve997     ve998     ve999
0  1000  1000    48    -0.999942  ...  0.031642 -0.031573  0.031408 -0.031282

[1 rows x 1004 columns]
INFO:EMS.manager:Count: 40; Time: 13; Seconds/Instance: 0.3375; Remaining (s): 324; Remaining Count: 960
INFO:EMS.manager:   nrow  ncol  seed  v_alignment  ...     ve996     ve997     ve998     ve999
0  1000  1000   782    -0.999944  ...  0.032201 -0.031003  0.032151 -0.031873

[1 rows x 1004 columns]
INFO:EMS.manager:Count: 50; Time: 14; Seconds/Instance: 0.2756; Remaining (s): 262; Remaining Count: 950
INFO:EMS.manager:   nrow  ncol  seed  v_alignment  ...     ve996     ve997    ve998    ve999
0  1000  1000   433    -0.999945  ...  0.031583 -0.031511  0.03167 -0.03145

[1 rows x 1004 columns]
```
It starts by sharing the `sbatch` script it used to create the workers. Then, every ten calculations it posts some performance metrics, Seconds/Instance is of particular interest. It allows you to project how long each invocation of your experiment will likely take. In this case, it took about 77 seconds to calculate 1000 SVDs. Here is the end of the file:
```
WARNING:EMS.manager:batch_result(): Early Push: Length of DataFrames: 200
WARNING:EMS.manager:_push_to_database(): Number of DataFrames: 200; Length of DataFrames: 200
     nrow  ncol  seed  v_alignment  ...     ve996     ve997     ve998     ve999
0    1000  1000   690    -0.999945  ...  0.031443 -0.031443  0.031531 -0.031859
1    1000  1000   654    -0.999947  ...  0.031676 -0.031047  0.031915 -0.031524
2    1000  1000   954    -0.999946  ...  0.032172 -0.031818  0.031603 -0.030853
3    1000  1000    65    -0.999943  ...  0.030796 -0.031628  0.031248 -0.031469
4    1000  1000   178    -0.999945  ...  0.031113 -0.031387  0.031530 -0.031435
..    ...   ...   ...          ...  ...       ...       ...       ...       ...
195  1000  1000   161    -0.999945  ...  0.032281 -0.031565  0.031443 -0.031374
196  1000  1000   505    -0.999943  ...  0.031187 -0.031334  0.031931 -0.031603
197  1000  1000   268    -0.999943  ...  0.031281 -0.031061  0.031392 -0.031837
198  1000  1000   142    -0.999939  ...  0.031596 -0.031979  0.030816 -0.031810
199  1000  1000   921    -0.999947  ...  0.031462 -0.031619  0.031765 -0.031319

[200 rows x 1004 columns]
INFO:pandas_gbq.gbq:^M200 out of 200 rows loaded.
INFO:EMS.manager:Performed experiment in 77.0673 seconds
INFO:EMS.manager:Count: 1000, Seconds/Instance: 0.0771
45.83user 2.99system 1:34.08elapsed 51%CPU (0avgtext+0avgdata 462232maxresident)k
760408inputs+40288outputs (245major+500911minor)pagefaults 0swaps
```
#### Performing Analysis with Google Colab.

1. Open the `hw5_reduce.ipynb` notebook on the Github website.
2. Click the 'Open in Colab' button.
3. Run the code in the notebook. 
    * This code will read the data from the cloud database and perform the Tall & Skinny SVD to form
      an approximation of `v_true` (defined in the `generate_data` function of `map_function.py`) 
      using `vt` which is the top right singular vector of the data matrix formed by collecting
      1000 different noisy measurements of the underlying $1000 \times 1000$ matrix.
4. Compare the accuracy of using this `vt` to that obtained 
   from using only one approximation formed using one $1000 x 1000$ matrix.

#### Submitting on Canvas
To get credit for this homework, you should submit the following on Canvas:

1. **Short Answer:** Answer the following quests and submit them as a PDF file on Canvas.
   * Read the `main.py` file. Explain what the `generate_data`, `experiment`, `build_params`, `do_cluster_experiment`,
     and `do_local_experiment` functions do and how they interact with one another.
   * Compare the output files from running `do_local_experiment` and `do_cluster_experiment`. How much time did each
     each take?
   * Compare the accuracy from using `vt` to estimate `v_true` in `hw5.ipynb` to that obtained from using only one 
     approximation formed using one $1000 \times 1000$ matrix in earlier homeworks.
   * Describe your experiences with this homework. What parts had the most "friction"? Which parts felt the most
     "frictionless"?
2. **Files:** Submit the following files on Canvas:
   * `hw5_large.err` (You can either `scp` it from the cluster or copy-and-paste its contents from terminal)
   * `hw5_cluster.err` (You can either `scp` it from the cluster or copy-and-paste its contents from terminal)
   * Screenshots of your outputs in `hw5_reduce.ipynb`.
   * On Google Colab, click File -> Download -> Download .ipynb. Submit the downloaded notebook (which should contain
     your edits and outputs).


