from pypika import Query, Tables, Order, Criterion, Table, Field, functions
import duckdb
from abc import ABC, abstractmethod


class SegmentationQueryGenerator(ABC):

    def __init__(self, conn: duckdb.DuckDBPyConnection):

        self.table_column_list = self.get_table_columns(
            conn)

    def get_table_columns(self, conn) -> tuple[set]:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_columns = ()

        for table in tables:
            table_name = table[0]
            columns = conn.execute(
                f"PRAGMA table_info('{table_name}')").fetchall()
            column_names = set(column[1] for column in columns)
            table_columns += (column_names,)

        return table_columns

    def divide_columns(self, lst: list) -> list[list] | None:
        if lst:
            table = {}
            for i in range(len(self.table_column_list)):
                for col in self.table_column_list[i]:
                    if col not in table:
                        table[col] = i

            segmented_dict = {}
            for col in lst:
                if table[col] in segmented_dict:
                    segmented_dict[table[col]].append(col)
                else:
                    segmented_dict[table[col]] = [col]

            return list(segmented_dict.values())

    @abstractmethod
    def generate(self, payload: dict):
        # implementation starts here
        pass


class DuckmartQueryGenerator(SegmentationQueryGenerator):
    MAX_LIMIT = 200

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        super().__init__(conn)
        self.query = Query

    # override

    def generate(self, payload: dict) -> str:
        users, events = Tables("users", "events")
        segmentBy: dict = payload.get("segmentBy")
        outputFields: dict = payload.get("outputFields")

        q = self.query

        self.divided_segmentation_columns = self.divide_columns(
            segmentBy.keys() if segmentBy else None)
        self.divided_output_columns = self.divide_columns(
            outputFields if outputFields else None)

        all_criteria_list = []

        def get_table_name(property: str) -> str:
            # works if users and events table were created sequentially

            if property in self.table_column_list[0]:
                return "users"
            elif property in self.table_column_list[1]:
                return "events"

        def handleDict(values: list, min: str | int, max: str | int):
            min_max_criteria = []
            if min:
                min_max_criteria.append(Table(get_table_name(property)).field(
                    property).gte(min))
            if max:
                min_max_criteria.append(Table(get_table_name(property)).field(
                    property).lte(max))

            if values:

                if min or max:
                    return (Table(get_table_name(property)).field(
                        property).isin(values) | Criterion.all(min_max_criteria))
                return Table(get_table_name(property)).field(
                    property).isin(values)
            if min or max:
                return Criterion.all(min_max_criteria)

        def handle_timestamp(property: str) -> list:

            if "date" in segmentBy[property] or "time" in segmentBy[property]:
                date_values = segmentBy[property].get(
                    "date", {}).get("values", [])
                time_values = segmentBy[property].get(
                    "time", {}).get("values", [])
                timestamp_values = []
                for i in range(max(len(date_values), len(time_values))):
                    d = date_values[i] if i < len(date_values) else ""
                    t = time_values[i] if i < len(time_values) else ""
                    timestamp_values.append(f"{d} {t}")

                min_timestamp = segmentBy[property].get(
                    "date", {}).get("min", "")
                min_time = segmentBy[property].get(
                    "time", {}).get("min", "")
                if min_time:
                    min_timestamp += " " + min_time
                max_timestamp = segmentBy[property].get(
                    "date", {}).get("max", "")
                max_time = segmentBy[property].get(
                    "time", {}).get("max", "")
                if max_time:
                    max_timestamp += " " + max_time

                return handleDict(timestamp_values,
                                  min_timestamp, max_timestamp)

        def handle_event(property: str):
            criteria_list = []
            values = segmentBy[property].get("values")
            min_event = segmentBy[property].get("min")
            max_event = segmentBy[property].get("max")
            subqueries = []
            if values:

                criteria_list.append(Field(property).isin(values))

            if min_event or max_event:
                subqueries = []
                for i, value in enumerate(values):
                    subqueries.append(Query.from_(events).select(
                        "user_id").where(Field(property).eq(value)).groupby("user_id"))
                if min_event:
                    subqueries = [subquery.having(functions.Count(
                        "*").gte(min_event)) for subquery in subqueries]
                if max_event:
                    subqueries = [subquery.having(functions.Count(
                        "*").lte(min_event)) for subquery in subqueries]

                criteria_list = [users.field(
                    "user_id").isin(query) for query in subqueries]

            return Criterion.all(criteria_list)

        join_needed = (self.divided_output_columns and len(
            self.divided_output_columns) > 1) or (not outputFields)
        subquery_needed = (self.divided_segmentation_columns and len(
            self.divided_segmentation_columns) > 1) or (self.divided_segmentation_columns and len(
                self.divided_segmentation_columns) == 1 and self.divided_segmentation_columns[0][0] == "events")

        # From and Select
        q = q.from_(users).select("*")
        if not (segmentBy):

            if join_needed:
                q = Query.from_(users)
                if not outputFields:
                    q = q.select("*")
                else:
                    for property in outputFields:
                        q = q.select(Table(get_table_name(property)).field(
                            property))
            elif len(self.divided_output_columns) == 1:
                q = Query.from_(get_table_name(
                    self.divided_output_columns[0][0]))
                for property in outputFields:
                    q = q.select(property)

        elif segmentBy and outputFields:
            if join_needed:
                q = Query.from_(users)
                for property in outputFields:
                    q = q.select(Table(get_table_name(property)).field(
                        property))
            else:
                q = Query.from_(users)
                for property in outputFields:
                    q = q.select(property)
        # Join
        if join_needed:
            q = q.join(events).on(users.user_id == events.user_id)

        # Attach condition
        subqueries = []
        if segmentBy:
            for property in segmentBy.keys():

                if (type(segmentBy[property]) == list):
                    values = segmentBy[property]
                    if property == "location":
                        values = [value.lower() for value in values]
                    all_criteria_list.append(Table(get_table_name(property)).field(
                        property).isin(values))

                elif (type(segmentBy[property]) == dict):
                    if "timestamp" in property:
                        if get_table_name(property) == "events":
                            subqueries.append(Query.from_(events).select(
                                "user_id").where(handle_timestamp(property)))
                        else:
                            q = q.where(handle_timestamp(property))
                        continue
                    if "event" == property:
                        q = q.where(handle_event(property))
                        continue

                    q = q.where(handleDict(segmentBy[property].get("values"), segmentBy[property].get(
                        "min"), segmentBy[property].get("max")))

            q = q.where(Criterion.all(all_criteria_list)).where(Criterion.all(users.field(
                "user_id").isin(query) for query in subqueries))

        # add order
        if "orderBy" in payload:
            orderBy = payload["orderBy"]
            order = Order.desc if orderBy.get(
                "order") == "descending" else Order.asc
            q = q.orderby(orderBy["criteria"], order=order)

        # offset pagination
        offset = payload.get("offset")
        if offset:
            q = q.offset()

        # add limit max 100
        limit = payload.get("limit", self.MAX_LIMIT)
        if limit > self.MAX_LIMIT:
            limit = self.MAX_LIMIT
        q = q.limit(limit)

        return str(q)


__all__ = ['DuckmartQueryGenerator']
