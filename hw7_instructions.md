# Homework 7. XYZ -- Capstone Homework Assignment …

We spent the semester building up to this assignment. We will now conduct an XYZ experiment with multiple data sets, multiple algorithms, multiple hyperparameter settings and multiple observables.
In this homework you will use the framework we constructed for you, to execute this pattern. We hope that we are able to convince you that this emerging computational paradigm can be mostly painless.

## Overview

Our homework has two phases. The first places you in control of the parameter scanning process. The second phase turns control over to Google's Vizier. As defined in our lectures, an XYZ experiment applies several algorithms across several data sets across a parameter range. Also in lectures, we discussed the outperformance of boosted trees on tabular data. This homework allows you to explore this outperformance for yourself. We will focus on the XGBoost and LightGBM packages; in principle a state-of-the-art experiment would have to include also some deep learning competitors, but we already know that those methods probably still don't outerperform, and so to save time and money we maintain our focus. Note: you may think that two different algorithms is too few to be studying. We agree, and we originally wanted to study more algos. When you look at the code, you will see vestiges of our attempts to use CatBoost. CatBoost crashes for some values of the parameter set. It is an exercise left for the student, not required to pass the course, to fix the CatBoost code.

There are at least two problems we address in conducting an automated XYZ experiment. First, we need to wrangle the data sets into an experimentally-friendly form. We therefore pre-installed them for you in Google BigQuery (GBQ). As GBQ charges us per query and per size of the results, we aim to read BigQuery only once per data run. (Also, these databases are somewhat large; one is over 100 MB in size.) Our supplied homework app first reads the data into the cluster; each node can then later access the data from the cluster. Second, each raw data set needs to be wrangled into a form suitable for each of the algorithms. Our function `normalize_dataset()` accomplishes the wrangling.

Our experiment implmenentation code provides an engine that runs the same code for each XYZ hyperparameter instance. It algorithm and returns a `DataFrame` with the input parameters and output results. In a more thorough experiment, one might also track execution time, memory use, and other performance criteria. When we are using EMS, the returned results will be written to BigQuery and we afterwards will start the next computation. When we are using Vizier, the data are written to both BigQuery and Vizier; Vizier then makes its next guess (in Viziereses "suggestion"), and we try again. (When we are using Vizier, we actually have one computation per node running. Hence, Vizier starts refining its guesses based upon values that return quickly. We have seen it declare optimality before longer running computations finish.)

#### `xyz_ems.sbatch`

The EMS experiment is quite similar to our prior homework exercises:
- Read configuration and create cluster.
- Send different parameters to the same function throughout the cluster.
- Return data to the database.

Nonetheless, the heart of the science is in the `experiment()` function:
```
def experiment(*, url: str, boost: str, depth: int, reg_lambda: float, learning_rate: float, num_rounds: int) -> DataFrame:
    df = get_local_dataset(url)
    df, y_df = normalize_dataset(url, df)
    return experiment_local(url=url, X_df=df, y_df=y_df, boost=boost,
                            depth=depth, reg_lambda=reg_lambda, learning_rate=learning_rate, num_rounds=num_rounds)
```
As described above, it reads the data, normalizes it and then runs the algorithm on it. As there is little science in `get_local_dataset()` we will ignore it for the moment. (If you want to see simple caching/memoization in action, the code is easily followed.) `normalize_dataset()` will convert each DataFrame into one that each implemented algorithm is set up to handle.
```
def normalize_dataset(url: str, df: DataFrame) -> (DataFrame, DataFrame):
    match url:
        case StudyURL.UCIML_ADULT_INCOME:
            y_df = df[['income']]
            X_df = df.drop('income', axis=1)
        case StudyURL.KAGGLE_CALIFORNIA_HOUSING_PRICES:
            y_df = df[['median_house_value']]
            X_df = df.drop('median_house_value', axis=1)
        case StudyURL.UCIML_FOREST_COVERTYPE:
            y_df = df[['Cover_Type']]
            X_df = df.drop('Cover_Type', axis=1)
        case StudyURL.KAGGLE_HIGGS_BOSON_TRAINING | StudyURL.KAGGLE_HIGGS_BOSON_TEST:
            y_df = df[['Label']]
            X_df = df.drop('Label', axis=1)
        case _:
            raise Exception("Invalid Dataset Name!")
    X_df = category_encode(X_df)
    return X_df, y_df
```
As before, `category_encode()` converts categories into bitfields.
```
def category_encode(df: DataFrame) -> DataFrame:
    # Select object columns
    object_cols = df.select_dtypes(include='object').columns

    # One-hot encode these columns
    df_encoded = pd.get_dummies(df, columns=object_cols)

    # Preview
    logger.info(f'{df_encoded.head()}')

    return df_encoded
```
With each dataset normalized, we are ready to run the Boost algorithms.
```
def experiment_local(*, url: str, X_df: DataFrame, y_df: DataFrame, boost: str,
                     depth: int, reg_lambda: float, learning_rate: float, num_rounds: int) -> DataFrame:
    logger.warning(f'url: {url}; boost: {boost}\n{depth}, {reg_lambda}, {learning_rate}, {num_rounds}')
    # Create data array
    X = X_df.values

    # Convert y into target array
    y_array = y_df.iloc[:, 0].to_numpy()

    # Create target vector
    if np.issubdtype(y_array.dtype, np.number):
        y = y_array
        num_classes = 1
        obj_type = 'reg'
    else:
        # If y is categorical (including strings), use LabelEncoder for encoding
        encoder = LabelEncoder()
        y = encoder.fit_transform(y_array)
        num_classes = len(encoder.classes_)
        obj_type = 'bin' if num_classes == 2 else 'mult'

    # Split into train and test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    match boost:
        case StudyBOOST.XGBOOST:
            xgb_params = {'learning_rate': learning_rate, 'reg_lambda': reg_lambda,
                          'max_depth': depth, 'n_estimators': num_rounds}
            match obj_type:
                case 'reg':
                    xgb_params['objective'] = 'reg:squarederror'
                case 'bin':
                    xgb_params['objective'] = 'binary:logistic'
                case 'mult':
                    xgb_params['objective'] = 'multi:softprob'
                    xgb_params['num_classes'] = num_classes
            model = xgb.XGBRegressor(**xgb_params) if obj_type == 'reg' else xgb.XGBClassifier(**xgb_params)
        case StudyBOOST.CATBOOST:
            model = catboost.CatBoostClassifier(learning_rate=learning_rate,
                                                l2_leaf_reg=reg_lambda,
                                                depth=depth,
                                                iterations=num_rounds,
                                                silent=True)
        case StudyBOOST.LIGHTGBM:
            model = lgb.LGBMClassifier(learning_rate=learning_rate,
                                       lambda_l2=reg_lambda,
                                       max_depth=depth,
                                       n_estimators=num_rounds,
                                       verbose=-1)
        case _:
            raise Exception("Invalid Method Name!")
    model.fit(X_train, y_train)

    # Make predictions on the test set
    test_preds = model.predict(X_test)
    test_predictions = [1 if x > 0.5 else 0 for x in test_preds]
    test_accuracy = accuracy_score(y_test, test_predictions)

    return DataFrame(data={'url': url, 'boost': boost, 'depth': depth,
                           'reg_lambda': reg_lambda, 'learning_rate': learning_rate, 'num_rounds': num_rounds,
                           'test_accuracy': test_accuracy},
                     index=[0])
```
This is normal Python code, tested in a single threaded fashion on a laptop. You can easily see the parts of the code commented out that were used in development. (In general, you should not be in a hurry to delete your development code. You will never know when you may need to use it again. Those of you who are intrigued by the crashing of CatBoost will, most likely, find the leftover code useful.)

#### `xyz_vertex.sbatch`

[Google's Vizier service](https://console.cloud.google.com/vertex-ai/experiments/studies?orgonly=true&project=stanford-stats-285-donoho&supportedpurview=organizationId) is a subsidiary service within the general Vertex AI service. Your studies will appear on their [dashboard](https://console.cloud.google.com/vertex-ai/experiments/studies?orgonly=true&project=stanford-stats-285-donoho&supportedpurview=organizationId).

We use Dask to hide a huge amount of complexity. Our private library, EMS, due to Dask, is being used regularly to manage 1,000 node clusters. This requires a fancy scheduler and an asynchronous data transfer system. But the programming model has remained resolutely single threaded, as is most Python code you encounter. This is a *very good thing*. Yet, when we introduce a foreign server, such as Google Vizier, we can no longer ignore blocking I/O. Without going into detail about how Python's `async`/`await` keywords function, know that they are used to enable us to communicate with Vizier while not breaking our own communication with our cluster.

The function `calc_xyz_vertex_on_cluster_async()` is simpler than it appears. It is focused around two ideas. First, `push_suggestions_to_cluster()` pulls suggestions from Vizier and pushes them to the cluster to be calculated. This code path uses a sophisticated part of Dask that allows us to dynamically insert computations into the cluster after the work has started. Second, `push_result_to_vertex()` takes results from the cluster and pushes them up to Vizier. Here is the core of the interaction between Vizier and your cluster:
```
# Prime the cluster.
push_suggestions_to_cluster(2 * nodes)
i = 0
for df, key in ec:  # Start retiring trials.
	logger.info(f'Result: {df}.')
	# push_result_to_vertex(df, key)
	await IOLoop.current().run_in_executor(None, push_result_to_vertex, df, key)
	i += 1
	active_suggestions = len(in_cluster)
	logger.info(f'Completed computations: {i}; Pending: {active_suggestions}.')
	if i < MAX_NUM_ITERATIONS:
		# push_suggestions_to_cluster(nodes)
		await IOLoop.current().run_in_executor(None, push_suggestions_to_cluster, nodes)
	else:
		if active_suggestions > 0:
			logger.info(f'Unclaimed suggestions:\n{in_cluster}')
		break
```
Please do not be alarmed by the unexpected `await IOLoop.current().run_in_executor()` in the middle of your experiment. All it is doing is putting long running I/O tasks on a separate thread and is awaiting their completion. Basically, you are being polite to your cluster. Or put another way, without doing this, your cluster will crash when the heart beat functions come in to the scheduler and are not answered. Your code is now a transfer/control point between two complex machines -- your cluster and Vizier.

The other thing to notice is the loop's exit condition, `MAX_NUM_ITERATIONS`. It was a surprise to us that it is standard optimization practice to run for a fixed number of iterations. In fact, Sagi Perel suggested that one should multiply the number of parameters by 10 to make your first guess at an iteration limit. We have respected that observation while starting with twice the number of compute nodes to keep the cluster busy, `MAX_NUM_ITERATIONS = 6 * 10 + 2 * nodes`. This is significantly less than the 360 calculations run by the EMS example. 

Regardless, here is the complete asynchronous function:
```
async def calc_xyz_vertex_on_cluster_async(table_name: str, client: Client,
                                           nodes: int, credentials: service_account.Credentials):

    MAX_NUM_ITERATIONS = 6 * 10 + 2 * nodes  # Sagi Perel suggestion. Less than the 360 used in EMS example.
    study = get_vertex_study(study_id=table_name, credentials=credentials)
    ec = EvalOnCluster(client, table_name, credentials=credentials)
    in_cluster = {}

    def push_suggestions_to_cluster(count):
        logger.info(f'Call Vizier.')
        for suggestion in study.suggest(count=count):
            params = suggestion.materialize().parameters.as_dict()
            params['depth'] = round(params['depth'])
            params['num_rounds'] = round(params['num_rounds'])
            key = ec.key_from_params(params)
            if not in_cluster.get(key, None):  # Defend against duplicate computation.
                logger.info(f'EC Key: {key}\nParams: {params}')
                key = ec.eval_params(experiment, params)
                in_cluster[key] = suggestion
        logger.info(f'Pending computations: {len(in_cluster)}.')

    def push_result_to_vertex(df: DataFrame, key: tuple):
        logger.info(f'Push result to Vizier, EC Key: {key}')
        measurement = vz.Measurement()
        measurement.metrics['test_accuracy'] = df.iloc[0]['test_accuracy']
        suggestion = in_cluster.get(key, None)
        if suggestion is not None:
            suggestion.add_measurement(measurement=measurement)
            suggestion.complete(measurement=measurement)
            del in_cluster[key]
        else:
            logger.info(f'Key problem: {key}\n{in_cluster}')
        logger.info(f'End Push.')

    # Prime the cluster.
    push_suggestions_to_cluster(2 * nodes)
    i = 0
    for df, key in ec:  # Start retiring trials.
        logger.info(f'Result: {df}.')
        # push_result_to_vertex(df, key)
        await IOLoop.current().run_in_executor(None, push_result_to_vertex, df, key)
        i += 1
        active_suggestions = len(in_cluster)
        logger.info(f'Completed computations: {i}; Pending: {active_suggestions}.')
        if i < MAX_NUM_ITERATIONS:
            # push_suggestions_to_cluster(nodes)
            await IOLoop.current().run_in_executor(None, push_suggestions_to_cluster, nodes)
        else:
            if active_suggestions > 0:
                logger.info(f'Unclaimed suggestions:\n{in_cluster}')
            break
    logger.info('Finishing')
    ec.final_push()
    optimal_trials = study.optimal_trials()
    logger.info(f'{optimal_trials}')
```

## Instructions (Not yet done for HW7.)

#### Running code on FarmShare/Sherlock

1. Login to FarmShare.

2. Personalize the environment for your Stanford ID (Replace `su_id` with your actual Stanford ID.):  
	`export SU_ID=su_id_hw7`

2. Change directory to your project:  
	`cd Stats285_F23/`

1. Pull the latest version of the code:  
	`git pull`

5. Check if the `conda` environment `stats285` is still around?  
```
	ml anaconda3/2023.07
	conda env list
```

If so, delete it:  
	`conda env remove --name stats285`

6. Create a new environment:  
	`conda env create --name stats285 --file environment.yml`  
	(This can take a few minutes.)

7. Turn it on:  
	`source activate stats285`  
	(Note, FarmShare/Sherlock is different from other Unix/Linux shells.)

3. Examine the contents; does it look modestly familiar?
   
4.  Personalize the environment for your Stanford ID (Replace `SU_ID` with your actual Stanford ID.):  
	`export TABLE_NAME=SU_ID_hw5`

8. Execute `map_function.py` on an array of nodes:  
	`sbatch hw5_sbatch_array.sh`  
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
9. Upon completion, about 2 minutes, look inside `hw5_sbatch_array.err`.  
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
`sbatch hw5_dask_large.sh`  
`squeue -u $USER`  
    ####
    A line similar to the following should be displayed:
    ```
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
           2422892    normal hw5_larg  adonoho  R       1:28      1 wheat12
    ```

12. In `main.py`, comment out lines 110-111, `do_local_experiment()` and uncomment lines 112-113, `do_cluster_experiment()`. Run the following command:  
`sbatch hw5_dask_cluster.sh`  
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

13. Both versions of the EMS code produce similar logs in `hw5_dask_large.err` and `hw5_dask_cluster.err`. Here's an example from the cluster:
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
2. Click the 'Open in Colab' button. (Alternatively, you can go directly to [this link](https://colab.research.google.com/github/adonoho/Stats285_F23/blob/main/hw5_reduce.ipynb)).
   * *Warning:* By default, you will not be able to save changes (which we will ask you to make in next steps) to 
     this notebook. To save changes, you will need to make a copy of the notebook in your Google Drive by 
     clicking File -> Save a copy in Drive.
   * Make sure you are logged into your `suid@stanford.edu` Google account. Otherwise, you will not be able to read the
     from the GBQ database.
     **Edit the notebook changing the fragment** 'HW5_SUID_hw5' to something like 'HW5_suid_hw5' where suid denotes your Stanford ID.
3. Run the code in the notebook. 
    * This code will read the data from the cloud database and perform the Tall & Skinny SVD to form
      an approximation of `v_true` (defined in the `generate_data` function of `map_function.py`) 
      using `vt` which is the top right singular vector of the data matrix formed by collecting
      1000 different noisy measurements of the underlying $1000 \times 1000$ matrix.
4. Compare (a) the accuracy of using this `vt` to estimate `v_true` with (b) accuracy of the estimate obtained
   from using only one approximation formed using one $1000 \times 1000$ matrix in previous homeworks.

## Submitting on Canvas
To get credit for this homework, you should submit the following on Canvas:

1. **Short Answer:** Answer the following quests and submit them as a PDF file on Canvas.
   * Read the `main.py` file. For each function inside (`generate_data`, `experiment`, `build_params`, `do_cluster_experiment`,
     and `do_local_experiment`), describe what it does.
   * How do the functions in `main.py` interact with each other?
   * Using the outputs found in `hw5_sbatch_array.err`, `hw5_dask_large.err`, and `hw5_dask_cluster.err`;
     estimate how long each of their corresponding scripts took to run? Which one(s) were the fastest? 
     Which one(s) were the slowest? Explain why.
   * Compare the accuracy from using `vt` to estimate `v_true` in `hw5_reduce.ipynb` to that obtained from using only one 
     approximation formed using one $1000 \times 1000$ matrix in earlier homeworks.
   * Describe your experiences with this homework. What parts had the most "friction"? Which parts felt the most
     "frictionless"?
2. **Files:** Submit the following files on Canvas:
   * `hw5_sbatch_array.err`, `hw5_dask_large.err`, and `hw5_dask_cluster.err` (You can either `scp` them from the cluster or 
     copy-and-paste their contents from terminal)
   * Screenshots of your outputs in `hw5_reduce.ipynb`.
   * On Google Colab, click File -> Download -> Download .ipynb. Submit the downloaded notebook (which should contain
     your edits and outputs).
