#!/usr/bin/env python3

# library imports
import argparse
import logging
import sys
import pathlib

# third party imports
import attr

from telegram_tl_parser.parser import Parser
from telegram_tl_parser.gen import Generator
from telegram_tl_parser.output import JsonOutput, AttrsOutput

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
        path_resolved = path_maybe.resolve(strict=False).expanduser()

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

    parser.add_argument("--tl-file-path",
        dest="tl_file_path",
        type=isFileType,
        required=True,
        help="the telegram .tl file")
    parser.add_argument("--output-file-path",
        dest="output_file_path",
        type=isValidNewFileLocation,
        required=True,
        help="the output file we will write")
    parser.add_argument("--skip-n-lines",
        dest="skip_n_lines",
        type=int,
        default=14,
        required=False,
        help="Skip N number of lines from the start of the file, defaults to 14.")
    parser.add_argument("--pyparsing-debug-logging",
        dest="pyparsing_debug_logging_is_enabled",
        action="store_true",
        help="If provided, we will turn on extra logging from pyparsing, at the debug/error level")
    parser.add_argument("--verbose",
        action="store_true",
        help="Increase logging verbosity")
    parser.add_argument("--log-to-file",
        dest="log_to_file",
        type=isValidNewFileLocation,
        help="If set, the log statements will be logged to the specified file rather than stdout")

    subparsers = parser.add_subparsers(help="sub-command help" )

    json_subparser = subparsers.add_parser("json", help="JSON output")
    json_subparser.set_defaults(func_to_run=JsonOutput.run_from_args)

    attrs_subparser = subparsers.add_parser("attrs", help="Attrs style classes output")
    attrs_subparser.set_defaults(func_to_run=AttrsOutput.run_from_args)

    try:
        parsed_args = parser.parse_args()

        # set up logging stuff
        logging.captureWarnings(True) # capture warnings with the logging infrastructure
        root_logger = logging.getLogger()
        logging_formatter = logging.Formatter("%(asctime)s %(threadName)-10s %(name)-24s %(levelname)-8s: %(message)s")

        # set up logging handler
        logging_handler = None
        if parsed_args.log_to_file:
            logging_handler = logging.FileHandler(parsed_args.log_to_file, mode="a", encoding="utf-8")
        else:
            logging_handler = logging.StreamHandler(sys.stdout)

        logging_handler.setFormatter(logging_formatter)
        root_logger.addHandler(logging_handler)

        # set logging level based on arguments
        if parsed_args.verbose:
            root_logger.setLevel("DEBUG")
        else:
            root_logger.setLevel("INFO")


        root_logger.debug("parsed arguments: `%s`", parsed_args)

        # run the function associated with each sub command
        if "func_to_run" in parsed_args:

            parsed_args.func_to_run(parsed_args)

        else:
            root_logger.info("no subcommand specified!")
            parser.print_help()
            sys.exit(0)

        root_logger.info("Done!")

    except Exception as e:
        root_logger.exception("Something went wrong!")
        sys.exit(1)