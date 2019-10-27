# Author: Rodrigo Bistolfi
# Date: 03/2013

"""
Test cases for Nikola ReST extensions.

A sample will be rendered by CompileRest.
One method is provided for checking the resulting HTML:

    * assertHTMLContains(html, element, attributes=None, text=None)

"""

import io
import os
from io import StringIO

from lxml import html as lxml_html

import nikola.plugins.compile.rest
import nikola.plugins.compile.rest.listing
from nikola.plugins.compile.rest import vimeo
from nikola.utils import _reload, LocaleBorg

from .base import FakeSite, FakePost

import pytest


def test_ReST_extension(tmpdir):
    "Simple test for our base class :)"

    sample = '.. raw:: html\n\n   <iframe src="foo" height="bar">spam</iframe>'
    html = getHtmlFromRst(tmpdir, sample)

    assertHTMLContains(html, "iframe", attributes={"src": "foo"}, text="spam")

    with pytest.raises(Exception):
        assertHTMLContains("eggs", {})


def test_math_extension_outputs_tex(tmpdir):
    "Test that math is outputting TeX code."
    sample = r':math:`e^{ix} = \cos x + i\sin x`'
    html = getHtmlFromRst(tmpdir, sample)

    assertHTMLContains(html, "span", attributes={"class": "math"},
                                     text=r"\(e^{ix} = \cos x + i\sin x\)")


def test_soundcloud_iframe(tmpdir):
    "Test SoundCloud iframe tag generation"

    sample = '.. soundcloud:: SID\n   :height: 400\n   :width: 600'
    html = getHtmlFromRst(tmpdir, sample)
    assertHTMLContains(html, "iframe",
                       attributes={"src": ("https://w.soundcloud.com/player/"
                                           "?url=http://api.soundcloud.com/"
                                           "tracks/SID"),
                                   "height": "400",
                                   "width": "600"})


def test_youtube_iframe(tmpdir):
    "Test Youtube iframe tag generation"

    sample = '.. youtube:: YID\n   :height: 400\n   :width: 600'
    html = getHtmlFromRst(tmpdir, sample)
    assertHTMLContains(html, "iframe",
                             attributes={"src": ("https://www.youtube-nocookie.com/"
                                                 "embed/YID?rel=0&"
                                                 "wmode=transparent"),
                                         "height": "400",
                                         "width": "600",
                                         "frameborder": "0",
                                         "allowfullscreen": "",
                                         "allow": "encrypted-media"})


def test_vimeo(disable_vimeo_api_query, tmpdir):
    "Test Vimeo iframe tag generation"

    sample = '.. vimeo:: VID\n   :height: 400\n   :width: 600'
    html = getHtmlFromRst(tmpdir, sample)
    assertHTMLContains(html, "iframe",
                             attributes={"src": ("https://player.vimeo.com/"
                                                 "video/VID"),
                                         "height": "400",
                                         "width": "600"})


@pytest.mark.parametrize("sample", [
    '.. code-block:: python\n\n   import antigravity',
    '.. sourcecode:: python\n\n   import antigravity',
])
def test_rendering_codeblock_alias(tmpdir, sample):
    """ Test CodeBlock aliases """
    getHtmlFromRst(tmpdir, sample)


def test_doc_doesnt_exist():
    with pytest.raises(Exception):
        assertHTMLContains('anything', {})


def test_doc(tmpdir):
    sample = 'Sample for testing my :doc:`fake-post`'
    html = getHtmlFromRst(tmpdir, sample)
    assertHTMLContains(html, 'a', text='Fake post',
                                  attributes={'href': '/posts/fake-post'})

def test_doc_titled(tmpdir):
    sample = 'Sample for testing my :doc:`titled post <fake-post>`'
    html = getHtmlFromRst(tmpdir, sample)
    assertHTMLContains(html, 'a', text='titled post',
                                  attributes={'href': '/posts/fake-post'})


@pytest.fixture(autouse=True, scope="module")
def localeborg_base():
    """A base config of LocaleBorg."""
    LocaleBorg.reset()
    assert not LocaleBorg.initialized
    LocaleBorg.initialize({}, 'en')
    assert LocaleBorg.initialized
    assert LocaleBorg().current_lang == 'en'
    try:
        yield
    finally:
        LocaleBorg.reset()
        assert not LocaleBorg.initialized


def getHtmlFromRst(temp_dir, rst):
    "Create html output from rst string"

    infile = os.path.join(temp_dir, 'inf')
    outfile = os.path.join(temp_dir, 'outf')

    with io.open(infile, 'w+', encoding='utf8') as post_file:
        post_file.write(rst)

    post = FakePost('', '')
    post._depfile[outfile] = []

    compiler = nikola.plugins.compile.rest.CompileRest()
    compiler.set_site(FakeSite())
    compiler.site.post_per_input_file[infile] = post
    compiler.compile(infile, outfile)

    with io.open(outfile, 'r', encoding='utf8') as rendered_file:
        return rendered_file.read()


def assertHTMLContains(html, element, attributes=None, text=None):
    """
    Test if HTML document includes an element with the given attributes
    and text content.

    The HTML is parsed with lxml for checking against the data you
    provide. The method takes an element argument, a string representing
    the *name* of an HTML tag, like "script" or "iframe".
    We will try to find this tag in the document and perform the tests
    on it. You can pass a dictionary to the attributes kwarg
    representing the name and the value of the tag attributes. The text
    kwarg takes a string argument, which will be tested against the
    contents of the HTML element.

    One last caveat: you need to url unquote your urls if you are going
    to test attributes like "src" or "link", since the HTML rendered by
    docutils will be always unquoted.
    """
    html_doc = lxml_html.parse(StringIO(html))

    try:
        tag = next(html_doc.iter(element))
    except StopIteration:
        raise Exception("<{0}> not in {1}".format(element, html))

    if attributes:
        arg_attrs = set(attributes.items())
        tag_attrs = set(tag.items())
        assert arg_attrs.issubset(tag_attrs)

    if text:
        assert text in tag.text


@pytest.fixture
def disable_vimeo_api_query():
    """
    Disable query of the vimeo api over the wire

    Set Vimeo.request_size to False for avoiding querying the Vimeo api
    over the network.
    """
    before = vimeo.Vimeo.request_size
    vimeo.Vimeo.request_size = False
    try:
        _reload(nikola.plugins.compile.rest)
        yield
    finally:
        vimeo.Vimeo.request_size = before
