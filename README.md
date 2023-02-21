# py4web debug tools

Tooling to improve the developer experience when working with py4web.

There are two main tools and some helpers that this package provides.

1. A better error 500 screen, that shows the error + traceback of what happened
2. A debug bar containing the requests's data, queries including duplicate and custom caught data.

## In this package:

- `tools`:
    - `enable(db: DAL, enabled?: bool, fancy_rendering?: bool, bar_style?: "bootstrap", slow_threshold_ms?: int)`:  
      activate or disable the debug tools (add the custom error screen and create the Debug Bar Fixture).  
      The first argument (DAL) is required for the debug bar to collect queries.  
      `enabled` can be used to dynamically turn on/off the debug features.  
      `fancy_rendering`: This will render the `data` section of the debug bar using `json-browse`, which
      includes `jQuery`. If this clashes with the other JS on a page, this can be set to False to simply show a `<pre>`
      block with data.  
      `bar_style`: only bootstrap is supported at this moment.  
      `slow_threshold_ms`: amount of milliseconds an SQL query has to take before it is considered a 'slow query' in the
      debug bar.
    - `debug_bar`: this Fixture can be used on py4web actions to enable the bar for that page.
- `catch(*)`: Data and a stacktrace of where `catch()` is called can be found in the catch tab of the debug bar.
- `dump(*)`: convert objects to JSON, with a more capable converter than the default json.dumps (e.g. it works better
  with NamedTuples, pyDAL Rows, objects with some variation of `as_dict` and more. See `dumping.py:DDJsonEncoder` for
  specifics)
- `dd(*)`: Show a page with the data passed to this method and halt execution directly.

## Example:

```python
# controllers.py

from py4web_debug import tools, catch, dump, dd

tools.enable(db, enabled=True)


@action("index")
@action.uses("index.html", db, tools.debug_bar)
def index():
    catch("Catch to Debug Bar")
    return {}


@action("other")
@action.uses("index.html", db)
def page_without_debugbar():
    dd("Stop executing here!")
    return {}


@action("error")
@action.uses("index.html", db)
def page_with_error():
    0 / 0
    return {}
```