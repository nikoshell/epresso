"""Epresso Pygments styles — light + dark code palettes.

Reusable syntax-highlighting styles for any epresso site. Used via
``pygments_css_pair(EpressoThemeLight, EpressoThemeDark)``, which emits every
colour as ``light-dark()`` so one stylesheet follows ``color-scheme`` the way an
epresso theme's design tokens do. ``pygments_css(theme, selector)`` is still
there for a single-palette site.

Palette (token → role):
  green   = keyword / operator / control / interpol
  blue    = function call / builtin name
  purple  = class / decorator
  cyan    = builtin type / constant builtin
  orange  = string
  amber   = number / constant
  red     = error / exception
  gray    = comment / operator / punctuation
"""

from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
)


class EpressoThemeLight(Style):
    background_color = "#ffffff"
    default_style = ""

    styles = {
        Text: "#1a1d23",

        Comment: "italic #6f7681",

        Keyword: "bold #087a44",
        Keyword.Constant: "bold #0c9d58",
        Keyword.Declaration: "bold #0c9d58",
        Keyword.Namespace: "bold #087a44",
        Keyword.Type: "bold #087a44",

        Name: "#1a1d23",
        Name.Builtin: "#0a7ea4",
        Name.Function: "bold #0067c4",
        Name.Class: "bold #7a3eb0",
        Name.Decorator: "#7a3eb0",
        Name.Exception: "#c23b3b",
        Name.Variable: "#1a1d23",
        Name.Constant: "#9a5b00",

        String: "#a05a00",
        String.Doc: "italic #8a7d66",
        String.Interpol: "#087a44",

        Number: "#9a5b00",

        Operator: "bold #5c6370",
        Operator.Word: "bold #087a44",

        Punctuation: "#5c6370",

        Generic.Heading: "bold #087a44",
        Generic.Emph: "italic",
        Generic.Strong: "bold",

        Error: "border:#c23b3b #c23b3b",
    }


class EpressoThemeDark(Style):
    background_color = "#171a21"
    default_style = ""

    styles = {
        Text: "#e8ecf1",

        Comment: "italic #7d8794",

        Keyword: "bold #5fe0a6",
        Keyword.Constant: "bold #3ecf8e",
        Keyword.Declaration: "bold #3ecf8e",
        Keyword.Namespace: "bold #5fe0a6",
        Keyword.Type: "bold #5fe0a6",

        Name: "#e8ecf1",
        Name.Builtin: "#56b6c2",
        Name.Function: "bold #4ea1ff",
        Name.Class: "bold #c792ea",
        Name.Decorator: "#c792ea",
        Name.Exception: "#e06a6a",
        Name.Variable: "#e8ecf1",
        Name.Constant: "#e0b45a",

        String: "#f0a35e",
        String.Doc: "italic #7d8794",
        String.Interpol: "#5fe0a6",

        Number: "#e0b45a",

        Operator: "bold #9aa2b1",
        Operator.Word: "bold #5fe0a6",

        Punctuation: "#9aa2b1",

        Generic.Heading: "bold #5fe0a6",
        Generic.Emph: "italic",
        Generic.Strong: "bold",

        Error: "border:#e06a6a #e06a6a",
    }
