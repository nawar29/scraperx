import os
import json
import logging
from pprint import pprint
from deepdiff import DeepDiff

from .write_to import WriteTo
from .arguments import cli_args
from .config import config, SCRAPER_NAME

logger = logging.getLogger(__name__)


def run_test(extract_cls):
    # TODO: Loop over test dir for scraper and extract
    #       compare the json files using code from centrifuge
    #       delete the test file after the chekc runs
    for _ in ['file']:  # TODO: thread for all files
        task = {
            "device_type": "desktop",
            "id": 0,
            "scraper_name": SCRAPER_NAME,
            "url": "http://testing-ground.scraping.pro/blocks"
        }
        source_file = f"test_sources/{SCRAPER_NAME}/test_1.html"
        download_manifest = {
            "date_downloaded": "2019-01-21",
            "source_files": [
                {
                    "location": "local",
                    "path": source_file
                }
            ],
            "time_downloaded": "2019-01-21 21:27:36.485610",
        }
        # TODO: Forcing this will fail for scrapers that extract
        #       to multiple files. Need to fix
        config._set_value('EXTRACTOR_FILE_TEMPLATE',
                          f"{source_file}_test.json")

        extractor = extract_cls(task, download_manifest)
        test_files = extractor.run()

        # TODO: Make work for multiple extracted files
        # for test_file in test_files:

        # Compare the qa files for each output
        data = {}
        test_file = test_files[0]['path']
        with open(test_file) as test_data:
            data['new'] = json.load(test_data)

        qa_file = f"{source_file}_qa.json"
        with open(qa_file) as qa_data:
            data['qa'] = json.load(qa_data)

        diff = DeepDiff(data['qa'], data['new'])
        if diff != {}:
            logger.error(f"Errors found in the file {qa_file}")
            pprint(diff)
        else:
            logger.info("All test qa'd files passed the extraction test")

        os.remove(test_file)


def run_dispatch(dispatch_cls):
    """Kick off the dispatcher for the scraper

    Arguments:
        dispatch_cls {class} -- Class of the dispatch action from the scraper
    """
    tasks = None
    if cli_args.tasks:
        tasks = cli_args.tasks

    # If a limit is set, the dispatcher init will handle it
    dispatcher = dispatch_cls(tasks=tasks)
    if cli_args.dump_tasks:
        # Dump data to local json file
        task_file = WriteTo(dispatcher.tasks).write_json()\
                                             .save_local('tasks.json')
        num_tasks = len(dispatcher.tasks)
        logger.info(f"Saved {num_tasks} tasks to {task_file['path']}")

    # Run the dispatcher...
    dispatcher.dispatch()


def run_download(download_cls):
    """Kick off the downloader for the scraper

    Arguments:
        download_cls {class} -- Class of the download action from the scraper
    """
    for task in cli_args.tasks:
        downloader = download_cls(task)
        downloader.run()


def run_extract(extract_cls):
    """Kick off the extractor for the scraper

    Arguments:
        extract_cls {class} -- Class of the extract action from the scraper
    """
    if os.path.isdir(cli_args.source):
        # source_dir = os.fsencode(cli_args.source)
        # for file in os.listdir(source_dir):

        # extractor = cli_args.scraper.Extract(task, cli_args=args)
        # extractor.run()
        pass
    else:
        metadata_file = f"{cli_args.source}.metadata.json"
        metadata = {}
        with open(metadata_file) as f:
            metadata = json.load(f)

        extractor = extract_cls(metadata['task'],
                                metadata['download_manifest'])
        extractor.run()


def run(dispatch=None, download=None, extract=None):

    if cli_args.action == 'validate':
        from pprint import pprint
        print("Testing the config....")
        pprint(config.values)

    elif cli_args.action == 'test':
        run_test(extract)

    elif cli_args.action == 'dispatch':
        run_dispatch(dispatch)

    elif cli_args.action == 'download':
        run_download(download)

    elif cli_args.action == 'extract':
        run_extract(extract)
