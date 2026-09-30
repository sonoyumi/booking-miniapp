"""Точка входа: `python -m booking_miniapp` или команда `booking-miniapp`."""


def greet(name: str) -> str:
    return f"Привет, {name}!"


def main() -> None:
    print(greet("мир"))


if __name__ == "__main__":
    main()
