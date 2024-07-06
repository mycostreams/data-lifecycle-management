import os

import imagej


def main():
    ij = imagej.init(os.getenv("FIJI_HOME", "Fiji.app"))
    ij.getVersion()


if __name__ == "__main__":
    main()
