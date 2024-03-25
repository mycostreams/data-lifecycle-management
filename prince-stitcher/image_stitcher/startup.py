import os

import imagej


def main():
    ij = imagej.init(os.getenv("FIJI_HOME"))
    ij.getVersion()


if __name__ == "__main__":
    main()
