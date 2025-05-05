"""Misc stuff used when running experiments with SemanticSteve."""

import csv
import os
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, confloat


class TaskRunResult(BaseModel):
    task: str
    screenshot_fpath: str | None
    score: Annotated[float, confloat(ge=0, le=1)]
    n_skills_invoked: int
    time_elapsed_seconds: float


def append_task_result_to_csv(csv_fpath: str, result: TaskRunResult) -> None:
    should_write_header = False if os.path.isfile(csv_fpath) else True
    # Open in append mode ('a') to add to existing file
    with open(csv_fpath, "a", newline="") as f:
        writer = csv.writer(f)
        if should_write_header:
            headers = list(TaskRunResult.__annotations__.keys())
            writer.writerow(headers)
        writer.writerow(
            [
                result.task,
                result.screenshot_fpath,
                result.score,
                result.n_skills_invoked,
                result.time_elapsed_seconds,
            ]
        )


def get_latest_png_in_dir(directory: str, since_datetime: datetime) -> str | None:
    """
    Returns the name of the most recently created .png file in the specified directory
    since the given datetime. Returns None if no .png files found after that datetime.

    Args:
        directory (str): Path to the directory to search in
        since_datetime (datetime): Datetime to compare file creation times against

    Returns:
        str or None: Filename of the most recent .png file, or None if no matching files
    """
    latest_file = None
    latest_time = since_datetime

    # Check if directory exists
    if not os.path.isdir(directory):
        raise ValueError(f"Directory not found: {directory}")

    # Iterate through files in the directory
    for filename in os.listdir(directory):
        # Check if file is a .png
        if filename.lower().endswith(".png"):
            file_path = os.path.join(directory, filename)

            # Get file creation time
            # Using os.path.getctime() which returns creation time on Windows,
            # and might return last metadata change time on Unix-based systems
            creation_time = datetime.fromtimestamp(os.path.getctime(file_path))

            # If file was created after the since_datetime and is newer than our current latest
            if creation_time > since_datetime and creation_time > latest_time:
                latest_file = filename
                latest_time = creation_time

    return latest_file
