import argparse
import sys

from dsboot import DSBoot


def main():
    description = "Generate signaling records for Authenticated DNSSEC Bootstrapping from existing zones."
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "nameserver",
        help="Nameserver for which to generate signaling records",
        type=str,
        nargs="*",
    )
    parser.add_argument(
        "-r",
        "--read-files",
        help="Read signaling zone files for update",
        action="store_true",
    )
    parser.add_argument(
        "-w",
        "--write-files",
        help="Write signaling zone files, create if needed",
        action="store_true",
    )
    parser.add_argument(
        "-v", "--verbose", help="Increase output verbosity", action="count", default=0
    )
    args = parser.parse_args()

    dsboot = DSBoot(args.nameserver, read_files=args.read_files, log_level=args.verbose)
    dsboot.process(sys.stdin)
    dsboot.write(write_files=args.write_files)


if __name__ == "__main__":
    main()
