#!/usr/bin/env python3

# library imports
import argparse
import logging
import sys
import pathlib

# third party imports
import attr

from telegram_tl_parser.parser import Parser



def isFileType(filePath):
    ''' see if the file path given to us by argparse is a file
    @param filePath - the filepath we get from argparse
    @return the filepath as a pathlib.Path() if it is a file, else we raise a ArgumentTypeError'''

    path_maybe = pathlib.Path(filePath)
    path_resolved = None

    # try and resolve the path
    try:
        path_resolved = path_maybe.resolve(strict=True)

    except Exception as e:
        raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

    # double check to see if its a file
    if not path_resolved.is_file():
        raise argparse.ArgumentTypeError("The path `{}` is not a file!".format(path_resolved))

    return path_resolved

def isValidNewFileLocation(filePath):
    ''' see if the file path given to us by argparse is a file
    @param filePath - the filepath we get from argparse
    @return the filepath as a pathlib.Path() if it is a file, else we raise a ArgumentTypeError'''

    path_maybe = pathlib.Path(filePath)
    path_resolved = None

    # try and resolve the path
    try:
        path_resolved = path_maybe.resolve(strict=False)

    except Exception as e:
        raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

    if not path_resolved.parent.exists():
        raise argparse.ArgumentTypeError("The parent directory of  `{}` doesn't exist!".format(path_resolved))

    return path_resolved

if __name__ == "__main__":
    # if we are being run as a real program

    parser = argparse.ArgumentParser(
        description="parses telegram .tl files into python attrs classes",
        epilog="Copyright 2019-11-21 - Mark Grandi")

    # set up logging stuff
    logging.captureWarnings(True) # capture warnings with the logging infrastructure
    root_logger = logging.getLogger()
    logging_formatter = logging.Formatter("%(asctime)s %(threadName)-10s %(name)-20s %(levelname)-8s: %(message)s")
    logging_handler = logging.StreamHandler(sys.stdout)
    logging_handler.setFormatter(logging_formatter)
    root_logger.addHandler(logging_handler)

    # optional arguments, if specified these are the input and output files, if not specified, it uses stdin and stdout
    parser.add_argument("--tl-file", dest="tl_file_path", type=isFileType, required=True, help="the telegram .tl file")
    parser.add_argument("--output-file", dest="output_file_path", type=isValidNewFileLocation, required=True, help="the output file we will write")
    parser.add_argument("--verbose", action="store_true", help="Increase logging verbosity")


    try:
        parsed_args = parser.parse_args()

        # set logging level based on arguments
        if parsed_args.verbose:
            root_logger.setLevel("DEBUG")
        else:
            root_logger.setLevel("INFO")


        # run the application
        app = Parser()
        result = app.parse(parsed_args.tl_file_path)

        root_logger.info("Done!")
    except Exception as e:
        root_logger.exception("Something went wrong!")
        sys.exit(1)