#!/usr/bin/env python3
"""
Enhanced CLI tool to view structured JSON logs from Helm database
Usage: python logs_cli_enhanced.py [service_name] [--tail N] [--level LEVEL] [--correlation-id ID] [--user USER]
"""
import sys
import os
import configparser
import json
from datetime import datetime

# Get database connection from config
INSTANCE_PATH = os.path.join(os.path.dirname(__file__), 'instance')
CONFIG_PATH = os.path.join(INSTANCE_PATH, 'helm.conf')

def get_db_connection():
    """Get PostgreSQL connection string from config"""
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config not found at {CONFIG_PATH}")
        print("Run: python init_db.py")
        return None

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    try:
        return config.get('database', 'connection_string')
    except:
        print("❌ Database config not found in helm.conf")
        return None

def parse_json_log(message):
    """Try to parse message as JSON, return dict or None"""
    try:
        return json.loads(message)
    except (json.JSONDecodeError, TypeError):
        return None

def format_timestamp(ts):
    """Format timestamp for display"""
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return ts
    return str(ts)

def view_logs(service_name=None, tail=50, level=None, correlation_id=None, user=None):
    """View logs from database with enhanced JSON parsing"""
    conn_str = get_db_connection()
    if not conn_str:
        return

    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return

    try:
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor()

        # Build query
        query = "SELECT timestamp, service_name, level, message FROM log_entries WHERE 1=1"
        params = []

        if service_name:
            query += " AND service_name = %s"
            params.append(service_name)

        if level:
            query += " AND level = %s"
            params.append(level.upper())

        # For JSON fields, we need to filter after fetching
        # (or add JSON columns to the database schema)

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(tail * 2 if (correlation_id or user) else tail)  # Fetch more if filtering

        cursor.execute(query, params)
        logs = cursor.fetchall()
        conn.close()

        if not logs:
            print("No logs found")
            return

        # Parse and filter JSON logs
        parsed_logs = []
        for timestamp, svc, lvl, msg in logs:
            json_data = parse_json_log(msg)

            # Apply filters
            if correlation_id and json_data:
                if json_data.get('correlation_id') != correlation_id:
                    continue

            if user and json_data:
                if json_data.get('username') != user and json_data.get('user_id') != user:
                    continue

            parsed_logs.append((timestamp, svc, lvl, msg, json_data))

            if len(parsed_logs) >= tail:
                break

        if not parsed_logs:
            print("No logs found matching filters")
            return

        # Print logs in reverse (oldest first)
        print(f"\n📋 Showing {len(parsed_logs)} most recent logs")
        if correlation_id:
            print(f"🔗 Filtered by correlation_id: {correlation_id}")
        if user:
            print(f"👤 Filtered by user: {user}")
        print()

        for timestamp, svc, lvl, msg, json_data in reversed(parsed_logs):
            # Color code by level
            color = {
                'ERROR': '\033[91m',    # Red
                'WARNING': '\033[93m',  # Yellow
                'INFO': '\033[92m',     # Green
                'DEBUG': '\033[94m'     # Blue
            }.get(lvl, '')
            reset = '\033[0m'
            bold = '\033[1m'
            dim = '\033[2m'

            # Format timestamp
            ts_str = format_timestamp(timestamp)

            if json_data:
                # Structured JSON log
                log_msg = json_data.get('message', msg)
                corr_id = json_data.get('correlation_id', '')
                username = json_data.get('username', '')
                user_id = json_data.get('user_id', '')

                # Build display line
                line = f"{dim}{ts_str}{reset} [{color}{bold}{lvl:7s}{reset}] [{bold}{svc:15s}{reset}]"

                if corr_id:
                    line += f" [{dim}🔗 {corr_id[:8]}{reset}]"

                if username:
                    line += f" [{dim}👤 {username}{reset}]"

                line += f" {log_msg}"

                print(line)

                # Print extra fields if any
                extra_data = json_data.get('extra_data') or {}
                if extra_data:
                    for key, value in extra_data.items():
                        print(f"  {dim}└─ {key}: {value}{reset}")

                # Print exception if present
                if 'exception' in json_data:
                    print(f"  {color}└─ Exception: {json_data['exception'][:200]}{reset}")
            else:
                # Plain text log (legacy format)
                print(f"{dim}{ts_str}{reset} [{color}{lvl:7s}{reset}] [{svc:15s}] {msg}")

    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='View HiveMatrix service logs with JSON support')
    parser.add_argument('service', nargs='?', help='Service name (optional)')
    parser.add_argument('--tail', '-n', type=int, default=50, help='Number of lines to show')
    parser.add_argument('--level', '-l', help='Filter by level (ERROR, WARNING, INFO, DEBUG)')
    parser.add_argument('--correlation-id', '-c', help='Filter by correlation ID (distributed tracing)')
    parser.add_argument('--user', '-u', help='Filter by username or user_id')

    args = parser.parse_args()
    view_logs(args.service, args.tail, args.level, args.correlation_id, args.user)
