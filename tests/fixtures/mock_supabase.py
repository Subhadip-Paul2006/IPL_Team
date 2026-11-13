"""In-memory mock Supabase client for offline testing."""

from typing import Any


class MockPostgrestResponse:
    """Emulates Postgrest APIResponse."""

    def __init__(self, data: list[dict[str, Any]], count: int | None = None) -> None:
        self.data = data
        self.count = count if count is not None else len(data)


class MockQueryBuilder:
    """Fluent query builder emulating supabase-py / postgrest-py."""

    def __init__(self, table_name: str, store: dict[str, list[dict[str, Any]]]) -> None:
        self.table_name = table_name
        self.store = store
        self._filters: list[tuple[str, str, Any]] = []
        self._order_col: str | None = None
        self._order_desc: bool = False
        self._limit_count: int | None = None
        self._pending_insert: list[dict[str, Any]] | None = None
        self._pending_update: dict[str, Any] | None = None
        self._pending_delete: bool = False

    def select(self, *columns: str) -> "MockQueryBuilder":
        return self

    def insert(self, values: dict[str, Any] | list[dict[str, Any]]) -> "MockQueryBuilder":
        if isinstance(values, dict):
            self._pending_insert = [values]
        else:
            self._pending_insert = list(values)
        return self

    def update(self, values: dict[str, Any]) -> "MockQueryBuilder":
        self._pending_update = values
        return self

    def delete(self) -> "MockQueryBuilder":
        self._pending_delete = True
        return self

    def eq(self, column: str, value: Any) -> "MockQueryBuilder":
        self._filters.append((column, "eq", value))
        return self

    def neq(self, column: str, value: Any) -> "MockQueryBuilder":
        self._filters.append((column, "neq", value))
        return self

    def in_(self, column: str, values: list[Any]) -> "MockQueryBuilder":
        self._filters.append((column, "in", values))
        return self

    def order(self, column: str, desc: bool = False) -> "MockQueryBuilder":
        self._order_col = column
        self._order_desc = desc
        return self

    def limit(self, count: int) -> "MockQueryBuilder":
        self._limit_count = count
        return self

    def execute(self) -> MockPostgrestResponse:
        records = self.store.setdefault(self.table_name, [])

        if self._pending_insert is not None:
            records.extend(self._pending_insert)
            result = list(self._pending_insert)
            self._pending_insert = None
            return MockPostgrestResponse(result)

        matched = list(records)
        for col, op, val in self._filters:
            if op == "eq":
                matched = [r for r in matched if str(r.get(col)) == str(val)]
            elif op == "neq":
                matched = [r for r in matched if str(r.get(col)) != str(val)]
            elif op == "in":
                str_vals = {str(v) for v in val}
                matched = [r for r in matched if str(r.get(col)) in str_vals]

        if self._pending_update is not None:
            for r in matched:
                r.update(self._pending_update)
            result = [dict(r) for r in matched]
            self._pending_update = None
            return MockPostgrestResponse(result)

        if self._pending_delete:
            self.store[self.table_name] = [r for r in records if r not in matched]
            result = list(matched)
            self._pending_delete = False
            return MockPostgrestResponse(result)

        if self._order_col is not None:
            order_col: str = self._order_col
            matched.sort(
                key=lambda r: (r.get(order_col) is None, r.get(order_col)),
                reverse=self._order_desc,
            )

        if self._limit_count is not None:
            matched = matched[: self._limit_count]

        return MockPostgrestResponse(matched)


class MockSupabaseClient:
    """Mock Supabase client providing isolated in-memory table storage."""

    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {}

    def table(self, table_name: str) -> MockQueryBuilder:
        return MockQueryBuilder(table_name, self.tables)

    def from_(self, table_name: str) -> MockQueryBuilder:
        return self.table(table_name)
