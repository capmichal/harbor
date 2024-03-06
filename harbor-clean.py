import argparse
import getpass
import json
import re
from datetime import datetime, timedelta

import requests

HARBOR_API_ARTIFACT_PULL_TIME = "pull_time"
HARBOR_API_ARTIFACT_PUSH_TIME = "push_time"
HARBOR_API_ARTIFACT_TAGS = "tags"
HARBOR_API_ARTIFACT_DIGEST = "digest"

HARBOR_API_REPOSITORY_NAME = "name"
HARBOR_API_REPOSITORY_ARTIFACT_COUNT = "artifact_count"

HARBOR_API_TAG_NAME = "name"

DEFAULT_DAYS_NUMBER = 90
DEFAULT_MINIMUM_KEPT_NUMBER = 10
DEFAULT_HARBOR_URL = "HARBOR URL"

VERSION_PATTERN = r"\d+\.\d+\.\d+-\d+\.\w+"
STABLE_PATTERN = "stable"
LATEST_PATTERN = "latest"
RELEASE_CANDIDATE_PATTERN = "-rc"


class TextColor:
    RED = "\033[31m"
    GREEN = "\033[32m"
    BLUE = "\033[34m"
    WHITE = "\033[37m"
    RESET = "\033[0m"


def print_color(text, color):
    print(color + text + TextColor.RESET)


def is_version_pattern(string):
    pattern = re.compile(VERSION_PATTERN)
    return bool(pattern.match(string))


def custom_sort_key(all_artifacts):
    def key(artifact):
        pull_date_str = artifact.get(HARBOR_API_ARTIFACT_PULL_TIME)
        pull_date_str_time = datetime.strptime(pull_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()
        push_date_str = artifact.get(HARBOR_API_ARTIFACT_PUSH_TIME)

        if not hasattr(custom_sort_key, "same_pull_time_checked"):
            # Check if all pull_time values (considering only date not time) are the same
            same_pull_time = all(
                datetime.strptime(art.get(HARBOR_API_ARTIFACT_PULL_TIME), "%Y-%m-%dT%H:%M:%S.%fZ").date() == pull_date_str_time
                for art in all_artifacts
            )
            custom_sort_key.same_pull_time_checked = True
            custom_sort_key.use_push_time = same_pull_time

        date_to_use = push_date_str if (custom_sort_key.use_push_time and push_date_str) or (not pull_date_str) else pull_date_str

        return (date_to_use,)

    return key


def get_formatted_repo_name(repo):
    return "%252F".join(repo[HARBOR_API_REPOSITORY_NAME].split("/")[1:])


def get_true_repo_size(harbor_base_url, project_name, formatted_repo_name, username, password, repo):
    artifacts_endpoint = f"{harbor_base_url}/projects/{project_name}/repositories/{formatted_repo_name}/artifacts"
    true_repo_size = repo[HARBOR_API_REPOSITORY_ARTIFACT_COUNT]
    artifact_page = 1
    artifact_page_size = 15
    all_artifacts = []

    while True:
        artifact_params = {"page": artifact_page, "page_size": artifact_page_size}
        artifacts = requests.get(artifacts_endpoint, auth=(username, password), params=artifact_params).json()

        for art in artifacts:
            if art[HARBOR_API_ARTIFACT_TAGS] and (
                any(
                    RELEASE_CANDIDATE_PATTERN in tag[HARBOR_API_TAG_NAME]
                    or STABLE_PATTERN in tag[HARBOR_API_TAG_NAME]
                    or LATEST_PATTERN in tag[HARBOR_API_TAG_NAME]
                    for tag in art[HARBOR_API_ARTIFACT_TAGS]
                )
                or any(is_version_pattern(tag[HARBOR_API_TAG_NAME]) for tag in art[HARBOR_API_ARTIFACT_TAGS])
            ):
                true_repo_size -= 1
            else:
                all_artifacts.extend([art])

        if len(artifacts) < artifact_page_size:
            break
        else:
            artifact_page += 1

    return true_repo_size, all_artifacts


def process_artifacts(repository, current_time, repo_size, all_artifacts, how_old, deletion_run, artifacts_endpoint, username, password):
    sorted_artifacts_desc = sorted(all_artifacts, key=custom_sort_key(all_artifacts), reverse=True)

    for art in sorted_artifacts_desc[repo_size:]:
        last_pull_date = datetime.strptime(art[HARBOR_API_ARTIFACT_PULL_TIME], "%Y-%m-%dT%H:%M:%S.%fZ")
        tag_list = [tag[HARBOR_API_TAG_NAME] for tag in art[HARBOR_API_ARTIFACT_TAGS]] if art[HARBOR_API_ARTIFACT_TAGS] else []

        if last_pull_date.year != 1:
            time_difference = current_time - last_pull_date
        else:
            last_push_date = datetime.strptime(art[HARBOR_API_ARTIFACT_PUSH_TIME], "%Y-%m-%dT%H:%M:%S.%fZ")
            time_difference = current_time - last_push_date

        if time_difference > timedelta(days=how_old):
            if not deletion_run:
                print_color(f"tags: {tag_list}, {art[HARBOR_API_ARTIFACT_DIGEST]} TO DELETE", TextColor.RED)
            elif deletion_run:
                delete = requests.delete(f"{artifacts_endpoint}/{art[HARBOR_API_ARTIFACT_DIGEST]}", auth=(username, password))
                if delete.status_code == 200:
                    print_color(f"tags: {tag_list}, {art[HARBOR_API_ARTIFACT_DIGEST]} DELETED", TextColor.RED)
                elif delete.status_code == 403:
                    print_color(f"{tag_list}, {art[HARBOR_API_ARTIFACT_DIGEST]}, permissions problem, failed to delete", TextColor.RED)
                else:
                    print_color(
                        f"Failed to delete {tag_list}, {art[HARBOR_API_ARTIFACT_DIGEST]} Status code: {delete.status_code}, Response: {delete.text}",
                        TextColor.RED,
                    )
        else:
            print_color(f"tags: {tag_list}, {art[HARBOR_API_ARTIFACT_DIGEST]} TO KEEP", TextColor.GREEN)


def spec_repo(project_name, how_old, repo_size, url, deletion_run, username, password):
    harbor_base_url = url
    current_time = datetime.now()
    spec_repo_endpoint = f"{harbor_base_url}/projects/{project_name}/repositories"
    page = 1
    page_size = 15

    try:
        while True:
            params = {"page": page, "page_size": page_size}
            response = requests.get(spec_repo_endpoint, auth=(username, password), params=params)
            response.raise_for_status()

            try:
                repositories = response.json()
            except json.JSONDecodeError:
                print_color(f"Error decoding JSON response from the server. Check if the URL is correct and the server is accessible.", TextColor.RED)
                break

            for repository in repositories:
                formatted_repo_name = get_formatted_repo_name(repository)
                true_repo_size, all_artifacts = get_true_repo_size(harbor_base_url, project_name, formatted_repo_name, username, password, repository)

                if true_repo_size > repo_size:
                    print_color(f"\nWorking on this repo: {repository[HARBOR_API_REPOSITORY_NAME]}", TextColor.WHITE)
                    process_artifacts(
                        repository,
                        current_time,
                        repo_size,
                        all_artifacts,
                        how_old,
                        deletion_run,
                        f"{harbor_base_url}/projects/{project_name}/repositories/{formatted_repo_name}/artifacts",
                        username,
                        password,
                    )

            if len(repositories) < page_size:
                print_color("\nDone.", TextColor.BLUE)
                break
            else:
                page += 1

    except requests.ConnectTimeout:
        print_color(f"Connection to {url} timed out. Please check the URL and try again.", TextColor.RED)
    except requests.RequestException as e:
        print_color(f"An error occurred during the request: {e}", TextColor.RED)
    except Exception as e:
        print_color(f"An unexpected error occurred: {e}", TextColor.RED)


parser = argparse.ArgumentParser(description="Delete artifacts from a specified project based on criteria.")

# positional args
parser.add_argument("--project", dest="projectName", type=str, required=True, help="Name of the project")
parser.add_argument("--days", dest="howOld", type=int, default=DEFAULT_DAYS_NUMBER, help="Age of artifacts in days to consider for deletion")
parser.add_argument(
    "--count", dest="repoSize", type=int, default=DEFAULT_MINIMUM_KEPT_NUMBER, help="Minimum artifact count for deletion"
)  # fix description

# optional args
parser.add_argument("--deletionRun", action="store_true", help="Deletion run mode, script will actually delete artifacts")
parser.add_argument("--user", type=str, help="Username for authentication")
parser.add_argument("--password", type=str, help="Password for authentication")
parser.add_argument("--url", dest="url", type=str, default=DEFAULT_HARBOR_URL, help="URL of your Harbor")

args = parser.parse_args()
user = args.user if args.user else input("Enter username: ")
password = args.password if args.password else getpass.getpass("Enter password: ")

spec_repo(args.projectName, args.howOld, args.repoSize, args.url, deletion_run=args.deletionRun, username=user, password=password)
