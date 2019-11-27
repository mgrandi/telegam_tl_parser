import logging
import argparse

from telegram_tl_parser.parser import Parser
from telegram_tl_parser.gen import Generator


logger = logging.getLogger(__name__)

class JsonOutput:

    @staticmethod
    def run_from_args(parsed_args:argparse.Namespace) -> None:

        logger.info("Parsing and outputting as JSON")

        parser = Parser()
        gen = Generator()

        result_file_def = parser.parse(
            parsed_args.tl_file_path,
            parsed_args.skip_n_lines,
            parsed_args.pyparsing_debug_logging_is_enabled)


        output = gen.tl_file_definition_to_json(result_file_def)

        with open(parsed_args.output_file_path, "w", encoding="utf-8") as f:
            f.write(output)

        logger.info("file successfully written as JSON to `%s`", parsed_args.output_file_path)


class AttrsOutput:

    @staticmethod
    def run_from_args(parsed_args:argparse.Namespace) -> None:

        logger.info("Parsing and outputting as Attrs Classes")

        parser = Parser()
        gen = Generator()

        result_file_def = parser.parse(
            parsed_args.tl_file_path,
            parsed_args.skip_n_lines,
            parsed_args.pyparsing_debug_logging_is_enabled)


        output = gen.tl_file_definition_to_attrs_classes(result_file_def)

        with open(parsed_args.output_file_path, "w", encoding="utf-8") as f:
            f.write(output)