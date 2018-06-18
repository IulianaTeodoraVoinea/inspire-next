"""
LIST ALL TABLES AND INDEXES, COMPARE RESULTS.

This snippet can be used to build a dictionary of tables and their indexes and
constraints. It can also be used to compare the results across different dbs.

On 2018.04.24 it was run to compare dev db vs pro db, the results was:
https://gist.github.com/turtle321/3a602e66e2588912789687726b97971d
"""
from pprint import pformat

from invenio_db import db
from sqlalchemy.sql import text

SELECT_ALL_TABLES = """
SELECT * FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
"""

SELECT_INDEXES = """
SELECT * FROM pg_indexes
WHERE tablename = :tablename
order by indexname;
"""

SELECT_CONSTRAINTS = """
SELECT
    tc.constraint_name, tc.table_name, kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_type
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
WHERE
    ccu.table_name = :tablename
ORDER BY constraint_name;
"""


def list_tables_and_indexes():
    """
    List all tables and indexes (including public keys).

    Returns:
        Dict[str, Set[str]]
    """
    # Get all tables.
    tables = db.engine.execute(SELECT_ALL_TABLES).fetchall()

    result = {}
    for table in tables:
        table_name = str(table[1])

        # Get all indexes.
        qry = text(SELECT_INDEXES)
        indexes = db.engine.execute(qry, tablename=table_name).fetchall()
        result[table_name] = set()
        for index in indexes:
            index_name = str(index[2])
            result[table_name].add(index_name)

        # Get all constraints.
        qry = text(SELECT_CONSTRAINTS)
        constraints = db.engine.execute(qry, tablename=table_name).fetchall()
        for constraint in constraints:
            constraint_name = str(constraint[0])
            result[table_name].add(constraint_name)

    return result


def compare_list_tables_and_indexes(data1, data2):
    """
    Compare 2 dictionaries generated by `list_tables_and_indexes`.
    """
    # Print missing tables.
    table_names1 = set(data1.keys())
    table_names2 = set(data2.keys())

    print 'Tables missing in data1:\n{}\n'.format(pformat(table_names2-table_names1))
    print 'Tables missing in data2:\n{}\n'.format(pformat(table_names1-table_names2))

    # Print missing indexes for each table.
    common_table_names = table_names1.intersection(table_names2)

    missing_indexes_and_constraints1 = {}
    missing_indexes_and_constraints2 = {}
    for table_name in common_table_names:
        missing_indexes_and_constraints1[table_name] = []
        missing_indexes_and_constraints2[table_name] = []

        indexes_and_constraints1 = data1[table_name]
        indexes_and_constraints2 = data2[table_name]

        missing_indexes_and_constraints1[table_name] = indexes_and_constraints2 - indexes_and_constraints1
        missing_indexes_and_constraints2[table_name] = indexes_and_constraints1 - indexes_and_constraints2

    print 'Indexes and constraints missing in data1:\n{}\n'.format(pformat(missing_indexes_and_constraints1))
    print 'Indexes and constraints missing in data2:\n{}\n'.format(pformat(missing_indexes_and_constraints2))