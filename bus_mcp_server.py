from mcp.server.fastmcp import FastMCP
import os
import pymysql
import re
from decimal import Decimal
import datetime

port = int(os.environ.get("PORT", 8000))

mcp = FastMCP(
    "bus-mysql",
    host="0.0.0.0",
    port=port,
    stateless_http=True,
    json_response=True,
)

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "busdb")


def db_query(sql, params=None):
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def normalize(v):
    if isinstance(v, Decimal):
        if v == v.to_integral_value():
            return int(v)
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    return v


def tool_count_rows():
    return db_query("SELECT COUNT(*) FROM bus_data")[0][0]


def tool_latest_rows(limit=5):
    return db_query(
        """SELECT id, service_date, route, hour, stop, bus_on, bus_off, bus_transfer
           FROM bus_data
           ORDER BY id DESC
           LIMIT %s""",
        (limit,),
    )


def tool_route_date_hour(route, stop, service_date, hour):
    return db_query(
        """SELECT stop, bus_on, bus_off, bus_transfer
           FROM bus_data
           WHERE route = %s AND stop = %s AND service_date = %s AND hour = %s
           ORDER BY id DESC
           LIMIT 1""",
        (route, stop, service_date, hour),
    )


@mcp.tool()
def db_ping() -> str:
    """MySQL 연결 상태를 확인한다."""
    rows = db_query("SELECT 1")
    return "OK" if rows and rows[0][0] == 1 else "FAIL"


@mcp.tool()
def count_rows() -> int:
    """bus_data 테이블의 전체 행 수를 반환한다."""
    return int(normalize(tool_count_rows()))


@mcp.tool()
def latest_rows(limit: int = 5) -> list[dict]:
    """bus_data 최근 행들을 조회한다. limit은 1~20 권장."""
    if limit < 1:
        limit = 1
    elif limit > 20:
        limit = 20

    rows = tool_latest_rows(limit)
    cols = ["id", "service_date", "route", "hour", "stop", "bus_on", "bus_off", "bus_transfer"]
    return [dict(zip(cols, (normalize(x) for x in row))) for row in rows]


@mcp.tool()
def route_date_hour(route: str, stop: str, service_date: str, hour: int) -> list[dict]:
    """특정 노선, 정류장, 날짜, 시간의 승하차 데이터를 조회한다."""
    if not route.strip() or not stop.strip():
        return []
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", service_date):
        return []
    if hour < 0 or hour > 23:
        return []

    rows = tool_route_date_hour(route.strip(), stop.strip(), service_date, hour)
    cols = ["stop", "bus_on", "bus_off", "bus_transfer"]
    return [dict(zip(cols, (normalize(x) for x in row))) for row in rows]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
