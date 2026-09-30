"""Entry points: `python -m booking_miniapp` or the `booking-miniapp` command."""

import sys

from booking_miniapp.cli import main

if __name__ == "__main__":
    sys.exit(main())
