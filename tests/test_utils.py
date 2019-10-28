# -*- coding: utf-8 -*-
import unittest
from unittest import mock
import os
import pytest
import lxml.html
from nikola import metadata_extractors
from nikola.post import get_meta
from nikola.utils import (
    demote_headers, TranslatableSetting, get_crumbs, TemplateHookRegistry,
    get_asset_path, get_theme_chain, get_translation_candidate, write_metadata)
from nikola.plugins.task.sitemap import get_base_path as sitemap_get_base_path

import pytest


class dummy(object):
    default_lang = 'en'
    metadata_extractors_by = metadata_extractors.default_metadata_extractors_by()
    config = {'TRANSLATIONS_PATTERN': '{path}.{lang}.{ext}',
              'TRANSLATIONS': {'en': './'},
              'DEFAULT_LANG': 'en'}

    def __init__(self):
        metadata_extractors.load_defaults(self, self.metadata_extractors_by)


class GetMetaTest(unittest.TestCase):
    def test_getting_metadata_from_content(self):
        file_metadata = ".. title: Nikola needs more tests!\n"\
                        ".. slug: write-tests-now\n"\
                        ".. date: 2012/09/15 19:52:05\n"\
                        ".. tags:\n"\
                        ".. link:\n"\
                        ".. description:\n\n"\
                        "Post content\n"

        opener_mock = mock.mock_open(read_data=file_metadata)

        post = dummy()
        post.source_path = 'file_with_metadata'
        post.metadata_path = 'file_with_metadata.meta'

        with mock.patch('nikola.post.io.open', opener_mock, create=True):
            meta = get_meta(post, None)[0]

        self.assertEqual('Nikola needs more tests!', meta['title'])
        self.assertEqual('write-tests-now', meta['slug'])
        self.assertEqual('2012/09/15 19:52:05', meta['date'])
        self.assertFalse('tags' in meta)
        self.assertFalse('link' in meta)
        self.assertFalse('description' in meta)

    def test_get_title_from_fname(self):
        file_metadata = ".. slug: write-tests-now\n"\
                        ".. date: 2012/09/15 19:52:05\n"\
                        ".. tags:\n"\
                        ".. link:\n"\
                        ".. description:\n"

        opener_mock = mock.mock_open(read_data=file_metadata)

        post = dummy()
        post.source_path = 'file_with_metadata'
        post.metadata_path = 'file_with_metadata.meta'

        with mock.patch('nikola.post.io.open', opener_mock, create=True):
            meta = get_meta(post, None)[0]

        self.assertEqual('file_with_metadata', meta['title'])
        self.assertEqual('write-tests-now', meta['slug'])
        self.assertEqual('2012/09/15 19:52:05', meta['date'])
        self.assertFalse('tags' in meta)
        self.assertFalse('link' in meta)
        self.assertFalse('description' in meta)

    def test_use_filename_as_slug_fallback(self):
        file_metadata = ".. title: Nikola needs more tests!\n"\
                        ".. date: 2012/09/15 19:52:05\n"\
                        ".. tags:\n"\
                        ".. link:\n"\
                        ".. description:\n\n"\
                        "Post content\n"

        opener_mock = mock.mock_open(read_data=file_metadata)

        post = dummy()
        post.source_path = 'Slugify this'
        post.metadata_path = 'Slugify this.meta'

        with mock.patch('nikola.post.io.open', opener_mock, create=True):
            meta = get_meta(post, None)[0]
        self.assertEqual('Nikola needs more tests!', meta['title'])
        self.assertEqual('slugify-this', meta['slug'])
        self.assertEqual('2012/09/15 19:52:05', meta['date'])
        self.assertFalse('tags' in meta)
        self.assertFalse('link' in meta)
        self.assertFalse('description' in meta)

    def test_extracting_metadata_from_filename(self):
        dummy_opener_mock = mock.mock_open(read_data="No metadata in the file!")

        post = dummy()
        post.source_path = '2013-01-23-the_slug-dub_dub_title.md'
        post.metadata_path = '2013-01-23-the_slug-dub_dub_title.meta'
        post.config['FILE_METADATA_REGEXP'] = r'(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>.*)-(?P<title>.*)\.md'
        for unslugify, title in ((True, 'Dub dub title'), (False, 'dub_dub_title')):
            post.config['FILE_METADATA_UNSLUGIFY_TITLES'] = unslugify
            with mock.patch('nikola.post.io.open', dummy_opener_mock, create=True):
                meta = get_meta(post, None)[0]

            self.assertEqual(title, meta['title'])
            self.assertEqual('the_slug', meta['slug'])
            self.assertEqual('2013-01-23', meta['date'])

    def test_get_meta_slug_only_from_filename(self):
        dummy_opener_mock = mock.mock_open(read_data="No metadata in the file!")
        post = dummy()
        post.source_path = 'some/path/the_slug.md'
        post.metadata_path = 'some/path/the_slug.meta'
        with mock.patch('nikola.post.io.open', dummy_opener_mock, create=True):
            meta = get_meta(post, None)[0]

        self.assertEqual('the_slug', meta['slug'])


@pytest.mark.parametrize("level, input_str, expected_output", [
    (0,
     '''
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     ''',
     '''
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     '''),
    (1,
     '''
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     ''',
     '''
     <h2>header 1</h2>
     <h3>header 2</h3>
     <h4>header 3</h4>
     <h5>header 4</h5>
     <h6>header 5</h6>
     <h6>header 6</h6>
     '''),
    (2,
     '''
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     ''',
     '''
     <h3>header 1</h3>
     <h4>header 2</h4>
     <h5>header 3</h5>
     <h6>header 4</h6>
     <h6>header 5</h6>
     <h6>header 6</h6>
     '''),
    (-1,
     '''
     <h1>header 1</h1>
     <h2>header 2</h2>
     <h3>header 3</h3>
     <h4>header 4</h4>
     <h5>header 5</h5>
     <h6>header 6</h6>
     ''',
     '''
     <h1>header 1</h1>
     <h1>header 2</h1>
     <h2>header 3</h2>
     <h3>header 4</h3>
     <h4>header 5</h4>
     <h5>header 6</h5>
     ''')
], ids=["by zero", "by one", "by two", "by minus one"])
def test_demoting_headers(level, input_str, expected_output):
    doc = lxml.html.fromstring(input_str)
    outdoc = lxml.html.fromstring(expected_output)
    demote_headers(doc, level)
    assert lxml.html.tostring(outdoc) == lxml.html.tostring(doc)


class TranslatableSettingsTest(unittest.TestCase):
    """Tests for translatable settings."""

    def test_string_input(self):
        """Tests for string input."""
        inp = 'Fancy Blog'
        S = TranslatableSetting('S', inp, {'xx': ''})
        S.default_lang = 'xx'
        S.lang = 'xx'

        u = str(S)

        cn = S()      # no language specified
        cr = S('xx')  # real language specified
        cf = S('zz')  # fake language specified

        self.assertEqual(inp, u)
        self.assertEqual(inp, cn)
        self.assertEqual(inp, cr)
        self.assertEqual(inp, cf)
        self.assertEqual(S.lang, 'xx')
        self.assertEqual(S.default_lang, 'xx')

    def test_dict_input(self):
        """Tests for dict input."""
        inp = {'xx': 'Fancy Blog',
               'zz': 'Schmancy Blog'}

        S = TranslatableSetting('S', inp, {'xx': '', 'zz': ''})
        S.default_lang = 'xx'
        S.lang = 'xx'

        u = str(S)

        cn = S()
        cx = S('xx')
        cz = S('zz')
        cf = S('ff')

        self.assertEqual(inp['xx'], u)
        self.assertEqual(inp['xx'], cn)
        self.assertEqual(inp['xx'], cx)
        self.assertEqual(inp['zz'], cz)
        self.assertEqual(inp['xx'], cf)

    def test_dict_input_lang(self):
        """Test dict input, with a language change along the way."""
        inp = {'xx': 'Fancy Blog',
               'zz': 'Schmancy Blog'}

        S = TranslatableSetting('S', inp, {'xx': '', 'zz': ''})
        S.default_lang = 'xx'
        S.lang = 'xx'

        u = str(S)

        cn = S()

        self.assertEqual(inp['xx'], u)
        self.assertEqual(inp['xx'], cn)

        # Change the language.
        # WARNING: DO NOT set lang locally in real code!  Set it globally
        #          instead! (TranslatableSetting.lang = ...)
        # WARNING: TranslatableSetting.lang is used to override the current
        #          locale settings returned by LocaleBorg!  Use with care!
        S.lang = 'zz'

        u = str(S)
        cn = S()

        self.assertEqual(inp['zz'], u)
        self.assertEqual(inp['zz'], cn)


def test_get_asset_path():
    assert get_asset_path('assets/css/nikola_rst.css',
                          get_theme_chain('bootstrap4', ['themes'])).replace(
        '\\', '/').endswith('nikola/data/themes/base/assets/css/nikola_rst.css')
    assert get_asset_path('assets/css/theme.css',
                          get_theme_chain('bootstrap4', ['themes'])).replace(
        '\\', '/').endswith(
        'nikola/data/themes/bootstrap4/assets/css/theme.css')
    assert get_asset_path(
        'nikola.py', get_theme_chain('bootstrap4', ['themes']),
        {'nikola': ''}).replace(
        '\\', '/').endswith('nikola/nikola.py')
    assert get_asset_path('nikola.py', get_theme_chain(
        'bootstrap4', ['themes']), {'nikola': 'nikola'}) is None
    assert get_asset_path(
        'nikola/nikola.py', get_theme_chain('bootstrap4', ['themes']),
        {'nikola': 'nikola'}).replace(
        '\\', '/').endswith('nikola/nikola.py')


def test_get_crumbs():
    crumbs = get_crumbs('galleries')
    assert len(crumbs) == 1
    assert crumbs[0] == ['#', 'galleries']

    crumbs = get_crumbs(os.path.join('galleries', 'demo'))
    assert len(crumbs) == 2
    assert crumbs[0] == ['..', 'galleries']
    assert crumbs[1] == ['#', 'demo']

    crumbs = get_crumbs(os.path.join('listings', 'foo', 'bar'), is_file=True)
    assert len(crumbs) == 3
    assert crumbs[0] == ['..', 'listings']
    assert crumbs[1] == ['.', 'foo']
    assert crumbs[2] == ['#', 'bar']


def test_get_translation_candidate():
    config = {'TRANSLATIONS_PATTERN': '{path}.{lang}.{ext}',
              'DEFAULT_LANG': 'en', 'TRANSLATIONS': {'es': '1', 'en': 1}}
    assert get_translation_candidate(config, '*.rst', 'es') == '*.es.rst'
    assert get_translation_candidate(
        config, 'fancy.post.rst', 'es') == 'fancy.post.es.rst'
    assert get_translation_candidate(config, '*.es.rst', 'es') == '*.es.rst'
    assert get_translation_candidate(config, '*.es.rst', 'en') == '*.rst'
    assert get_translation_candidate(
        config, 'cache/posts/fancy.post.es.html', 'en') == 'cache/posts/fancy.post.html'
    assert get_translation_candidate(
        config, 'cache/posts/fancy.post.html', 'es') == 'cache/posts/fancy.post.es.html'
    assert get_translation_candidate(
        config, 'cache/pages/charts.html', 'es') == 'cache/pages/charts.es.html'
    assert get_translation_candidate(
        config, 'cache/pages/charts.html', 'en') == 'cache/pages/charts.html'

    config = {'TRANSLATIONS_PATTERN': '{path}.{ext}.{lang}',
              'DEFAULT_LANG': 'en', 'TRANSLATIONS': {'es': '1', 'en': 1}}
    assert get_translation_candidate(config, '*.rst', 'es') == '*.rst.es'
    assert get_translation_candidate(config, '*.rst.es', 'es') == '*.rst.es'
    assert get_translation_candidate(config, '*.rst.es', 'en') == '*.rst'
    assert get_translation_candidate(
        config, 'cache/posts/fancy.post.html.es', 'en') == 'cache/posts/fancy.post.html'
    assert get_translation_candidate(
        config, 'cache/posts/fancy.post.html', 'es') == 'cache/posts/fancy.post.html.es'


def test_TemplateHookRegistry():
    r = TemplateHookRegistry('foo', None)
    r.append('Hello!')
    r.append(lambda x: 'Hello ' + x + '!', False, 'world')
    assert r() == 'Hello!\nHello world!'


@pytest.mark.parametrize("base, expected_path", [
    ('http://some.site', '/'),
    ('http://some.site/', '/'),
    ('http://some.site/some/sub-path', '/some/sub-path/'),
    ('http://some.site/some/sub-path/', '/some/sub-path/'),
])
def test_sitemap_get_base_path(base, expected_path):
    assert expected_path == sitemap_get_base_path(base)


@pytest.mark.parametrize("metadata_format, expected_result", [
    ('nikola', """\
.. title: Hello, world!
.. slug: hello-world
.. a: 1
.. b: 2

"""),
    ('yaml', """\
---
a: '1'
b: '2'
slug: hello-world
title: Hello, world!
---
""")
])
def test_write_metadata_with_formats(metadata_format, expected_result):
    """
    Test writing metadata with different formats.

    YAML is expected to be sorted alphabetically.
    Nikola sorts by putting the defaults first and then sorting the rest
    alphabetically.
    """
    data = {'slug': 'hello-world', 'title': 'Hello, world!', 'b': '2', 'a': '1'}
    assert write_metadata(data, metadata_format) == expected_result


def test_write_metadata_with_format_toml():
    """
    Test writing metadata in TOML format.

    TOML is sorted randomly in Python 3.5 or older and by insertion
    order since Python 3.6.
    """
    data = {'slug': 'hello-world', 'title': 'Hello, world!', 'b': '2', 'a': '1'}

    toml = write_metadata(data, 'toml')
    assert toml.startswith('+++\n')
    assert toml.endswith('+++\n')
    assert 'slug = "hello-world"' in toml
    assert 'title = "Hello, world!"' in toml
    assert 'b = "2"' in toml
    assert 'a = "1"' in toml


@pytest.mark.parametrize("wrap, expected_result", [
    (False, """\
.. title: Hello, world!
.. slug: hello-world

"""),
    (True, """\
<!--
.. title: Hello, world!
.. slug: hello-world
-->

"""),
    (('111', '222'), """\
111
.. title: Hello, world!
.. slug: hello-world
222

""")
])
def test_write_metadata_comment_wrap(wrap, expected_result):
    data = {'title': 'Hello, world!', 'slug': 'hello-world'}
    assert write_metadata(data, 'nikola', wrap) == expected_result


@pytest.mark.parametrize("metadata_format, expected_results", [
    ('rest_docinfo', ["""=============
Hello, world!
=============

:slug: hello-world
"""]),
    ('markdown_meta', ["""title: Hello, world!
slug: hello-world

""", """slug: hello-world
title: Hello, world!

"""]),

])
def test_write_metadata_compiler(metadata_format, expected_results):
    """
    Test writing metadata with different formats.

    We test for multiple results because some compilers might produce
    unordered output.
    """
    data = {'title': 'Hello, world!', 'slug': 'hello-world'}
    assert write_metadata(data, metadata_format) in expected_results


@pytest.mark.parametrize("post_format, expected_metadata", [
    ('rest', '==\nxx\n==\n\n'),
    ('markdown', 'title: xx\n\n'),
    ('html', '.. title: xx\n\n'),
])
def test_write_metadata_pelican_detection(post, post_format, expected_metadata):
    post.name = post_format

    data = {'title': 'xx'}
    assert write_metadata(data, 'pelican', compiler=post) == expected_metadata


def test_write_metadata_pelican_detection_default():
    data = {'title': 'xx'}
    assert write_metadata(data, 'pelican', compiler=None) == '.. title: xx\n\n'


def test_write_metadata_from_site(post):
    post.config = {'METADATA_FORMAT': 'yaml'}
    data = {'title': 'xx'}
    assert write_metadata(data, site=post) == '---\ntitle: xx\n---\n'


def test_write_metadata_default(post):
    data = {'title': 'xx'}
    assert write_metadata(data) == '.. title: xx\n\n'


@pytest.mark.parametrize("arg", ['foo', 'filename_regex'])
def test_write_metadata_fallbacks(post, arg):
    data = {'title': 'xx'}
    assert write_metadata(data, arg) == '.. title: xx\n\n'


@pytest.fixture
def post():
    return dummy()


if __name__ == '__main__':
    unittest.main()
