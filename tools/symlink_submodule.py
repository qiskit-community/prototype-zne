#!/usr/bin/env python3

##    _____  _____
##   |  __ \|  __ \    AUTHOR: Pedro Rivero
##   | |__) | |__) |   ---------------------------------
##   |  ___/|  _  /    DATE: Feb 21, 2023
##   | |    | | \ \    ---------------------------------
##   |_|    |_|  \_\   https://github.com/pedrorrivero
##

## Copyright 2023 Pedro Rivero
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
## http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

"""Create symlinks to submodule files in base repo, adding all missing directories."""

from pathlib import Path


EXCLUDE = {"README.md", ".git", ".gitignore"}


def symlink_files(original: Path, host_dir: Path, relative: Path = None) -> None:
    """Recursively create symlinks(s) to file(s) in original path into host directory.
    
    Args:
        original: path to original file or directory.
        host_dir: directory to host the symlinks.
        relative: relative path to build the symlinks from.
    """
    # Input standardization
    original = original.resolve()
    host_dir = host_dir.resolve()
    if not host_dir.is_dir():
        host_dir = host_dir.parent
    if relative is None:
        relative = Path()
    else:
        relative = relative.resolve()
    
    # Logic
    host = host_dir.joinpath(original.name)
    if original.is_file():
        original = original.relative_to(relative)
        host.symlink_to(original)
    elif original.is_dir():
        host.mkdir(parents=True, exist_ok=True)
        for path in original.iterdir():
            symlink_files(path, host, relative)


if __name__ == "__main__":
    file = Path(__file__).resolve()
    tools = file.parent
    submodule = tools.parent
    repo = submodule.parent
    for file in submodule.iterdir():
        if file.name not in EXCLUDE:
            symlink_files(file, repo, repo)
