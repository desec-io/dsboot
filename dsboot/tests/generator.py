import contextlib
import io
from collections import defaultdict
from glob import glob
from unittest import TestCase
from unittest.mock import patch, mock_open

import dns.name
import dns.zone

from dsboot import DSBoot


def normalize_zonefiles(zonefiles):
    return sorted([sorted(z.split("\n")) for z in zonefiles.split("\n\n")])


class TestBase(TestCase):
    def setUp(self):
        pass

    def _run_test(self, assertfunc, read_files=False):
        prefix = "read-" if read_files else "out-"
        with contextlib.chdir('data/'), open("in.dat") as f_in:
            # Iterate over different parameters for dsboot_generate
            for dirname in glob(f"{prefix}*"):
                # Extract nameservers from filename and remove empty string
                nameservers = dirname.removeprefix(prefix)
                nameservers = list(filter(None, nameservers.split(",")))

                # Process input
                f_in.seek(0)  # reset from previous read
                with contextlib.chdir(dirname):
                    dsboot = DSBoot(nameservers=nameservers, read_files=read_files)
                    dsboot.process(f_in)

                # Check output against expected
                if not nameservers:
                    f_in.seek(0)
                    nameservers = [
                        rdata.target.to_text()
                        for *_, rdata in dns.zone.from_text(
                            f_in, check_origin=False
                        ).iterate_rdatas()
                        if rdata.rdtype == dns.rdatatype.NS
                    ]
                assertfunc(dirname, dsboot, nameservers)

    def test_generate(self):
        def _assert(dirname, dsboot, _):
            with io.StringIO() as buf:
                # Collect outputs
                with contextlib.redirect_stdout(buf):
                    dsboot.write(write_files=False)

                # Compare outputs
                with open(f"{dirname}/out.dat") as f_out:
                    actual = normalize_zonefiles(buf.getvalue())
                    expected = normalize_zonefiles(f_out.read())
                    self.assertEqual(actual, expected)

        self._run_test(_assert)

    def test_write(self):
        def _assert(dirname, dsboot, expected_nameservers):
            # Collect outputs
            open_mock = mock_open()
            open_mock.return_value.encoding = None
            zonefiles = defaultdict(bytes)
            with patch("dns.zone.open", open_mock, create=True):
                dsboot.write(write_files=True)
            for method, args, kwargs in open_mock.mock_calls:
                if not method:
                    zone = args[0]
                    continue
                if method == "().write":
                    zonefiles[zone] += args[0]

            # Compare outputs
            self.assertEqual(
                zonefiles.keys(),
                {f"_signal.{nameserver}.zone" for nameserver in expected_nameservers},
            )
            for zone, zonefile in zonefiles.items():
                with open(f"{dirname}/{zone}") as f_out:
                    actual = normalize_zonefiles(zonefile.decode())
                    expected = normalize_zonefiles(f_out.read())
                    self.assertEqual(actual, expected)

        self._run_test(_assert)

    def test_read(self):
        def _assert(dirname, dsboot, _):
            with io.StringIO() as buf:
                # Collect outputs
                with contextlib.redirect_stdout(buf):
                    dsboot.write(write_files=False)

                # Compare outputs
                with open(f"{dirname}/out.dat") as f_out:
                    actual = normalize_zonefiles(buf.getvalue().strip())
                    expected = normalize_zonefiles(f_out.read().strip())
                    self.assertEqual(actual, expected)

        self._run_test(_assert, read_files=True)
