# Email Module
An email module that I had built.  Supports legacy style email via smtp as well as the more modern method of sending email via a cloud api such as Gmail.

## Example

```python
from emailsender import Gmail

body = """
<html>
  <head></head>
    <body>
      <p>Hello World!!</p>
    </body>
</html>
"""

gmail = Gmail("bo@bosmith.tech", "gmail-api-address", body)
gmail.send_email()
```