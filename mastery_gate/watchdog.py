#!/usr/bin/env python3
"""
DAWES Benchmark Watchdog

Background daemon that monitors benchmark processes and automatically
restarts any that die unexpectedly.

Features:
- Checks every 5 minutes if benchmark processes are alive
- Restarts dead benchmark processes
- Logs all restarts to ~/dawes/logs/watchdog.log
- Sends alerts to ~/dawes/logs/alerts.log if the same process
  dies more than 3 times

Usage:
    python watchdog.py                  # Run in foreground
    python watchdog.py --daemon         # Run as background daemon
    python watchdog.py --register CMD   # Register a benchmark command
    python watchdog.py --status         # Show monitored process status
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHECK_INTERVAL_SECONDS = 300  # 5 minutes
MAX_DEATHS_BEFORE_ALERT = 3
DAWES_HOME = os.path.expanduser("~/dawes")
LOG_DIR = os.path.join(DAWES_HOME, "logs")
WATCHDOG_LOG = os.path.join(LOG_DIR, "watchdog.log")
ALERTS_LOG = os.path.join(LOG_DIR, "alerts.log")
REGISTRY_FILE = os.path.join(DAWES_HOME, "watchdog_registry.json")

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------


def _setup_logging():
    """Configure dual logging: watchdog.log for operations, alerts.log for
    critical alerts."""
    os.makedirs(LOG_DIR, exist_ok=True)

    # Main watchdog logger
    wdlogger = logging.getLogger("watchdog")
    wdlogger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler for watchdog.log
    fh = logging.FileHandler(WATCHDOG_LOG)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    wdlogger.addHandler(fh)

    # Console handler for interactive runs
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    wdlogger.addHandler(ch)

    # Separate alert logger → alerts.log
    alert_logger = logging.getLogger("watchdog.alerts")
    alert_logger.setLevel(logging.WARNING)
    ah = logging.FileHandler(ALERTS_LOG)
    ah.setLevel(logging.WARNING)
    ah.setFormatter(fmt)
    alert_logger.addHandler(ah)

    return wdlogger, alert_logger


logger, alert_logger = _setup_logging()

# ---------------------------------------------------------------------------
# Process registry
# ---------------------------------------------------------------------------


def _load_registry():
    """Load the process registry from disk.

    Returns:
        dict mapping process name → entry dict with keys:
            - command (str): The shell command to run
            - pid (int or None): Last known PID
            - death_count (int): Number of times the process has died
            - last_restart (str or None): ISO timestamp of last restart
    """
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_registry(registry):
    """Persist the process registry to disk."""
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


def register_process(name, command):
    """Register a benchmark process for monitoring.

    Args:
        name: A short identifier for the process.
        command: The full shell command to run/restart the process.
    """
    registry = _load_registry()
    registry[name] = {
        "command": command,
        "pid": None,
        "death_count": 0,
        "last_restart": None,
    }
    _save_registry(registry)
    logger.info("Registered process '%s': %s", name, command)


def unregister_process(name):
    """Remove a process from the monitoring registry.

    Args:
        name: The process identifier to remove.
    """
    registry = _load_registry()
    if name in registry:
        del registry[name]
        _save_registry(registry)
        logger.info("Unregistered process '%s'", name)


# ---------------------------------------------------------------------------
# Process health checking
# ---------------------------------------------------------------------------


def _is_process_alive(pid):
    """Check whether a process with the given PID is still running.

    Args:
        pid: Process ID to check.

    Returns:
        True if the process exists, False otherwise.
    """
    if pid is None:
        return False
    try:
        # Signal 0 doesn't kill the process — just checks if it exists
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we don't own it
        return True


def _start_process(command):
    """Start a benchmark process and return its PID.

    Args:
        command: Shell command to execute.

    Returns:
        PID of the started process.
    """
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return proc.pid


# ---------------------------------------------------------------------------
# Main watchdog loop
# ---------------------------------------------------------------------------


def check_and_restart():
    """Check all registered processes and restart any that have died.

    Returns:
        Number of processes restarted during this check.
    """
    registry = _load_registry()
    restarted = 0

    for name, entry in registry.items():
        pid = entry.get("pid")

        if pid is not None and _is_process_alive(pid):
            logger.debug("Process '%s' (PID %d) is alive", name, pid)
            continue

        # Process is dead or was never started
        if pid is not None:
            entry["death_count"] = entry.get("death_count", 0) + 1
            logger.warning(
                "Process '%s' (PID %d) is dead (death #%d)",
                name, pid, entry["death_count"],
            )
        else:
            logger.info("Process '%s' has no PID — starting it", name)

        # Check if we should alert
        if entry["death_count"] > MAX_DEATHS_BEFORE_ALERT:
            alert_logger.warning(
                "ALERT: Process '%s' has died %d times (threshold: %d). "
                "Command: %s",
                name, entry["death_count"], MAX_DEATHS_BEFORE_ALERT,
                entry["command"],
            )

        # Restart the process
        try:
            new_pid = _start_process(entry["command"])
            entry["pid"] = new_pid
            entry["last_restart"] = datetime.now(timezone.utc).isoformat()
            logger.info(
                "Restarted process '%s' → PID %d", name, new_pid,
            )
            restarted += 1
        except Exception as exc:
            logger.error(
                "Failed to restart process '%s': %s", name, exc,
            )
            alert_logger.error(
                "ALERT: Failed to restart process '%s': %s", name, exc,
            )

    _save_registry(registry)
    return restarted


def run_watchdog_loop():
    """Run the watchdog main loop — checks every CHECK_INTERVAL_SECONDS."""
    logger.info(
        "Watchdog started — checking every %d seconds (%d minutes)",
        CHECK_INTERVAL_SECONDS, CHECK_INTERVAL_SECONDS // 60,
    )

    # Handle graceful shutdown
    running = True

    def _signal_handler(signum, frame):
        nonlocal running
        logger.info("Watchdog received signal %d — shutting down", signum)
        running = False

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    while running:
        try:
            check_and_restart()
        except Exception as exc:
            logger.error("Watchdog check failed: %s", exc)
        time.sleep(CHECK_INTERVAL_SECONDS)

    logger.info("Watchdog stopped")


# ---------------------------------------------------------------------------
# Daemonize
# ---------------------------------------------------------------------------


def daemonize():
    """Fork into a background daemon process (Unix double-fork)."""
    # First fork
    pid = os.fork()
    if pid > 0:
        # Parent exits
        print(f"Watchdog daemon started (PID {pid})")
        sys.exit(0)

    os.setsid()

    # Second fork — prevent acquiring a controlling terminal
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Redirect standard file descriptors
    sys.stdin = open(os.devnull, "r")
    sys.stdout = open(WATCHDOG_LOG, "a")
    sys.stderr = open(WATCHDOG_LOG, "a")

    # Write PID file
    pid_file = os.path.join(DAWES_HOME, "watchdog.pid")
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    run_watchdog_loop()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def show_status():
    """Print the current status of all monitored processes."""
    registry = _load_registry()
    if not registry:
        print("No processes registered.")
        return

    print(f"{'Name':<20} {'PID':<8} {'Alive':<7} {'Deaths':<8} {'Last Restart'}")
    print("-" * 75)
    for name, entry in registry.items():
        pid = entry.get("pid")
        alive = _is_process_alive(pid) if pid else False
        print(
            f"{name:<20} {str(pid or '-'):<8} "
            f"{'Yes' if alive else 'No':<7} "
            f"{entry.get('death_count', 0):<8} "
            f"{entry.get('last_restart', '-')}"
        )


def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="DAWES Benchmark Watchdog — monitors and restarts "
                    "benchmark processes"
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Run as a background daemon"
    )
    parser.add_argument(
        "--register", nargs=2, metavar=("NAME", "COMMAND"),
        help="Register a benchmark process: --register <name> '<command>'"
    )
    parser.add_argument(
        "--unregister", metavar="NAME",
        help="Remove a process from monitoring"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show status of all monitored processes"
    )
    parser.add_argument(
        "--check-once", action="store_true",
        help="Run a single health check (no loop)"
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Main entry point for the watchdog."""
    args = parse_args(argv)

    if args.register:
        name, command = args.register
        register_process(name, command)
        return

    if args.unregister:
        unregister_process(args.unregister)
        return

    if args.status:
        show_status()
        return

    if args.check_once:
        restarted = check_and_restart()
        print(f"Check complete — {restarted} process(es) restarted")
        return

    if args.daemon:
        daemonize()
    else:
        run_watchdog_loop()


if __name__ == "__main__":
    main()
