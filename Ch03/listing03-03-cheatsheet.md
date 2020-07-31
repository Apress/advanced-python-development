# Header 1
## Header 2
### Header 3
#### Header 4

_italic_ **bold** **_bold and italic_**

1. Numbered List
2. With more items
    1. Sublists are indented
    1. The numbers in any level of list need not be correct
3. It can be confusing if the numbers don't match the reader's expectation

* Unordered lists
* Use asterisks in the first position
    - Sublists are indented
    - Hyphens can be used to visually differentiate sublists
    + As with numbered lists, * - and + are interchangeable and do not need to be used consistently
* but it is best to use them consistently

When referring to things that should be rendered in a monospace font, such as file names or the names of classes, these should be surrounded by `backticks`.

Larger blocks of code should be surrounded with three backticks. They can optionally have a language following the first three backticks, to facilitate syntax highlighting
```python
def example():
    return True
```

> Quotations are declared with a leading right chevron
> and can cover multiple lines

Links and images are handled similarly to each other, as a pair of square brackets that defines the text that should be shown followed by a pair of parentheses that contain the target URL.

[Link to book's website](https://advancedpython.dev)

Images are differentiated by having a leading exclamation mark:

![Book's cover](https://advancedpython.dev/cover.png)

Finally, tables use pipes to delimit columns and new lines to delimit rows. Hyphens are used to split the header row from the body, resulting in a very readable ASCII art style table:


| Multiplications | One | Two |
| --------------- | --- | --- |
| One             |  1  |  2  |
| Two             |  2  |  4  |

However, the alignment is not important. The table will still render correctly even if the pipes are not aligned correctly. The row that contains the hyphens must include at least three hyphens per column, but otherwise, the format is relatively forgiving.
