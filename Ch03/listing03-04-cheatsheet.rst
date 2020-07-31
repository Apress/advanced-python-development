Header 1
========

Header 2
--------

Header 3
++++++++

Header 4
********

*italic* **bold** Combining bold and italic is not possible.

1. Numbered List
2. With more items

   #. Sublists are indented with a blank line surrounding them
   #. The # symbol can be used in place of the number to auto-number the list

3. It can be confusing if the numbers don’t match the reader’s
   expectation

-  Unordered lists
-  Use asterisks in the first position

   -  Sublists are indented with a blank line surrounding them
   -  Hyphens can be used to visually differentiate sublists
   -  As with numbered lists, \* - and + are interchangeable but must be used consistently

-  but it is best to use them consistently

When referring to things that should be rendered in a monospace font,
such as file names or the names of classes. These should be surrounded
by ``double backticks``.

Larger blocks of code are in a named block, starting with ``.. code ::``. They
can optionally have a language following the double colon, to
facilitate syntax highlighting

.. code:: python

   def example():
       return True

..

   Quotations are declared with an unnamed block, declared with ``..`` 
   and can cover multiple lines. They must be surrounded by blank lines.

Links have a confusing structure. The link definition is a pair of backticks
with a trailing underscore. Inside the backticks are the link text followed by
the target in angle brackets.

`Link to book’s website <https://advancedpython.dev>`_

Images are handled similarly to code blocks, with a ``.. image::`` declaration
followed by the URL of the image. They can have indented arguments, such as
to define alt text.

.. image:: https://advancedpython.dev/cover.png
   :alt: Book’s cover

Finally, tables use pipes to delimit columns and new lines to delimit
rows. Equals signs are used to delimit the columns as well as the top
and bottom of the table and the end of the header.

=============== === ===
Multiplications One Two
=============== === ===
One             1   2
Two             2   4
=============== === ===

The alignment here is essential. The table will not render unless the equals signs
all match the extent of the column they define, with no discrepancy. Any text that extends
wider will also cause rendering to fail.
