#########################
 Grid Table Span Gallery
#########################

A gallery of grid tables exercising every combination of ``morecols`` / ``morerows``
(colspan / rowspan) I could think of. Each subsection shows one scenario.

**************
 Column spans
**************

Single colspan across two columns
=================================

+------+------+
| A    | B    |
+------+------+
| C spans two |
+-------------+

Single colspan across three columns
===================================

+-----+-----+------+
| One | Two | Tri  |
+-----+-----+------+
| Header spans all |
+-----+-----+------+
| A   | B   | C    |
+-----+-----+------+

Colspan at the top, split below
===============================

+---------------------------+
| Banner across all columns |
+------+------+------+------+
| A    | B    | C    | D    |
+------+------+------+------+

Colspan at the bottom, split above
==================================

+------+------+------+------+
| A    | B    | C    | D    |
+------+------+------+------+
| Banner across all columns |
+---------------------------+

Colspan sandwich (split, span, split)
=====================================

+------+------+------+
| A    | B    | C    |
+------+------+------+
| Middle spans three |
+------+------+------+
| D    | E    | F    |
+------+------+------+

Two independent colspans in one row
===================================

+-----+-----+-----+-----+
| A   | B   | C   | D   |
+-----+-----+-----+-----+
| A+B spans | C+D spans |
+-----+-----+-----+-----+
| E   | F   | G   | H   |
+-----+-----+-----+-----+

***********
 Row spans
***********

Single rowspan across two rows
==============================

+---+---+
| A | B |
|   +---+
|   | C |
+---+---+
| D | E |
+---+---+

Single rowspan across three rows
================================

+---+---+
| A | B |
|   +---+
|   | C |
|   +---+
|   | D |
+---+---+

Rowspan in the middle column
============================

+---+---+---+
| a | b | c |
+---+   +---+
| d |   | e |
+---+   +---+
| f |   | g |
+---+---+---+

Rowspan at the left edge
========================

+------+---+---+---+
| Left | B | C | D |
|      +---+---+---+
|      | E | F | G |
|      +---+---+---+
|      | H | I | J |
+------+---+---+---+

Rowspan at the right edge
=========================

+---+---+---+-------+
| A | B | C | Right |
+---+---+---+       |
| D | E | F |       |
+---+---+---+       |
| G | H | I |       |
+---+---+---+-------+

Two independent rowspans in one column
======================================

+---+---+
| A | B |
|   +---+
|   | C |
+---+---+
| D | E |
|   +---+
|   | F |
+---+---+

*******************************
 Combined row and column spans
*******************************

Rowspan + colspan on the same cell (2 rows × 2 cols)
====================================================

+---+---+---+---+
| A | B | C | D |
+---+---+---+---+
| E | Fspan | H |
+---+       +---+
| I |       | J |
+---+-------+---+

Rowspan + colspan (3 rows × 2 cols)
===================================

+---+----+-----+---+
| A | B  | C   | D |
+---+----+-----+---+
| E | Big span | F |
+---+          +---+
| G |          | H |
+---+          +---+
| I |          | J |
+---+----------+---+

Rowspan + colspan (2 rows × 3 cols)
===================================

+---+---+---+---+---+
| A | B | C | D | E |
+---+---+---+---+---+
| F | Wide span | G |
+---+           +---+
| H |           | I |
+---+-----------+---+

*********
 Corners
*********

Top-left corner colspan
=======================

+-----------+---+
| Top-left  | X |
+---+---+---+---+
| A | B | C | Y |
+---+---+---+---+

Top-right corner colspan
========================

+---+-----------+
| X | Top-right |
+---+---+---+---+
| Y | A | B | C |
+---+---+---+---+

Bottom-left corner colspan
==========================

+---+----+----+---+
| A | B  | C  | X |
+---+----+----+---+
| Bottom-left | Y |
+-------------+---+

Bottom-right corner colspan
===========================

+---+----+----+----+
| X | A  | B  | C  |
+---+----+----+----+
| Y | Bottom-right |
+---+--------------+

Top-left corner rowspan
=======================

+------+---+---+
| Left | A | B |
|      +---+---+
|      | C | D |
+------+---+---+
| E    | F | G |
+------+---+---+

Bottom-right corner 2x2 block
=============================

+---+---+---+---+
| A | B | C | D |
+---+---+---+---+
| E | F | Block |
+---+---+       |
| G | H |       |
+---+---+-------+

*****************
 Header patterns
*****************

Colspan in the header row only
==============================

+---------------+
| Group heading |
+------+--------+
| Left | Right  |
+======+========+
| A    | B      |
+------+--------+
| C    | D      |
+------+--------+

Two-level header via colspan
============================

+---------------+---------------+
| Person        | Contact       |
+-------+-------+-------+-------+
| First | Last  | Email | Phone |
+=======+=======+=======+=======+
| Alice | Adams | a@x   | 111   |
+-------+-------+-------+-------+
| Bob   | Brown | b@x   | 222   |
+-------+-------+-------+-------+

Header with rowspan for a stub column
=====================================

+-------+-------+-------+
| ID    | Name  | Score |
+=======+=======+=======+
| Group | Alice | 90    |
|       +-------+-------+
|       | Bob   | 85    |
+-------+-------+-------+

Full-width banner headers above sub-tables
==========================================

+---------------------------+
| Report Section A          |
+------+------+------+------+
| Col1 | Col2 | Col3 | Col4 |
+======+======+======+======+
| a1   | a2   | a3   | a4   |
+------+------+------+------+
| b1   | b2   | b3   | b4   |
+------+------+------+------+

********************
 Content variations
********************

Multi-paragraph content in a spanned cell
=========================================

+--------------+--------------+
| A            | B            |
+--------------+--------------+
| Long spanning cell content. |
|                             |
| More text in second para.   |
+--------------+--------------+
| C            | D            |
+--------------+--------------+

Bulleted list inside a spanned cell
===================================

+-------+-------------------+
| A     | B and C header    |
+-------+---------+---------+
| Left  | Center  | Right   |
+-------+---------+---------+
| Left2 | Spans two columns |
|       |                   |
|       | - item one        |
|       | - item two        |
|       | - item three      |
+-------+-------------------+
| D     | E | F             |
+-------+-------------------+

Very wide colspan across many columns
=====================================

+---+---+---+---+---+---+
| A | B | C | D | E | F |
+---+---+---+---+---+---+
| Span across all six   |
+---+---+---+---+---+---+
| G | H | I | J | K | L |
+---+---+---+---+---+---+

Tall rowspan across many rows
=============================

+------+---+
| Tall | A |
|      +---+
|      | B |
|      +---+
|      | C |
|      +---+
|      | D |
|      +---+
|      | E |
+------+---+

****************************************
 Mixed grid: several spans in one table
****************************************

+----+-----+---+-----+------+
| A  | B   | C | D   | E    |
+----+-----+---+-----+------+
| F/G span | H | I/J span   |
+----+-----+---+------------+
| K  | L   | M spans        |
+----+-----+                |
| N  | O   |                |
+----+-----+----------------+
| Total across five columns |
+---------------------------+

*****************************
 Markup inside spanned cells
*****************************

.. |trade| unicode:: U+02122 .. trademark

+--------------------+------------------------------+--------------------------+
| Feature            | Kind                         | Notes                    |
+====================+==============================+==========================+
| *emphasis*         | **strong**                   | ``literal``              |
+--------------------+------------------------------+--------------------------+
| :PEP:`8`           | :RFC:`2119`                  | :math:`e^{i\pi}`         |
+--------------------+------------------------------+--------------------------+
| `link text`_       | |trade| symbol               | H\ :sub:`2`\ O           |
+--------------------+------------------------------+--------------------------+
| Roles and refs span three columns across the row.                            |
+------------------------------------------------------------------------------+
| Note directive spanning two columns:                                         |
|                                                                              |
| .. note::                                                                    |
|                                                                              |
|     Note admonition with *inline emphasis* and a ``literal`` snippet, plus a |
|     :PEP:`20` role.                                                          |
+------------------------------------------------------------------------------+
| Code block spans two columns:                                                |
|                                                                              |
| .. code-block:: python                                                       |
|                                                                              |
|     def greet(name: str) -> str:                                             |
|         return f"Hello, {name}!"                                             |
+----------------------------------+-------------------------------------------+
| Bulleted list                    | Enumerated list                           |
|                                  |                                           |
| - alpha with *emphasis*          | 1. first ``item``                         |
| - beta with ``code``             | 2. second `title ref`                     |
| - gamma with :PEP:`20`           | 3. third with |trade|                     |
+----------------------------------+-------------------------------------------+

.. _link text: https://example.com/

***************************************
 Rowspan taller than the rows it spans
***************************************

+---+--------------------+
| A | B                  |
+---+--------------------+
| C | Tall spanning cell |
+---+                    |
| D | - item one         |
|   | - item two         |
|   | - item three       |
|   | - item four        |
+---+--------------------+

******************
 Captioned tables
******************

.. table:: A caption on a spanned grid table

    +-----+-----+
    | A   | B   |
    +-----+-----+
    | C spans   |
    +-----------+

.. table:: A caption on a plain table

    ===== =====
    Col 1 Col 2
    ===== =====
    Data1 Data2
    ===== =====
