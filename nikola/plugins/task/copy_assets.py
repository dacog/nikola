# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

"""Copy theme assets into output."""


import io
import os

from nikola.plugin_categories import Task
from nikola import utils
from nikola.nikola import LEGAL_VALUES

_COLORBOX_PREFIX = 'js|colorbox-i18n|jquery.colorbox-'.replace('|', os.sep)
_COLORBOX_SLICE = slice(len(_COLORBOX_PREFIX), -3)


class CopyAssets(Task):
    """Copy theme assets into output."""

    name = "copy_assets"

    def gen_tasks(self):
        """Create tasks to copy the assets of the whole theme chain.

        If a file is present on two themes, use the version
        from the "youngest" theme.
        """
        kw = {
            "themes": self.site.THEMES,
            "translations": self.site.translations,
            "files_folders": self.site.config['FILES_FOLDERS'],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "code_color_scheme": self.site.config['CODE_COLOR_SCHEME'],
            "code.css_selectors": 'pre.code',
            "code.css_head": '/* code.css file generated by Nikola */\n',
            "code.css_close": "\ntable.codetable { width: 100%;} td.linenos {text-align: right; width: 4em;}\n",
        }
        tasks = {}
        code_css_path = os.path.join(kw['output_folder'], 'assets', 'css', 'code.css')
        code_css_input = utils.get_asset_path('assets/css/code.css',
                                              themes=kw['themes'],
                                              files_folders=kw['files_folders'], output_dir=None)
        yield self.group_task()

        main_theme = utils.get_theme_path(kw['themes'][0])
        theme_ini = utils.parse_theme_meta(main_theme)
        if theme_ini:
            ignored_assets = theme_ini.get("Nikola", "ignored_assets", fallback='').split(',')
            ignore_colorbox_i18n = theme_ini.get("Nikola", "ignore_colorbox_i18n", fallback="unused")
        else:
            ignored_assets = []
            ignore_colorbox_i18n = "unused"

        if ignore_colorbox_i18n == "unused":
            # Check what colorbox languages we need so we can ignore the rest
            needed_colorbox_languages = [LEGAL_VALUES['COLORBOX_LOCALES'][i] for i in kw['translations']]
            needed_colorbox_languages = [i for i in needed_colorbox_languages if i]  # remove '' for en
            # ignored_filenames is passed to copy_tree to avoid creating
            # directories. Since ignored_assets are full paths, and copy_tree
            #  works on single filenames, we can’t use that here.
            if not needed_colorbox_languages:
                ignored_filenames = set(["colorbox-i18n"])
            else:
                ignored_filenames = set()

        for theme_name in kw['themes']:
            src = os.path.join(utils.get_theme_path(theme_name), 'assets')
            dst = os.path.join(kw['output_folder'], 'assets')
            for task in utils.copy_tree(src, dst, ignored_filenames=ignored_filenames):
                asset_name = os.path.relpath(task['name'], dst)
                if task['name'] in tasks or asset_name in ignored_assets:
                    continue
                elif asset_name.startswith(_COLORBOX_PREFIX):
                    if ignore_colorbox_i18n == "all" or ignore_colorbox_i18n is True:
                        continue

                    colorbox_lang = asset_name[_COLORBOX_SLICE]
                    if ignore_colorbox_i18n == "unused" and colorbox_lang not in needed_colorbox_languages:
                        continue
                tasks[task['name']] = task
                task['uptodate'] = [utils.config_changed(kw, 'nikola.plugins.task.copy_assets')]
                task['basename'] = self.name
                if code_css_input:
                    if 'file_dep' not in task:
                        task['file_dep'] = []
                    task['file_dep'].append(code_css_input)
                yield utils.apply_filters(task, kw['filters'])

        # Check whether or not there is a code.css file around.
        if not code_css_input and kw['code_color_scheme']:
            def create_code_css():
                from pygments.formatters import get_formatter_by_name
                formatter = get_formatter_by_name('html', style=kw["code_color_scheme"])
                utils.makedirs(os.path.dirname(code_css_path))
                with io.open(code_css_path, 'w+', encoding='utf8') as outf:
                    outf.write(kw["code.css_head"])
                    outf.write(formatter.get_style_defs(kw["code.css_selectors"]))
                    outf.write(kw["code.css_close"])

            if os.path.exists(code_css_path):
                with io.open(code_css_path, 'r', encoding='utf-8') as fh:
                    testcontents = fh.read(len(kw["code.css_head"])) == kw["code.css_head"]
            else:
                testcontents = False

            task = {
                'basename': self.name,
                'name': code_css_path,
                'targets': [code_css_path],
                'uptodate': [utils.config_changed(kw, 'nikola.plugins.task.copy_assets'), testcontents],
                'actions': [(create_code_css, [])],
                'clean': True,
            }
            yield utils.apply_filters(task, kw['filters'])
