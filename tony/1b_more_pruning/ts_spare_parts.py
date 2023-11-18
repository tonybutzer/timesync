# Things I think we can remove
def retry(retries: int, jitter: Tuple[int, int] = (1, 15)) -> Callable:
    """
    Simple retry decorator, for retrying any function that may throw an exception
    such as when trying to retrieve network resources
    """
    def retry_dec(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            count = 1
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    count += 1
                    if count > retries:
                        raise
                    time.sleep(random.randint(*jitter))
        return wrapper
    return retry_dec

def local_setup(*args) -> dict:
    """
    Extra setup for writing output to a local file system
    """
    return {
        'fs': fsspec.filesystem('file'),
        'rio_env': {
            'session': None,
            'GDAL_PAM_ENABLED': 'NO',  # Set to 'YES' to write XML metadata
        }}


def aws_setup(profile: str, *args) -> dict:
    """
    Extra setup for writing to an S3 bucket
    """
    # key, secret = aws_credentials(profile)
    return {
        # 'fs': fsspec.filesystem('s3', key=key, secret=secret),
        'fs': fsspec.filesystem('s3', anon=False, requester_pays=True),
        'rio_env': {
            'session': rio.session.AWSSession(),
            'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
            'GDAL_PAM_ENABLED': 'NO',  # Set to 'YES' to write XML metadata
        }}


def submit_next_job(client: Client, func: Callable, plots: Iterable) -> Optional[Future]:
    """
    Run the processing of the next plot as a job on the cluster
    Set the priority of the job to favor completing plots in order
    """
    try:
        plot = next(plots)
        future = client.submit(func, plot, priority=-int(plot.plot_id))
    except StopIteration:
        future = None
    return future


def process_on_kube(params: dict) -> None:
    """
    Process a group of plots on the CHS Pangeo Kubernetes cluster
    """
    # Get input data
    plots_df, n_completed, n_total = data_preparation(params['plot_file'], log_file_name(params))
    if n_completed == n_total:
        print(f'All {n_total} plots processed successfully! Exiting...')

    else:

        # Get the client and dashboard link
        client = params.pop('client')
        print('Dashboard: https://pangeo.chs.usgs.gov' + client.dashboard_link)

        # Define the processing function
        processing_func = partial(process_plot_dask, params=params)

        # Prepare to iterate over plots and hold resulting futures
        plots, futures = plots_df.itertuples(), []

        # Submit the first n tasks; others will be submitted as each task completes
        for _ in range(CONCURRENT_STAC_QUERIES):
            future = submit_next_job(client, processing_func, plots)
            if future is not None:
                futures.append(future)

        # Prepare to process results as they complete
        watch_for_completion = as_completed(futures)

        # Track plot completion and handle subsequent task submissions
        with tqdm.tqdm(desc='Processing plots', initial=n_completed, total=n_total) as pbar:
            for completed in watch_for_completion:

                # Log plot completion (or error message)
                plot, status = completed.result()
                log_plot_status(plot, status, log_file_name(params))
                pbar.update()

                # Submit the next plot to the cluster
                future = submit_next_job(client, processing_func, plots)
                if future is not None:
                    watch_for_completion.add(future)


def aws_credentials(profile: str) -> Tuple[str, str]:
    """
    Fetch information on AWS credentials
    """
    # parser = configparser.ConfigParser()
    # parser.read(os.path.join(os.environ['HOME'], '.aws', 'credentials'))
    # return parser[profile]['aws_access_key_id'], parser[profile]['aws_secret_access_key']
    return 


@report_status
def process_plot_dask(plot: Tuple[Any, ...], params: dict) -> None:
    """
    Process an individual plot
    """
    groups = group_records(stac_records_for_plot(plot, params))
    func = partial(process_group, plot=plot, params=params)
    with worker_client() as client:
        futures = client.map(func, groups)
        try:
            client.gather(futures)
        except Exception:
            client.cancel(futures)
            raise
