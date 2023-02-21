# py4web debug tools
Tooling to improve the developer experience when working with py4web.  

There are two main tools and some helpers that this package provides.

1. A better error 500 screen, that shows the error + traceback of what happened
2. A debug bar containing the requests's data, queries including duplicate and custom caught data.

## In this package:

- `tools`:
    - `enable(db: DAL, enabled: bool)`: activate or disable the debug tools (add the custom error screen and create the Debug Bar
      Fixture).  
      The first argument (DAL) is required for the debug bar to collect queries.
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