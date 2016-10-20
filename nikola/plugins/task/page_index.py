# -*- coding: utf-8 -*-

# Copyright © 2012-2016 Roberto Alsina and others.

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

"""Render the blog indexes."""

from __future__ import unicode_literals

from nikola.plugin_categories import Taxonomy


class PageIndex(Taxonomy):
    """Render the page index."""

    name = "classify_page_index"

    classification_name = "page_index_folder"
    metadata_name = None
    overview_page_variable_name = "page_folder"
    more_than_one_classifications_per_post = False
    has_hierarchy = True
    include_posts_from_subhierarchies = False
    show_list_as_index = False
    generate_atom_feeds_for_post_lists = False
    template_for_list_of_one_classification = "list.tmpl"
    template_for_classification_overview = None
    always_disable_rss = True
    apply_to_posts = False
    apply_to_pages = True
    omit_empty_classifications = True
    also_create_classifications_from_other_languages = False

    def is_enabled(self, lang=None):
        """Return True if this taxonomy is enabled, or False otherwise."""
        return self.site.config["PAGE_INDEX"]

    def classify(self, post, lang):
        """Classify the given post for the given language."""
        destpath = post.destination_path(lang, sep='/')
        index_len = len(self.site.config["INDEX_FILE"])
        if destpath[-(1 + index_len):] == '/' + self.site.config["INDEX_FILE"]:
            destpath = destpath[:-(1 + index_len)]
        i = destpath.rfind('/')
        return destpath[:i] if i >= 0 else ''

    def get_classification_printable_name(self, hierarchy, lang, only_last_component=False):
        """Extract a printable name from the classification."""
        return '/'.join(hierarchy)

    def get_path(self, hierarchy, lang, type='page'):
        """A path handler for the given classification."""
        return hierarchy, 'always'

    def extract_hierarchy(self, dirname):
        """Given a classification, return a list of parts in the hierarchy."""
        return dirname.split('/') if dirname else []

    def recombine_classification_from_hierarchy(self, hierarchy):
        """Given a list of parts in the hierarchy, return the classification string."""
        return '/'.join(hierarchy)

    def provide_context_and_uptodate(self, dirname, lang):
        """Provide data for the context and the uptodate list for the list of the given classifiation."""
        kw = {
            "translations": self.site.config['TRANSLATIONS'],
            "filters": self.site.config['FILTERS'],
        }
        context = {
            "title": self.site.config['BLOG_TITLE'](lang),
            "classification_title": self.site.config['BLOG_TITLE'](lang),
            "pagekind": ["list", "front_page"] if dirname == '' else ["list"],
        }
        kw.update(context)
        return context, kw

    def should_generate_classification_list(self, dirname, post_list, lang):
        """Only generates list of posts for classification if this function returns True."""
        short_destination = dirname + '/' + self.site.config['INDEX_FILE']
        for post in post_list:
            # If there is an index.html pending to be created from a page, do not generate the page index.
            if post.destination_path(lang, sep='/') == short_destination:
                return False
        return True
