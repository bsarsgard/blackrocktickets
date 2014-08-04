"""
    Texas - Ticket Sales System
    Copyright (C) 2010 Ben Sarsgard

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from itertools import *
from django.db import connection
from datetime import datetime

def dictfetchone(cursor):
    "Returns a row from the cursor as a dict"
    row = cursor.fetchone()
    if not row:
        return None
    return _dict_helper(cursor.description, row)

def dictfetchmany(cursor, number):
    "Returns a certain number of rows from a cursor as a dict"
    desc = cursor.description
    for row in cursor.fetchmany(number):
        yield _dict_helper(desc, row)

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    for row in cursor.fetchall():
        yield _dict_helper(desc, row)

def _dict_helper(desc, row):
    "Returns a dictionary for the given cursor.description and result row."
    return dict(zip([col[0] for col in desc], row))

def query_to_dicts(query_string, *query_args):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, query_args)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(izip(col_names, row))
        yield row_dict
    return

def explode_history(from_str, to_str, rows):
    from_date = datetime.strptime(from_str, "%m/%d/%Y")
    to_date = datetime.strptime(to_str, "%m/%d/%Y")
    span_delta = to_date - from_date
    if span_delta.days > 14:
        increment = timedelta(days=math.ceil(float(span_delta.days) /\
                14.0))
    else:
        increment = timedelta(days=1)

    history = []
    cur_date = from_date
    while cur_date < to_date:
        next_date = cur_date + increment
        thistory = [cur_date.strftime("%m/%d/%y"), 0]
        for row in rows:
            row_date = datetime.strptime(row[0], "%m/%d/%Y")
            if row_date >= cur_date and row_date < next_date:
                thistory[1] += int(row[1])

        history.append(thistory)
        cur_date = next_date
    return history
