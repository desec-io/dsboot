import re

import dns.zone
from dns.name import root

from dsboot.base import DSBootBase


zonefile_re = re.compile("_signal\\.([A-Za-z0-9-]+\\.)+zone")


def get_signaling_zone_filename(signaling_domain):
    filename = f"{signaling_domain}zone"
    if not zonefile_re.fullmatch(filename):
        raise ValueError(
            f"Refusing to use non-hostname nameserver in filename: {signaling_domain.parent()}"
        )
    return filename


class DSBoot(DSBootBase):
    read_files: bool
    signaling_domains: set
    signaling_zones: dict

    def __init__(self, nameservers, read_files, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read_files = read_files
        self.signaling_domains = {
            dns.name.from_text("_signal." + nameserver) for nameserver in nameservers
        }
        self.signaling_zones = {}

    def process(self, f):
        default_signaling_domains = set()
        prev_name, signaling_domains, cdatas = None, set(), {}
        for line in f:
            try:
                if line.split()[3] not in ("CDS", "CDNSKEY", "NS"):
                    continue
            except IndexError:
                continue
            for rname, rttl, rdata in dns.zone.from_text(
                line,
                origin=root,
                relativize=False,
                filename="stdin",
                allow_include=False,
                check_origin=False,
                allow_directives=False,
            ).iterate_rdatas():
                if self.signaling_domains and rdata.rdtype == dns.rdatatype.NS:
                    continue
                if rdata.rdtype not in (
                    dns.rdatatype.CDS,
                    dns.rdatatype.CDNSKEY,
                    dns.rdatatype.NS,
                ):
                    self.logger.debug(
                        f"Ignoring record {rname}/{dns.rdatatype.to_text(rdata.rdtype)}"
                    )
                    continue
                if rdata.rdtype != dns.rdatatype.NS and rname == root:
                    raise ValueError(
                        f"CDS/CDNSKEY records for the root are illegal: {line}"
                    )
                if prev_name is not None:
                    if prev_name != rname:
                        if prev_name == root:  # Old name was for fallback NS
                            default_signaling_domains = signaling_domains
                        else:
                            self._insert(
                                prev_name,
                                signaling_domains or default_signaling_domains,
                                cdatas,
                            )
                            cdatas = {}
                        prev_name, signaling_domains = rname, set()
                else:
                    prev_name = rname
                if rdata.rdtype == dns.rdatatype.NS:
                    signaling_domains.add(
                        dns.name.from_text("_signal").relativize(origin=root)
                        + rdata.target.derelativize(origin=root)
                    )
                else:
                    cdata = cdatas.setdefault(rdata.rdtype, [rttl, set()])
                    cdata[0] = min(cdata[0], rttl)
                    cdata[1].add(rdata)
        self._insert(prev_name, signaling_domains or default_signaling_domains, cdatas)

    def _read_signaling_zone_file(self, signaling_domain):
        try:
            filename = get_signaling_zone_filename(signaling_domain)
            zone = dns.zone.from_file(
                filename,
                allow_include=False,
                check_origin=False,
            )
        except FileNotFoundError:
            return None
        if zone.origin != signaling_domain:
            raise ValueError(
                f"Unexpected zone origin in signaling zone file {filename}: {zone.origin}"
            )
        return zone

    def _get_signaling_zone(self, signaling_domain):
        if signaling_domain not in self.signaling_zones:
            zone = None
            if self.read_files:
                zone = self._read_signaling_zone_file(signaling_domain)
            if not zone:
                zone = dns.zone.from_text(
                    f"@ 3600 IN NS {signaling_domain.parent().to_text()}",
                    origin=signaling_domain,
                    check_origin=False,
                )
            self.signaling_zones[signaling_domain] = zone
        return self.signaling_zones[signaling_domain]

    def _insert(self, child, signaling_domains, cdatas):
        signaling_name = dns.name.from_text("_dsboot").relativize(
            origin=root
        ) + child.relativize(origin=root)
        if self.signaling_domains:
            signaling_domains |= self.signaling_domains
        for signaling_domain in signaling_domains:
            if signaling_domain.is_subdomain(child):
                self.logger.info(
                    f"Skipping in-bailiwick bootstrapping for {child} (via {signaling_domain})"
                )
                continue
            signaling_zone = self._get_signaling_zone(signaling_domain)
            signaling_zone.delete_node(signaling_name)
            for cdata in cdatas.values():
                signaling_zone.replace_rdataset(
                    signaling_name, dns.rdataset.from_rdata(cdata[0], *cdata[1])
                )

    def write(self, write_files):
        for signaling_zone in self.signaling_zones.values():
            if write_files:
                filename = get_signaling_zone_filename(signaling_zone.origin)
                signaling_zone.to_file(filename, sorted=False, want_origin=True)
            else:
                print(signaling_zone.to_text(want_origin=True))
