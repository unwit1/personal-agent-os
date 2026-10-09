from .cli import main

if __name__ == "__main__":  # multiprocessing workers import this module as __mp_main__
    raise SystemExit(main())
