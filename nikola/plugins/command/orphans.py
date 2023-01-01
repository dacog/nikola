# -*- coding: utf-8 -*-

# Copyright © 2012-2023 Roberto Alsina, Chris Warrick and others.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""List all orphans."""

import os

from nikola.plugin_categories import Command
from nikola.plugins.command.check import real_scan_files


class CommandOrphans(Command):
    """List all orphans."""

    name = "orphans"
    doc_purpose = "list all orphans"
    doc_description = """\
List all orphans, i.e. all files that are in the output directory,
but are not generated by Nikola.

Output contains filenames only (it is passable to `xargs rm` or the like)."""

    def _execute(self, options, args):
        """Run the orphans command."""
        orphans = real_scan_files(self.site)[0]
        print('\n'.join([p for p in orphans if not os.path.isdir(p)]))
