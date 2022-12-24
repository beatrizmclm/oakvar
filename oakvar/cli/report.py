from . import cli_entry
from . import cli_func


@cli_entry
def cli_report(args):
    return report(args)


@cli_func
def report(args, __name__="report"):
    from ..lib.util.util import quiet_print
    from ..api.report import report

    module_options = {}
    module_option = args.get("module_option")
    if module_option:
        for opt_str in module_option:
            toks = opt_str.split("=")
            if len(toks) != 2:
                quiet_print(
                    "Ignoring invalid module option {opt_str}. module-option should be module_name.key=value.",
                    args,
                )
                continue
            k = toks[0]
            if k.count(".") != 1:
                quiet_print(
                    "Ignoring invalid module option {opt_str}. module-option should be module_name.key=value.",
                    args,
                )
                continue
            [module_name, key] = k.split(".")
            if module_name not in module_options:
                module_options[module_name] = {}
            v = toks[1]
            module_options[module_name][key] = v
    args["module_options"] = module_options
    ret = report(**args)
    return ret


def get_parser_fn_report():
    from argparse import ArgumentParser, SUPPRESS
    from ..lib.system.consts import DEFAULT_SERVER_DEFAULT_USERNAME

    parser_ov_report = ArgumentParser(
        prog="ov report dbpath ...",
        description="Generate reports from result SQLite files",
        epilog="dbpath must be the first argument.",
    )
    parser_ov_report.add_argument("dbpath", help="Path to aggregator output")
    parser_ov_report.add_argument(
        "-t",
        dest="report_types",
        nargs="+",
        default=[],
        help="report types",
    )
    parser_ov_report.add_argument(
        "-f", dest="filterpath", default=None, help="Path to filter file"
    )
    parser_ov_report.add_argument("--filter", default=None, help=SUPPRESS)
    parser_ov_report.add_argument("--filtersql", default=None, help="Filter SQL")
    parser_ov_report.add_argument(
        "-F",
        dest="filtername",
        default=None,
        help="Name of filter (stored in aggregator output)",
    )
    parser_ov_report.add_argument(
        "--filterstring", dest="filterstring", default=None, help=SUPPRESS
    )
    parser_ov_report.add_argument(
        "-s", dest="savepath", default=None, help="Path to save file"
    )
    parser_ov_report.add_argument("-c", dest="confpath", help="path to a conf file")
    parser_ov_report.add_argument(
        "--module-name", dest="module_name", default=None, help="report module name"
    )
    parser_ov_report.add_argument(
        "--nogenelevelonvariantlevel",
        dest="nogenelevelonvariantlevel",
        action="store_true",
        default=False,
        help="Use this option to prevent gene level result from being added to variant level result.",
    )
    parser_ov_report.add_argument(
        "--confs", dest="confs", default="{}", help="Configuration string"
    )
    parser_ov_report.add_argument(
        "--inputfiles",
        nargs="+",
        dest="inputfiles",
        default=None,
        help="Original input file path",
    )
    parser_ov_report.add_argument(
        "--separatesample",
        dest="separatesample",
        action="store_true",
        default=False,
        help="Write each variant-sample pair on a separate line",
    )
    parser_ov_report.add_argument(
        "-d", dest="output_dir", default=None, help="directory for output files"
    )
    parser_ov_report.add_argument(
        "--quiet",
        action="store_true",
        default=None,
        help="Suppress output to STDOUT",
    )
    parser_ov_report.add_argument(
        "--system-option",
        dest="system_option",
        nargs="*",
        help="System option in key=value syntax. For example, --system-option modules_dir=/home/user/oakvar/modules",
    )
    parser_ov_report.add_argument(
        "--module-option",
        dest="module_option",
        nargs="*",
        help="Module-specific option in module_name.key=value syntax. For example, --module-option vcfreporter.type=separate",
    )
    parser_ov_report.add_argument(
        "--concise-report",
        dest="concise_report",
        action="store_true",
        default=False,
        help="Generate concise report with default columns defined by annotation modules",
    )
    parser_ov_report.add_argument(
        "--includesample",
        dest="includesample",
        nargs="+",
        default=None,
        help="Sample IDs to include",
    )
    parser_ov_report.add_argument(
        "--excludesample",
        dest="excludesample",
        nargs="+",
        default=None,
        help="Sample IDs to exclude",
    )
    parser_ov_report.add_argument(
        "--package", help="Use filters and report types in a package"
    )
    parser_ov_report.add_argument(
        "--md",
        default=None,
        help="Specify the root directory of OakVar modules (annotators, etc)",
    )
    parser_ov_report.add_argument(
        "--cols",
        dest="cols",
        nargs="+",
        default=None,
        help="columns to include in reports",
    )
    parser_ov_report.add_argument(
        "--level",
        default=None,
        help="Level to make a report for. 'all' to include all levels. Other possible levels include 'variant' and 'gene'.",
    )
    parser_ov_report.add_argument(
        "--user",
        default=DEFAULT_SERVER_DEFAULT_USERNAME,
        help=f"User who is creating this report. Default is {DEFAULT_SERVER_DEFAULT_USERNAME}.",
    )
    parser_ov_report.add_argument(
        "--no-summary",
        action="store_true",
        default=False,
        help="Skip gene level summarization. This saves time.",
    )
    parser_ov_report.set_defaults(func=cli_report)
    return parser_ov_report
