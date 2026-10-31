Step 6 - Event Lifecycle:
  a) Call icu_create_event with athlete_id="{target}", start_date tomorrow,
     name="Coach Test Event", category="NOTE".
  b) Call icu_update_event with athlete_id="{target}", changing the name.
  c) Call icu_duplicate_events with athlete_id="{target}" to create a copy 1 week later.
  d) Call icu_delete_event on both events with athlete_id="{target}".

Step 7 - Fitness / fatigue / form (the surface fixed in #99):
  a) Call icu_get_fitness_summary with NO athlete_id and note the CTL.
  b) Call icu_get_fitness_summary with athlete_id="{target}".
     The CTL must differ from (a) unless the two athletes genuinely train alike,
     and the response's athlete_id field must echo "{target}".
     Getting (a)'s numbers back is the exact bug this verifies against.
  c) Call icu_get_athlete_profile with athlete_id="{target}" and confirm the
     name is the coached athlete, not the default one.
  d) Call icu_get_fitness_chart with athlete_id="{target}", days_back=14,
     days_ahead=0.

Step 8 - Wellness and other athlete-scoped reads:
  Call icu_get_wellness_data, icu_get_sport_settings, icu_get_gear_list and
  icu_get_power_curves, each with athlete_id="{target}".

Step 9 - Permission enforcement:
  Call icu_get_fitness_summary with athlete_id="i999999" (an inaccessible id).
  It MUST return HTTP 403. Returning the default athlete's data instead means
  athlete_id is being silently dropped.

Present a summary table:
| Step | Tool | athlete_id Used | Status | Notes |
Flag 401/403 on reads as a missing follow/coach relationship. Flag 403 on writes
(Step 6) as read-only access, which is expected for a follower."""


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for transport selection.

    Defaults to stdio so existing Claude Desktop / Cursor / Claude Code
    configurations keep working without changes. Pass --transport http (or sse)
    to expose the server over HTTP for remote deployment.
    """
    parser = argparse.ArgumentParser(
        prog="intervals-icu-mcp",
        description="Intervals.icu MCP server. Defaults to stdio transport.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "http", "sse", "streamable-http"),
        default="stdio",
        help="Transport protocol. Use 'http' for remote deployment. Default: stdio.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind when using an HTTP transport. Default: 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind when using an HTTP transport. Default: 8000.",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="URL path to mount the server under (HTTP transports only).",
    )
    args = parser.parse_args(argv)
    if args.transport != "stdio" and args.path is not None:
        if args.path.removesuffix("/") == "/health":
            parser.error("--path cannot be /health because it conflicts with the health route")
    return args


async def _count_registered_tools() -> int:
    return len(await mcp.list_tools())


def _emit_startup_log() -> None:
    import asyncio

    try:
        count = asyncio.run(_count_registered_tools())
    except Exception:
        count = -1
    print(
        f"intervals-icu MCP starting: delete_mode={_DELETE_MODE}, registered_tools={count}",
        file=sys.stderr,
    )


def main() -> None:
    """Main entry point for the Intervals.icu MCP server."""
    args = _parse_args()
    _emit_startup_log()

    if args.transport == "stdio":
        mcp.run()
        return

    kwargs: dict[str, Any] = {"host": args.host, "port": args.port}
    if args.path is not None:
        kwargs["path"] = args.path
    mcp.run(transport=args.transport, **kwargs)


if __name__ == "__main__":
    main()
