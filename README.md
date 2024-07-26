# DNSSEC Bootstrapping Record Generator

This utility generates signaling zones for authenticated DNSSEC bootstrapping ([RFC 9615](https://www.rfc-editor.org/rfc/rfc9615.html)).

Before publishing these zones, child zone operators need to run them through their signing pipeline, as usual. (The tool is meant for environments where the nameserver cannot synthesize these records on the fly. Examples include BIND, NSD, and other pre-signed setups.)


## Installation

This package can be installed using [`pip`](https://pypi.org/project/pip/), preferably into its own [`virtualenv`](https://docs.python.org/3/tutorial/venv.html).

    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv)$ pip install dsboot
    (venv)$ dsboot_generate --help


## Usage

    $ dsboot_generate --help
    usage: dsboot_generate [-h] [-r] [-w] [-v] [nameserver ...]

    Generate signaling records for Authenticated DNSSEC Bootstrapping from existing zones.

    positional arguments:
      nameserver         nameserver for which to generate signaling records

    options:
      -h, --help         show this help message and exit
      -r, --read-files   read signaling zone files for update
      -w, --write-files  write signaling zone files, create if needed
      -v, --verbose      logging verbosity (default: 0)

### Input

Input is read from standard input, expecting CDS and/or CDNSKEY records for one or more domains, in the usual zone file format.

During one run, records for multiple domains are accepted. Domain names are extracted from the owner name of each CDS/CDNSKEY record.
  
In addition, NS records need to be provided for each domain. As a fallback, an NS record set with the root owner name (`.`) can be included. All subsequent domain names that do not have their own NS record set will be associated with this fallback NS record set.

Alternatively, one or more nameserver hostnames may be provided as arguments to the tool itself. In this case, NS records from standard input are ignored, and all domain names are associated with the explicitly provided nameservers.

Input records not of type CDS/CDNSKEY/NS are ignored. A simple way of generating "all signaling records" is therefore to simply dump all zones into the tool.

### Output

For each nameserver encountered, the tool outputs a signaling zone (`_signal.$NS`) containing the bootstrapping records for the domains associated with it. (An SOA record has to be added manually.)

By default, signaling zones are written to standard output, separated by a double newline (`\n\n`).
  
### Flags

When the `-w` flag is specified, each signaling zone is written to a separate file (`_signal.$NS.zone`) in the current working directory.

When the `-r` flag is specified, signaling zone files are read from disk and used as a starting point when generating signaling records, adding or replacing record sets as appropriate. Other record sets found remain unchanged, but may be reformatted or reordered. (As a consequence, there is currently no way to indicate removal of bootstrapping records for a domain.)

The `-r` and `-w` flags operate independently, that is, specifying `-r` without `-w` will not overwrite any files.

## Example

    (venv)$ dsboot_generate <<EOF
    > $ORIGIN .
    > test.example  3600  IN  CDS      17514 13 2 ba591a0751ce5e6f824398303d57fa766cb4d85db600c3da471edfd8330187f7
    > test.example  3600  IN  CDNSKEY  257 3 13 7BOWDw313HbPVNdqIaWUwBaLDQydSOE2BRqN6idpUr5ZJivYrzCmV+sSl1mR6Ioir7rqOyDm7Ns+6pr02ZvJjA==
    > test.example  3600  IN  NS       ns2.example.
    > test.example  3600  IN  NS       ns1.example.
    > EOF
    $ORIGIN _signal.ns1.example.
    @ 3600 IN NS ns1.example.
    _dsboot.test.example 3600 IN CDS 17514 13 2 ba591a0751ce5e6f824398303d57fa766cb4d85db600c3da471edfd8330187f7
    _dsboot.test.example 3600 IN CDNSKEY 257 3 13 7BOWDw313HbPVNdqIaWUwBaLDQydSOE2 BRqN6idpUr5ZJivYrzCmV+sSl1mR6Ioi r7rqOyDm7Ns+6pr02ZvJjA==
    
    $ORIGIN _signal.ns2.example.
    @ 3600 IN NS ns2.example.
    _dsboot.test.example 3600 IN CDS 17514 13 2 ba591a0751ce5e6f824398303d57fa766cb4d85db600c3da471edfd8330187f7
    _dsboot.test.example 3600 IN CDNSKEY 257 3 13 7BOWDw313HbPVNdqIaWUwBaLDQydSOE2 BRqN6idpUr5ZJivYrzCmV+sSl1mR6Ioi r7rqOyDm7Ns+6pr02ZvJjA==

---

This work was [funded by NLnet Foundation](https://nlnet.nl/project/AuthenticatedDNSSECbootstrap/) and [supported by SSE](https://securesystems.de/).