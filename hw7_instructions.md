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

1. Login to FarmShare (see previous homeworks).

2. Personalize the environment for your Stanford ID 
	
	(Replace `su_id` with your actual Stanford ID. For example, if you suid is `adonoho`, 
     then replace `su_id_hw7` with `adonoho_hw7`): 
	`export SU_ID=su_id_hw7`

2. Change directory to your project (recall we created this folder in hw5):  
	`cd Stats285_F23/`

1. Pull the latest version of the code:  
	`git pull`

5. Check if the `conda` environment `stats285` is still around?  
```
	ml anaconda3/2023.07
	conda env list
```

If so, delete it (this might take a few minutes to an hour):  
	`conda env remove --name stats285`

6. Create a new environment:  
	`conda env create --name stats285 --file environment.yml`  
	(This can take a few minutes to an hours.)

7. Turn it on:  
	`source activate stats285`  
	(Note, FarmShare/Sherlock is different from other Unix/Linux shells.)

8. Execute `xyz_ems.py` on an array of nodes:  
	`sbatch xyz_ems.sbatch`  
	`squeue -u $USER`
```
(stats285) adonoho@rice13:~/Stats285_F23$ squeue -u $USER
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
           2426605    normal  xyz_ems  adonoho  R       0:37      1 wheat09
           2426606    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426607    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426608    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426609    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426610    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426611    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426612    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426613    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426614    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426615    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426616    normal dask-wor  adonoho  R       0:14      1 wheat09
           2426617    normal dask-wor  adonoho  R       0:14      1 wheat08
           2426618    normal dask-wor  adonoho  R       0:14      1 wheat08
           2426619    normal dask-wor  adonoho  R       0:14      1 wheat08
           2426620    normal dask-wor  adonoho  R       0:14      1 wheat08
           2426621    normal dask-wor  adonoho  R       0:14      1 wheat08
```
9. Look inside `xyz_ems.err`. Using the following command:
	```
	cat xyz_ems.err
	```

	The beginning of the file:  
	```
	INFO:root:#!/usr/bin/env bash
	
	#SBATCH -J dask-worker
	#SBATCH -n 1
	#SBATCH --cpus-per-task=1
	#SBATCH --mem=4G
	#SBATCH -t 24:00:00
	
	/home/adonoho/.conda/envs/stats285/bin/python3 -m distributed.cli.dask_worker tcp://171.67.51.69:46403 --nthreads 1 --memory-limit 4.00GiB --name dummy-name --nanny --death-timeout 60
	
	INFO:root:https://archive.ics.uci.edu/dataset/2/adult
		   age  workclass  fnlwgt  ... hours_per_week  native_country income
	0       54          ?  148657  ...             40          Mexico  <=50K
	1       32    Private  112137  ...             40        Cambodia  <=50K
	2       46    Private  225065  ...             40          Mexico  <=50K
	3       64    Private  213391  ...             40   United-States  <=50K
	4       67    Private  142097  ...              6   United-States  <=50K
	...    ...        ...     ...  ...            ...             ...    ...
	48837   20    Private   86143  ...             30   United-States  <=50K
	48838   48    Private  350440  ...             40        Cambodia   >50K
	48839   22  Local-gov  195532  ...             43   United-States  <=50K
	48840   20    Private  176321  ...             20   United-States  <=50K
	48841   43  State-gov  255835  ...             40   United-States  <=50K
	
	[48842 rows x 15 columns]
	INFO:root:https://www.kaggle.com/datasets/camnugent/california-housing-prices
		   longitude  latitude  ...  median_house_value  ocean_proximity
	0        -116.00     33.19  ...             51300.0           INLAND
	1        -116.00     32.74  ...             43900.0           INLAND
	2        -116.00     34.12  ...             57700.0           INLAND
	3        -120.00     38.52  ...            140600.0           INLAND
	4        -120.00     38.93  ...            313400.0           INLAND
	...          ...       ...  ...                 ...              ...
	20635    -119.34     34.39  ...            231300.0       NEAR OCEAN
	20636    -123.59     38.80  ...            176100.0       NEAR OCEAN
	20637    -119.84     34.44  ...            274300.0       NEAR OCEAN
	20638    -119.84     34.45  ...            331200.0       NEAR OCEAN
	20639    -123.84     39.83  ...            145800.0       NEAR OCEAN
	
	[20640 rows x 10 columns]
	```  
	The start of computation …  
	```
	ERROR:EMS.manager:Reason: 404 Not found: Table stanford-stats-285-donoho:EMS.XYZ_EMS_adonoho_hw7 was not found in location US
	
	Location: US
	Job ID: c69f4d20-bc23-42d3-91dd-b94151d55481
	
	INFO:EMS.manager:Number of Instances to calculate: 360
	INFO:EMS.manager:Count: 10; Time: 52; Seconds/Instance: 5.1607; Remaining (s): 1806; Remaining Count: 350
	INFO:EMS.manager:                                             url  ... test_accuracy
	0  https://www.kaggle.com/c/higgs-boson/training  ...           1.0
	
	[1 rows x 7 columns]
	WARNING:EMS.manager:_push_to_database(): Number of DataFrames: 12; Length of DataFrames: 12
													  url  ... test_accuracy
	0   https://www.kaggle.com/datasets/camnugent/cali...  ...      0.000000
	1   https://www.kaggle.com/datasets/camnugent/cali...  ...      0.000000
	2         https://archive.ics.uci.edu/dataset/2/adult  ...      0.875320
	3         https://archive.ics.uci.edu/dataset/2/adult  ...      0.876446
	4   https://www.kaggle.com/datasets/camnugent/cali...  ...      0.000000
	5       https://www.kaggle.com/c/higgs-boson/training  ...      1.000000
	6         https://archive.ics.uci.edu/dataset/2/adult  ...      0.874092
	7       https://www.kaggle.com/c/higgs-boson/training  ...      1.000000
	8         https://archive.ics.uci.edu/dataset/2/adult  ...      0.871532
	9       https://www.kaggle.com/c/higgs-boson/training  ...      1.000000
	10   https://archive.ics.uci.edu/dataset/31/covertype  ...      0.685912
	11      https://www.kaggle.com/c/higgs-boson/training  ...      1.000000
	
	[12 rows x 7 columns]
	INFO:pandas_gbq.gbq:
	12 out of 12 rows loaded.
	INFO:EMS.manager:Count: 20; Time: 64; Seconds/Instance: 3.2122; Remaining (s): 1092; Remaining Count: 340
	INFO:EMS.manager:                                                 url  ... test_accuracy
	0  https://www.kaggle.com/datasets/camnugent/cali...  ...           0.0
	
	[1 rows x 7 columns]
	INFO:EMS.manager:Count: 30; Time: 76; Seconds/Instance: 2.5364; Remaining (s): 837; Remaining Count: 330
	INFO:EMS.manager:                                                 url  ... test_accuracy
	0  https://www.kaggle.com/datasets/camnugent/cali...  ...           0.0
	
	[1 rows x 7 columns]
	```
	The end of the file:  
	```
	WARNING:EMS.manager:_push_to_database(): Number of DataFrames: 4; Length of DataFrames: 4
													 url  ... test_accuracy
	0        https://archive.ics.uci.edu/dataset/2/adult  ...      0.863548
	1  https://www.kaggle.com/datasets/camnugent/cali...  ...      0.000000
	2  https://www.kaggle.com/datasets/camnugent/cali...  ...      0.000000
	3  https://www.kaggle.com/datasets/camnugent/cali...  ...      0.000000
	
	[4 rows x 7 columns]
	INFO:pandas_gbq.gbq:
	4 out of 4 rows loaded.
	INFO:EMS.manager:Performed experiment in 4122.9516 seconds
	INFO:EMS.manager:Count: 360, Seconds/Instance: 11.4526
	135.71user 37.15system 1:09:25elapsed 4%CPU (0avgtext+0avgdata 1175392maxresident)k
	1128128inputs+4496outputs (381major+855550minor)pagefaults 0swaps
	```
	On average, while using 16 nodes, EMS took 183 seconds per experiment, `4122.9516s / 360instances * 16 instances/cluster`.

   12. Now, let us do the same experiment but let Vizier drive the computation:  
       `sbatch xyz_vertex.sbatch`  
       `squeue -u $USER`
	   Lines similar to the following should be displayed:
		```
		(stats285) adonoho@rice13:~/Stats285_F23$ squeue -u $USER
					 JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
				   2426587    normal xyz_vert  adonoho  R       4:56      1 wheat08
				   2426588    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426589    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426590    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426591    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426592    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426593    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426594    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426595    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426596    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426597    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426598    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426599    normal dask-wor  adonoho  R       4:01      1 wheat08
				   2426600    normal dask-wor  adonoho  R       4:01      1 wheat09
				   2426601    normal dask-wor  adonoho  R       4:01      1 wheat09
				   2426602    normal dask-wor  adonoho  R       4:01      1 wheat09
				   2426603    normal dask-wor  adonoho  R       4:01      1 wheat09
		```
9. Look inside `xyz_vertex.err`.   Using the following command:
	```
	cat xyz_vertex.err
	```
	The beginning of the file:  
	```
	INFO:root:#!/usr/bin/env bash
	
	#SBATCH -J dask-worker
	#SBATCH -n 1
	#SBATCH --cpus-per-task=1
	#SBATCH --mem=4G
	#SBATCH -t 24:00:00
	
	/home/adonoho/.conda/envs/stats285/bin/python3 -m distributed.cli.dask_worker tcp://171.67.51.68:42485 --nthreads 1 --memory-limit 4.00GiB --name dummy-name --nanny --death-timeout 60
	
	INFO:root:https://archive.ics.uci.edu/dataset/2/adult
		   age  workclass  fnlwgt  ... hours_per_week  native_country income
	0       54          ?  148657  ...             40          Mexico  <=50K
	1       32    Private  112137  ...             40        Cambodia  <=50K
	2       46    Private  225065  ...             40          Mexico  <=50K
	3       64    Private  213391  ...             40   United-States  <=50K
	4       67    Private  142097  ...              6   United-States  <=50K
	...    ...        ...     ...  ...            ...             ...    ...
	48837   20    Private   86143  ...             30   United-States  <=50K
	48838   48    Private  350440  ...             40        Cambodia   >50K
	48839   22  Local-gov  195532  ...             43   United-States  <=50K
	48840   20    Private  176321  ...             20   United-States  <=50K
	48841   43  State-gov  255835  ...             40   United-States  <=50K
	
	[48842 rows x 15 columns]
	INFO:root:https://www.kaggle.com/datasets/camnugent/california-housing-prices
		   longitude  latitude  ...  median_house_value  ocean_proximity
	0        -116.00     33.19  ...             51300.0           INLAND
	1        -116.00     32.74  ...             43900.0           INLAND
	2        -116.00     34.12  ...             57700.0           INLAND
	3        -120.00     38.52  ...            140600.0           INLAND
	4        -120.00     38.93  ...            313400.0           INLAND
	...          ...       ...  ...                 ...              ...
	20635    -119.34     34.39  ...            231300.0       NEAR OCEAN
	20636    -123.59     38.80  ...            176100.0       NEAR OCEAN
	20637    -119.84     34.44  ...            274300.0       NEAR OCEAN
	20638    -119.84     34.45  ...            331200.0       NEAR OCEAN
	20639    -123.84     39.83  ...            145800.0       NEAR OCEAN
	
	[20640 rows x 10 columns]
	```
	The start of computation …  
	```
	INFO:absl:Adding child parameters {'reg_lambda'} to 1 subspaces 
	INFO:absl:Adding child parameters {'learning_rate'} to 1 subspaces 
	INFO:absl:Adding child parameters {'depth'} to 1 subspaces 
	INFO:absl:Adding child parameters {'num_rounds'} to 1 subspaces 
	INFO:absl:Adding child parameters {'url'} to 1 subspaces 
	INFO:absl:Adding child parameters {'boost'} to 1 subspaces 
	INFO:root:Call Vizier.
	INFO:google.cloud.aiplatform.vizier.study:Suggest Study study backing LRO: projects/21106255545/locations/us-central1/studies/323251796053/operations/323251796053__1
	INFO:google.cloud.aiplatform.vizier.study:<class 'google.cloud.aiplatform_v1.services.vizier_service.client.VizierServiceClient'>
	INFO:google.cloud.aiplatform.vizier.study:Study study suggested. Resource name: projects/21106255545/locations/us-central1/studies/323251796053
	INFO:root:EC Key: ('lightgbm', 8, 0.55, 50, 2.125, 'https://archive.ics.uci.edu/dataset/2/adult')
	Params: {'boost': 'lightgbm', 'depth': 8, 'learning_rate': 0.55, 'num_rounds': 50, 'reg_lambda': 2.125, 'url': 'https://archive.ics.uci.edu/dataset/2/adult'}
	INFO:root:EC Key: ('xgboost', 10, 0.45018079057923976, 50, 1.5002472492923795, 'https://www.kaggle.com/c/higgs-boson/training')
	Params: {'boost': 'xgboost', 'depth': 10, 'learning_rate': 0.45018079057923976, 'num_rounds': 50, 'reg_lambda': 1.5002472492923795, 'url': 'https://www.kaggle.com/c/higgs-boson/training'}
	INFO:root:EC Key: ('xgboost', 6, 0.732120410548891, 50, 2.7035596087532916, 'https://www.kaggle.com/datasets/camnugent/california-housing-prices')
	Params: {'boost': 'xgboost', 'depth': 6, 'learning_rate': 0.732120410548891, 'num_rounds': 50, 'reg_lambda': 2.7035596087532916, 'url': 'https://www.kaggle.com/datasets/camnugent/california-housing-prices'}
	INFO:root:EC Key: ('lightgbm', 6, 0.9378906640804748, 50, 2.0014312881620313, 'https://archive.ics.uci.edu/dataset/31/covertype')
	Params: {'boost': 'lightgbm', 'depth': 6, 'learning_rate': 0.9378906640804748, 'num_rounds': 50, 'reg_lambda': 2.0014312881620313, 'url': 'https://archive.ics.uci.edu/dataset/31/covertype'}
	INFO:root:EC Key: ('xgboost', 6, 0.5839490038051907, 50, 1.2550818377736495, 'https://archive.ics.uci.edu/dataset/31/covertype')
	Params: {'boost': 'xgboost', 'depth': 6, 'learning_rate': 0.5839490038051907, 'num_rounds': 50, 'reg_lambda': 1.2550818377736495, 'url': 'https://archive.ics.uci.edu/dataset/31/covertype'}
	INFO:root:EC Key: ('lightgbm', 8, 0.6440422069033257, 50, 1.6276452112558346, 'https://www.kaggle.com/datasets/camnugent/california-housing-prices')
	Params: {'boost': 'lightgbm', 'depth': 8, 'learning_rate': 0.6440422069033257, 'num_rounds': 50, 'reg_lambda': 1.6276452112558346, 'url': 'https://www.kaggle.com/datasets/camnugent/california-housing-prices'}
	INFO:root:EC Key: ('lightgbm', 6, 0.31744527196580163, 50, 2.7051093651867184, 'https://www.kaggle.com/c/higgs-boson/training')
	Params: {'boost': 'lightgbm', 'depth': 6, 'learning_rate': 0.31744527196580163, 'num_rounds': 50, 'reg_lambda': 2.7051093651867184, 'url': 'https://www.kaggle.com/c/higgs-boson/training'}
	INFO:root:EC Key: ('xgboost', 10, 0.2295345871709696, 50, 3.455495947166911, 'https://archive.ics.uci.edu/dataset/2/adult')
	Params: {'boost': 'xgboost', 'depth': 10, 'learning_rate': 0.2295345871709696, 'num_rounds': 50, 'reg_lambda': 3.455495947166911, 'url': 'https://archive.ics.uci.edu/dataset/2/adult'}
	INFO:root:EC Key: ('xgboost', 6, 0.9575220966227492, 50, 1.1073796544848755, 'https://archive.ics.uci.edu/dataset/2/adult')
	Params: {'boost': 'xgboost', 'depth': 6, 'learning_rate': 0.9575220966227492, 'num_rounds': 50, 'reg_lambda': 1.1073796544848755, 'url': 'https://archive.ics.uci.edu/dataset/2/adult'}
	INFO:root:EC Key: ('lightgbm', 8, 0.539608041858728, 50, 1.3988017852260832, 'https://www.kaggle.com/datasets/camnugent/california-housing-prices')
	Params: {'boost': 'lightgbm', 'depth': 8, 'learning_rate': 0.539608041858728, 'num_rounds': 50, 'reg_lambda': 1.3988017852260832, 'url': 'https://www.kaggle.com/datasets/camnugent/california-housing-prices'}
	INFO:root:EC Key: ('lightgbm', 10, 0.21045844620837129, 50, 0.5552733772530185, 'https://archive.ics.uci.edu/dataset/31/covertype')
	Params: {'boost': 'lightgbm', 'depth': 10, 'learning_rate': 0.21045844620837129, 'num_rounds': 50, 'reg_lambda': 0.5552733772530185, 'url': 'https://archive.ics.uci.edu/dataset/31/covertype'}
	INFO:root:EC Key: ('lightgbm', 10, 0.4543621438395158, 50, 3.2986838492476362, 'https://archive.ics.uci.edu/dataset/31/covertype')
	Params: {'boost': 'lightgbm', 'depth': 10, 'learning_rate': 0.4543621438395158, 'num_rounds': 50, 'reg_lambda': 3.2986838492476362, 'url': 'https://archive.ics.uci.edu/dataset/31/covertype'}
	INFO:root:EC Key: ('xgboost', 8, 0.9582659615559587, 50, 3.881355942788213, 'https://www.kaggle.com/c/higgs-boson/training')
	Params: {'boost': 'xgboost', 'depth': 8, 'learning_rate': 0.9582659615559587, 'num_rounds': 50, 'reg_lambda': 3.881355942788213, 'url': 'https://www.kaggle.com/c/higgs-boson/training'}
	INFO:root:EC Key: ('xgboost', 8, 0.34367778995114917, 50, 1.2913768005643165, 'https://www.kaggle.com/datasets/camnugent/california-housing-prices')
	Params: {'boost': 'xgboost', 'depth': 8, 'learning_rate': 0.34367778995114917, 'num_rounds': 50, 'reg_lambda': 1.2913768005643165, 'url': 'https://www.kaggle.com/datasets/camnugent/california-housing-prices'}
	INFO:root:EC Key: ('lightgbm', 10, 0.7514220574065439, 50, 0.9292980414014104, 'https://www.kaggle.com/c/higgs-boson/training')
	Params: {'boost': 'lightgbm', 'depth': 10, 'learning_rate': 0.7514220574065439, 'num_rounds': 50, 'reg_lambda': 0.9292980414014104, 'url': 'https://www.kaggle.com/c/higgs-boson/training'}
	INFO:root:EC Key: ('xgboost', 6, 0.7888275754708014, 50, 0.4864532010665985, 'https://www.kaggle.com/c/higgs-boson/training')
	Params: {'boost': 'xgboost', 'depth': 6, 'learning_rate': 0.7888275754708014, 'num_rounds': 50, 'reg_lambda': 0.4864532010665985, 'url': 'https://www.kaggle.com/c/higgs-boson/training'}
	INFO:root:EC Key: ('xgboost', 8, 0.1109200834494655, 50, 2.3956399674195703, 'https://archive.ics.uci.edu/dataset/31/covertype')
	Params: {'boost': 'xgboost', 'depth': 8, 'learning_rate': 0.1109200834494655, 'num_rounds': 50, 'reg_lambda': 2.3956399674195703, 'url': 'https://archive.ics.uci.edu/dataset/31/covertype'}
	INFO:root:EC Key: ('xgboost', 8, 0.14115867295860712, 50, 3.901439263950875, 'https://archive.ics.uci.edu/dataset/31/covertype')
	Params: {'boost': 'xgboost', 'depth': 8, 'learning_rate': 0.14115867295860712, 'num_rounds': 50, 'reg_lambda': 3.901439263950875, 'url': 'https://archive.ics.uci.edu/dataset/31/covertype'}
	INFO:root:EC Key: ('xgboost', 6, 0.9941588881278478, 50, 3.817822838974222, 'https://archive.ics.uci.edu/dataset/31/covertype')
	Params: {'boost': 'xgboost', 'depth': 6, 'learning_rate': 0.9941588881278478, 'num_rounds': 50, 'reg_lambda': 3.817822838974222, 'url': 'https://archive.ics.uci.edu/dataset/31/covertype'}
	INFO:root:EC Key: ('xgboost', 8, 0.31844189437443704, 50, 1.57897699926561, 'https://archive.ics.uci.edu/dataset/2/adult')
	Params: {'boost': 'xgboost', 'depth': 8, 'learning_rate': 0.31844189437443704, 'num_rounds': 50, 'reg_lambda': 1.57897699926561, 'url': 'https://archive.ics.uci.edu/dataset/2/adult'}
	INFO:root:EC Key: ('lightgbm', 10, 0.1680943606365825, 50, 3.905196784623627, 'https://www.kaggle.com/datasets/camnugent/california-housing-prices')
	Params: {'boost': 'lightgbm', 'depth': 10, 'learning_rate': 0.1680943606365825, 'num_rounds': 50, 'reg_lambda': 3.905196784623627, 'url': 'https://www.kaggle.com/datasets/camnugent/california-housing-prices'}
	INFO:root:EC Key: ('xgboost', 8, 0.39828192456794, 50, 2.876826266061232, 'https://www.kaggle.com/datasets/camnugent/california-housing-prices')
	Params: {'boost': 'xgboost', 'depth': 8, 'learning_rate': 0.39828192456794, 'num_rounds': 50, 'reg_lambda': 2.876826266061232, 'url': 'https://www.kaggle.com/datasets/camnugent/california-housing-prices'}
	INFO:root:EC Key: ('xgboost', 8, 0.601470460919959, 50, 2.2808297795533874, 'https://archive.ics.uci.edu/dataset/31/covertype')
	Params: {'boost': 'xgboost', 'depth': 8, 'learning_rate': 0.601470460919959, 'num_rounds': 50, 'reg_lambda': 2.2808297795533874, 'url': 'https://archive.ics.uci.edu/dataset/31/covertype'}
	INFO:root:EC Key: ('xgboost', 8, 0.4548634707368746, 50, 3.8275033626959813, 'https://www.kaggle.com/datasets/camnugent/california-housing-prices')
	Params: {'boost': 'xgboost', 'depth': 8, 'learning_rate': 0.4548634707368746, 'num_rounds': 50, 'reg_lambda': 3.8275033626959813, 'url': 'https://www.kaggle.com/datasets/camnugent/california-housing-prices'}
	INFO:root:EC Key: ('lightgbm', 6, 0.9676577267092487, 50, 3.8829372911643665, 'https://www.kaggle.com/c/higgs-boson/training')
	Params: {'boost': 'lightgbm', 'depth': 6, 'learning_rate': 0.9676577267092487, 'num_rounds': 50, 'reg_lambda': 3.8829372911643665, 'url': 'https://www.kaggle.com/c/higgs-boson/training'}
	INFO:root:EC Key: ('xgboost', 6, 0.8832490507572791, 50, 0.34624966391664275, 'https://www.kaggle.com/datasets/camnugent/california-housing-prices')
	Params: {'boost': 'xgboost', 'depth': 6, 'learning_rate': 0.8832490507572791, 'num_rounds': 50, 'reg_lambda': 0.34624966391664275, 'url': 'https://www.kaggle.com/datasets/camnugent/california-housing-prices'}
	INFO:root:EC Key: ('xgboost', 10, 0.7822090251655713, 50, 3.0559177136816333, 'https://archive.ics.uci.edu/dataset/2/adult')
	Params: {'boost': 'xgboost', 'depth': 10, 'learning_rate': 0.7822090251655713, 'num_rounds': 50, 'reg_lambda': 3.0559177136816333, 'url': 'https://archive.ics.uci.edu/dataset/2/adult'}
	INFO:root:EC Key: ('lightgbm', 8, 0.3268763511687526, 50, 3.9902381194770284, 'https://archive.ics.uci.edu/dataset/2/adult')
	Params: {'boost': 'lightgbm', 'depth': 8, 'learning_rate': 0.3268763511687526, 'num_rounds': 50, 'reg_lambda': 3.9902381194770284, 'url': 'https://archive.ics.uci.edu/dataset/2/adult'}
	INFO:root:EC Key: ('lightgbm', 8, 1.0, 50, 1.7531397815842582, 'https://archive.ics.uci.edu/dataset/31/covertype')
	Params: {'boost': 'lightgbm', 'depth': 8, 'learning_rate': 1.0, 'num_rounds': 50, 'reg_lambda': 1.7531397815842582, 'url': 'https://archive.ics.uci.edu/dataset/31/covertype'}
	INFO:root:EC Key: ('lightgbm', 8, 0.1, 50, 0.4703124319083829, 'https://archive.ics.uci.edu/dataset/2/adult')
	Params: {'boost': 'lightgbm', 'depth': 8, 'learning_rate': 0.1, 'num_rounds': 50, 'reg_lambda': 0.4703124319083829, 'url': 'https://archive.ics.uci.edu/dataset/2/adult'}
	INFO:root:EC Key: ('xgboost', 10, 0.38246408863907266, 50, 0.9180991099688451, 'https://archive.ics.uci.edu/dataset/2/adult')
	Params: {'boost': 'xgboost', 'depth': 10, 'learning_rate': 0.38246408863907266, 'num_rounds': 50, 'reg_lambda': 0.9180991099688451, 'url': 'https://archive.ics.uci.edu/dataset/2/adult'}
	INFO:root:EC Key: ('lightgbm', 8, 0.6545002408593917, 50, 0.25, 'https://archive.ics.uci.edu/dataset/2/adult')
	Params: {'boost': 'lightgbm', 'depth': 8, 'learning_rate': 0.6545002408593917, 'num_rounds': 50, 'reg_lambda': 0.25, 'url': 'https://archive.ics.uci.edu/dataset/2/adult'}
	INFO:root:Pending computations: 32.
	INFO:root:Result:                                                  url  ... test_accuracy
	0  https://www.kaggle.com/datasets/camnugent/cali...  ...           0.0
	
	[1 rows x 7 columns].
	INFO:root:Push result to Vizier, EC Key: ('xgboost', 6, 0.732120410548891, 50, 2.7035596087532916, 'https://www.kaggle.com/datasets/camnugent/california-housing-prices')
	INFO:root:End Push.
	INFO:root:Completed computations: 1; Pending: 31.
	INFO:root:Call Vizier.
	INFO:google.cloud.aiplatform.vizier.study:Suggest Study study backing LRO: projects/21106255545/locations/us-central1/studies/323251796053/operations/323251796053__2
	INFO:google.cloud.aiplatform.vizier.study:<class 'google.cloud.aiplatform_v1.services.vizier_service.client.VizierServiceClient'>
	INFO:google.cloud.aiplatform.vizier.study:Study study suggested. Resource name: projects/21106255545/locations/us-central1/studies/323251796053
	INFO:root:Pending computations: 31.
	INFO:root:Result:                                            url  ... test_accuracy
	0  https://archive.ics.uci.edu/dataset/2/adult  ...      0.874194
	
	[1 rows x 7 columns].
	```
	End of computation and optimal trials:
	```
	INFO:root:Finishing
	WARNING:EMS.manager:_push_to_database(): Number of DataFrames: 5; Length of DataFrames: 5
													 url  ... test_accuracy
	0      https://www.kaggle.com/c/higgs-boson/training  ...           1.0
	1  https://www.kaggle.com/datasets/camnugent/cali...  ...           0.0
	2      https://www.kaggle.com/c/higgs-boson/training  ...           1.0
	3      https://www.kaggle.com/c/higgs-boson/training  ...           1.0
	4      https://www.kaggle.com/c/higgs-boson/training  ...           1.0
	
	[5 rows x 7 columns]
	INFO:pandas_gbq.gbq:
	5 out of 5 rows loaded.
	INFO:root:[<google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa949598150> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/2, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943c97b90> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/7, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943f6b610> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/13, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943f68f10> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/15, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943fb4b10> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/16, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa94aab4910> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/25, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa94aab48d0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/33, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa9496cde90> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/34, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943d05fd0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/35, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943d04ad0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/36, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943e1d650> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/37, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943e1c590> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/38, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943e1d150> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/39, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943f6ee50> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/40, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943fe5a90> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/41, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa949797290> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/42, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa949796890> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/47, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943dd6850> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/48, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943dd4e50> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/49, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943c9b450> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/50, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943c9bc10> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/51, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943de97d0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/52, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943dea150> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/53, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942096d10> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/54, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942095890> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/55, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942094a50> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/56, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942095190> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/57, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa9420978d0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/59, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa9420952d0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/60, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942097050> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/61, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942096c50> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/62, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942096b50> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/63, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942094750> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/64, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942095490> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/65, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942097790> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/66, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa942094a90> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/68, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943c89f50> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/70, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943c8b0d0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/72, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943c8a2d0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/82, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa94953ff90> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/83, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa94953fdd0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/84, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943c78b10> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/85, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943c7b910> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/86, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa948779550> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/87, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa94877be50> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/88, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa9487790d0> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/89, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943cdc190> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/90, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943cdd350> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/91, <google.cloud.aiplatform.vizier.trial.Trial object at 0x7fa943c61a90> 
	resource name: projects/21106255545/locations/us-central1/studies/323251796053/trials/92]
	81.65user 24.85system 16:29.33elapsed 10%CPU (0avgtext+0avgdata 1229164maxresident)k
	1168616inputs+4104outputs (380major+871197minor)pagefaults 0swaps
	```

13. Up on BigQuery, you can check that your data has been saved with [the console](https://console.cloud.google.com/bigquery?orgonly=true&project=stanford-stats-285-donoho&supportedpurview=organizationId&ws=!1m4!1m3!3m2!1sstanford-stats-285-donoho!2sEMS). Your databases will be named: `XYZ_EMS_su_id_hw7` and `XYZ_Vertex_su_id_hw7` where `su_id` is the Stanford ID you set in step 2.

14. Up on Vizier/Vertex, you can see your study [here](https://console.cloud.google.com/vertex-ai/experiments/studies?orgonly=true&project=stanford-stats-285-donoho&supportedpurview=organizationId). It has the same name as in the EMS dataset on BigQuery.

#### Performing Analysis with Google Colab.


## Submitting on Canvas
